from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import ValidationError as DRFValidationError
from users.models import User as CustomUser
from users.serializers import UserSerializer
from rest_framework import filters as drf_filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
import logging


logger = logging.getLogger(__name__)
from core.views import BaseViewSet


class UserViewSet(BaseViewSet):
    user_model = CustomUser
    user_service = None  

    queryset = CustomUser.objects.all().order_by('username')
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['username', 'email', 'full_name']
    ordering_fields = ['username', 'created_at']
    pagination_class = PageNumberPagination

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        try:
            logger.debug('Creating user with data: %s', {k: v for k, v in serializer.validated_data.items() if k != 'password'})
            service = self.user_service or __import__('users.services', fromlist=['create_user']).create_user
            instance = service(serializer.validated_data)
        except Exception as exc:
            logger.exception('Error creating user')
            raise DRFValidationError(str(exc))

        serializer.instance = instance
        logger.info('User created: id=%s username=%s', getattr(instance, 'id', None), getattr(instance, 'username', None))
        return instance

    def get_queryset(self):
        qs = super().get_queryset().order_by('username')
        status = self.request.query_params.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        logger.debug('User list requested by %s filter_status=%s result_count=%s', getattr(self.request.user, 'username', None), status, qs.count())
        return qs


