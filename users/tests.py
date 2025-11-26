import pytest
from django.contrib.auth.hashers import check_password
from users.models import User
from model_bakery import baker

pytestmark = pytest.mark.django_db

def test_user_creation_default_status():
    """Verifica se um usuário é criado como ativo (is_active=True)."""
    user = baker.make(User, username='testuser', email='a@a.com')
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False


def test_required_fields_presence():
    """Verifica se os campos obrigatórios (username, email) estão presentes e têm o tipo correto."""
    user = baker.make(User, username='testuser', email='b@b.com', full_name='John Doe')

    assert user.username == 'testuser'
    assert user.email == 'b@b.com'
    assert user.full_name == 'John Doe'

    assert user.updated_at is not None

def test_password_hashing():
    """Verifica se a senha é hasheada corretamente na criação."""
    raw_password = 'Password123'
    user = User.objects.create_user(
        username='hasheduser', 
        email='c@c.com', 
        password=raw_password
    )
    assert user.password != raw_password
    assert check_password(raw_password, user.password) is True

def test_unique_email_constraint():
    """Verifica se a criação de um segundo usuário com o mesmo e-mail falha."""
    baker.make(User, email='duplicate@test.com')
    
    with pytest.raises(Exception):
        User.objects.create_user(
            username='user2', 
            email='duplicate@test.com', 
            password='test'
        )

def test_full_user_fields():
    """Verifica a presença e o tipo do campo full_name e birth_date."""
    user = baker.make(
        User,
        full_name='Maria Andrade',
        birthdate='1990-01-01'
    )
    
    assert user.full_name == 'Maria Andrade'
    assert str(user.birthdate) == '1990-01-01' # Verifica o formato da data
    assert user.email is not None # Email é obrigatório no seu modelo

def test_user_manager_methods():
    """Verifica se os métodos de manager (create_superuser) funcionam."""
    superuser = User.objects.create_superuser(
        username='admin',
        email='admin@admin.com',
        password='adminpassword',
        full_name='Super Admin'
    )
    assert superuser.is_staff is True
    assert superuser.is_superuser is True