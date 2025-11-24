from rest_framework import serializers
from users.models import User as CustomUser
from users.services import create_user as create_user_service


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser

        fields = (
            'id', 
            'username', 
            'email', 
            'full_name', 
            'birthdate', 
            'created_at', 
            'updated_at'
        )

    read_only_fields = (
        'id', 
        'created_at',
        'updated_at'
    )

    extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        """
        Delega a criação ao `users.services.create_user` para separar
        responsabilidades. O serviço delega ao manager do modelo, então
        as regras de negócio permanecem inalteradas.
        """
        return create_user_service(validated_data)
        