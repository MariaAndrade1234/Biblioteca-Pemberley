from typing import Dict
from users.models import User as CustomUser


def create_user(validated_data: Dict) -> CustomUser:
    return CustomUser.objects.create_user(
        username=validated_data.get('username'),
        password=validated_data.get('password'),
        email=validated_data.get('email'),
        full_name=validated_data.get('full_name'),
        birthdate=validated_data.get('birthdate')
    )
