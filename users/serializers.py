from rest_framework import serializers
from users.models import CustomUser

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
        Sobrescreve o método de criação para garantir o hashing da senha
        usando o método create_user do modelo customizado.
        """
        User = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            birth_date=validated_data.get('birth_date')  
        )
        return User
        