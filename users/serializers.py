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
            'updated_at',
            'is_active',
            'password',
        )

        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
        )

        extra_kwargs = {'password': {'write_only': True, 'required': False}}

    def create(self, validated_data):
        return create_user_service(validated_data)

    def update(self, instance, validated_data):
        # handle password changes securely
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
        