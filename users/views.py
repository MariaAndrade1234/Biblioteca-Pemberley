from rest_framework import viewsets, permissions
from users.models import CustomUser
from users.serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """
        Garante que apenas usuários autenticados possam ver/editar, 
        mas permite que qualquer um crie (POST).
        """
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


