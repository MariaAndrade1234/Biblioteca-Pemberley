from rest_framework import viewsets, permissions
from users.models import User as CustomUser
from users.serializers import UserSerializer
from rest_framework import filters as drf_filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend


class UserViewSet(viewsets.ModelViewSet):
    # Dependências substituíveis para facilitar testes e extensões futuras
    user_model = CustomUser
    user_service = None  # pode ser injetado; por padrão usamos o service module

    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['username', 'email', 'full_name']
    ordering_fields = ['username', 'created_at']
    pagination_class = PageNumberPagination

    def get_permissions(self):
        """
        Garante que apenas usuários autenticados possam ver/editar, 
        mas permite que qualquer um crie (POST).
        """
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        """Override para permitir injeção do serviço de criação se fornecido."""
        service = self.user_service or __import__('users.services', fromlist=['create_user']).create_user
        return service(serializer.validated_data)

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.query_params.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        return qs


