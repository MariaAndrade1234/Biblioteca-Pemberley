import pytest
from django.contrib.auth.hashers import check_password
from users.models import User
from model_bakery import baker

pytestmark = pytest.mark.django_db

def test_user_creation_default_status():
    """Ensure a newly created user is active by default (is_active=True)."""
    user = baker.make(User, username='testuser', email='a@a.com')
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False


def test_required_fields_presence():
    """Required fields (username, email) should exist and have correct values."""
    user = baker.make(User, username='testuser', email='b@b.com', full_name='John Doe')

    assert user.username == 'testuser'
    assert user.email == 'b@b.com'
    assert user.full_name == 'John Doe'

    assert user.updated_at is not None


def test_password_hashing():
    """Passwords must be hashed when creating users."""
    raw_password = 'Password123'
    user = User.objects.create_user(
        username='hasheduser',
        email='c@c.com',
        password=raw_password,
    )
    assert user.password != raw_password
    assert check_password(raw_password, user.password) is True


def test_unique_email_constraint():
    """Creating a second user with the same email should fail (unique constraint)."""
    baker.make(User, email='duplicate@test.com')

    with pytest.raises(Exception):
        User.objects.create_user(
            username='user2',
            email='duplicate@test.com',
            password='test',
        )


def test_full_user_fields():
    """Check presence and format of full_name and birthdate fields."""
    user = baker.make(
        User,
        full_name='Maria Andrade',
        birthdate='1990-01-01',
    )

    assert user.full_name == 'Maria Andrade'
    assert str(user.birthdate) == '1990-01-01'  # ensure date format
    assert user.email is not None  # email is required in the model


def test_user_manager_methods():
    """Manager helpers (create_superuser) should set staff/superuser flags."""
    superuser = User.objects.create_superuser(
        username='admin',
        email='admin@admin.com',
        password='adminpassword',
        full_name='Super Admin',
    )
    assert superuser.is_staff is True
    assert superuser.is_superuser is True