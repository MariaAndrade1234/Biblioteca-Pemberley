from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework import filters as drf_filters

from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Author, Book, Borrowing, Reservation
from .serializers import AuthorSerializer, BookSerializer, BorrowingSerializer, ReservationSerializer
from .serializers import AuthorSerializer as _AuthorSerializer
from . import services
from rest_framework import status
import logging
from core.views import BaseViewSet

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class AuthorViewSet(BaseViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

logger = logging.getLogger(__name__)

class BookViewSet(BaseViewSet):
    queryset = Book.objects.select_related('author').all().order_by('title')
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = ['category', 'author', 'status']
    search_fields = ['title', 'subtitle', 'ISBN']
    ordering_fields = ['title', 'publication_date', 'author__name']

    def update(self, request, *args, **kwargs):
        if 'status' in request.data and not request.user.is_staff:
            logger.warning('User %s attempted to change book status without permission', request.user)
            return Response({'detail': 'Only staff users can change book status'}, status=status.HTTP_403_FORBIDDEN)
        result = super().update(request, *args, **kwargs)
        logger.info('Book updated by user %s: %s', request.user, kwargs.get('pk'))
        return result

    def partial_update(self, request, *args, **kwargs):
        if 'status' in request.data and not request.user.is_staff:
            logger.warning('User %s attempted to change book status without permission', request.user)
            return Response({'detail': 'Only staff users can change book status'}, status=status.HTTP_403_FORBIDDEN)
        result = super().partial_update(request, *args, **kwargs)
        logger.info('Book partially updated by user %s: %s', request.user, kwargs.get('pk'))
        return result

class BorrowingViewSet(BaseViewSet):
    queryset = Borrowing.objects.select_related('book', 'user').all()
    serializer_class = BorrowingSerializer
    permission_classes = [permissions.IsAuthenticated]
    borrowing_service = services.DefaultBorrowingService

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user
        book = serializer.validated_data.get('book')
        days = int(self.request.data.get('days', 14))
        try:
            logger.debug('User %s is creating a borrowing for book %s for %s days', user, book, days)
            borrowing = self.borrowing_service.borrow(user, book, days=days)
        except PermissionError as exc:
            logger.warning('Permission denied when creating borrowing: %s', exc)
            raise DRFValidationError(str(exc))
        except Exception as exc:
            logger.exception('Unexpected error creating borrowing for user %s book %s', user, book)
            raise DRFValidationError(str(exc))
        serializer.instance = borrowing
        logger.info('Borrowing created: user=%s book=%s id=%s', user, getattr(book, 'pk', None), getattr(borrowing, 'pk', None))

    @action(detail=True, methods=['post'], url_path='return')
    def do_return(self, request, pk=None):
        borrowing = self.get_object()
        try:
            logger.info('User %s requested return for borrowing %s', request.user, borrowing.pk)
            services.return_book(borrowing)
        except PermissionError as exc:
            logger.warning('Permission error returning borrowing %s: %s', borrowing.pk, exc)
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as exc:
            logger.exception('Error returning borrowing %s', borrowing.pk)
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        logger.info('Borrowing %s returned by user %s', borrowing.pk, request.user)
        return Response({'status': 'returned'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='renew')
    def do_renew(self, request, pk=None):
        borrowing = self.get_object()
        extra_days = int(request.data.get('extra_days', 7))
        try:
            logger.info('User %s requested renew for borrowing %s (+%s days)', request.user, borrowing.pk, extra_days)
            services.renew_borrowing(borrowing, extra_days=extra_days)
        except PermissionError as exc:
            logger.warning('Permission error renewing borrowing %s: %s', borrowing.pk, exc)
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as exc:
            logger.exception('Error renewing borrowing %s', borrowing.pk)
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        logger.info('Borrowing %s renewed by user %s; new_return_date=%s', borrowing.pk, request.user, borrowing.return_date)
        return Response({'status': 'renewed', 'new_return_date': borrowing.return_date}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='overdue')
    def overdue(self, request):
        try:
            now = timezone.now()
            qs = self.queryset.filter(return_date__lt=now, returned=False)
            user_id = request.query_params.get('user_id')
            if user_id:
                qs = qs.filter(user_id=user_id)

            page = self.paginate_queryset(qs)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                logger.info('Overdue list paginated request by %s, items=%s', request.user, len(page))
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(qs, many=True)
            logger.info('Overdue list requested by %s, total_items=%s', request.user, qs.count())
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception('Error fetching overdue borrowings')
            return Response({'detail': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='borrowers')
    def borrowers(self, request):
        try:
            users_qs = User.objects.filter(borrowings__returned=False).distinct()
            status_q = request.query_params.get('status')
            if status_q == 'active':
                users_qs = users_qs.filter(is_active=True)
            elif status_q == 'inactive':
                users_qs = users_qs.filter(is_active=False)

            users_qs = users_qs.order_by('username')
            paginator = StandardResultsSetPagination()
            page = paginator.paginate_queryset(users_qs, request)
            data = [{'id': u.id, 'username': u.username, 'email': u.email, 'is_active': u.is_active} for u in page]
            logger.info('Borrowers list requested by %s status=%s items=%s', request.user, status_q, len(data))
            return paginator.get_paginated_response(data)
        except Exception as exc:
            logger.exception('Error fetching borrowers list')
            return Response({'detail': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReservationViewSet(BaseViewSet):
    queryset = Reservation.objects.select_related('book', 'user').all()
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        try:
            serializer.save()
        except Exception as exc:
            logger.exception('Error creating reservation')
            raise DRFValidationError(str(exc))
        else:
            try:
                # try to log saved instance details if available
                instance = getattr(serializer, 'instance', None)
                if instance is not None:
                    logger.info('Reservation created: id=%s user=%s book=%s', getattr(instance, 'pk', None), getattr(instance, 'user', None), getattr(instance, 'book', None))
            except Exception:
                logger.debug('Reservation created but failed to log instance details')


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def borrowed_books_by_user(request, user_id):
    try:
        user = get_object_or_404(User, pk=user_id)
        borrowings = Borrowing.objects.filter(user=user, returned=False).select_related('book')
        books = [b.book for b in borrowings]
        serializer = BookSerializer(books, many=True, context={'request': request})
        logger.info('Borrowed books fetched for user %s: count=%s by %s', user_id, len(books), request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as exc:
        logger.exception('Error fetching borrowed books for user %s', user_id)
        return Response({'detail': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
