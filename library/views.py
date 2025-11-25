from rest_framework import viewsets, permissions
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

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.select_related('author').all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = ['category', 'author', 'status']
    search_fields = ['title', 'subtitle', 'ISBN']
    ordering_fields = ['title', 'publication_date', 'author__name']

    def update(self, request, *args, **kwargs):
        # enforce staff-only status changes at view level for extra safety
        if 'status' in request.data and not request.user.is_staff:
            return Response({'detail': 'Only staff users can change book status'}, status=400)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if 'status' in request.data and not request.user.is_staff:
            return Response({'detail': 'Only staff users can change book status'}, status=400)
        return super().partial_update(request, *args, **kwargs)


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.select_related('book', 'user').all()
    serializer_class = BorrowingSerializer
    permission_classes = [permissions.IsAuthenticated]
    # dependency injection point: default service can be replaced in tests
    borrowing_service = services.DefaultBorrowingService

    def get_queryset(self):
        # regular users see only their borrowings; staff can see all
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        # Use the borrowing service to enforce business rules and return the created borrowing
        user = self.request.user
        book = serializer.validated_data.get('book')
        # allow client to request a 'days' parameter via request data
        days = int(self.request.data.get('days', 14))
        borrowing = self.borrowing_service.borrow(user, book, days=days)
        serializer.instance = borrowing

    @action(detail=True, methods=['post'], url_path='return')
    def do_return(self, request, pk=None):
        borrowing = self.get_object()
        try:
            services.return_book(borrowing)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=400)
        return Response({'status': 'returned'})

    @action(detail=True, methods=['post'], url_path='renew')
    def do_renew(self, request, pk=None):
        borrowing = self.get_object()
        extra_days = int(request.data.get('extra_days', 7))
        try:
            services.renew_borrowing(borrowing, extra_days=extra_days)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=400)
        return Response({'status': 'renewed', 'new_return_date': borrowing.return_date})

    @action(detail=False, methods=['get'], url_path='overdue')
    def overdue(self, request):
        now = timezone.now()
        qs = self.queryset.filter(return_date__lt=now, returned=False)
        # optional filter by user id
        user_id = request.query_params.get('user_id')
        if user_id:
            qs = qs.filter(user_id=user_id)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='borrowers')
    def borrowers(self, request):
        # list users who have at least one active borrowing
        users_qs = User.objects.filter(borrowings__returned=False).distinct()
        status = request.query_params.get('status')
        if status == 'active':
            users_qs = users_qs.filter(is_active=True)
        elif status == 'inactive':
            users_qs = users_qs.filter(is_active=False)

        # simple paginator
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(users_qs, request)
        data = [{'id': u.id, 'username': u.username, 'email': u.email, 'is_active': u.is_active} for u in page]
        return paginator.get_paginated_response(data)


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.select_related('book', 'user').all()
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        serializer.save()


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def borrowed_books_by_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    borrowings = Borrowing.objects.filter(user=user, returned=False).select_related('book')
    books = [b.book for b in borrowings]
    serializer = BookSerializer(books, many=True, context={'request': request})
    return Response(serializer.data)
