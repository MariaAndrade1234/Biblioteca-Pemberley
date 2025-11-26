from rest_framework import viewsets, permissions
from users.models import User as CustomUser
from users.serializers import UserSerializer
from rest_framework import filters as drf_filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend


class UserViewSet(viewsets.ModelViewSet):
    user_model = CustomUser
    user_service = None  # may be injected; by default we use the service module

    queryset = CustomUser.objects.all().order_by('username')
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['username', 'email', 'full_name']
    ordering_fields = ['username', 'created_at']
    pagination_class = PageNumberPagination

    def get_permissions(self):
        """Ensure only authenticated users can view/edit, but allow anyone to create (POST)."""
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        """Override to allow injection of a creation service if provided."""
        service = self.user_service or __import__('users.services', fromlist=['create_user']).create_user
        instance = service(serializer.validated_data)
        serializer.instance = instance
        return instance

    def get_queryset(self):
        qs = super().get_queryset().order_by('username')
        status = self.request.query_params.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        return qs


