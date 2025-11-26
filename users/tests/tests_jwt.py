from datetime import timedelta
import time

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from django.utils import timezone
from django.contrib.auth import get_user_model
from library.models import Author, Book

User = get_user_model()


class JWTFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = Author.objects.create(name='JWT Author')
        # Create a book for borrowing
        self.book = Book.objects.create(title='JWT Book', author=self.author, ISBN='ISBN-JWT-1', publication_date=timezone.now().date())
        # Create a normal user
        self.user = User.objects.create_user(username='jwtuser', email='jwtuser@example.com', password='Password123')

    def test_protected_endpoint_requires_auth(self):
        # Attempt to create borrowing without Authorization header
        resp = self.client.post('/api/v1/library/borrowings/', {'book': str(self.book.id), 'days': 7}, format='json')
        self.assertIn(resp.status_code, (401, 403))

    def test_obtain_token_and_use_access(self):
        # Obtain token pair
        resp = self.client.post('/api/v1/token/', {'username': 'jwtuser', 'password': 'Password123'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        access = data.get('access')
        self.assertIsNotNone(access)

        # Use access token in Authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp2 = self.client.post('/api/v1/library/borrowings/', {'book': str(self.book.id), 'days': 7}, format='json')
        self.assertEqual(resp2.status_code, 201)

    def test_refresh_token(self):
        resp = self.client.post('/api/v1/token/', {'username': 'jwtuser', 'password': 'Password123'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        refresh = data.get('refresh')
        self.assertIsNotNone(refresh)

        resp2 = self.client.post('/api/v1/token/refresh/', {'refresh': refresh}, format='json')
        self.assertEqual(resp2.status_code, 200)
        self.assertIn('access', resp2.json())

    def test_invalid_token_rejected(self):
        # Use a malformed/altered token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.token.value')
        resp = self.client.get('/api/v1/library/borrowings/')
        self.assertIn(resp.status_code, (401, 403))

    def test_access_token_expires(self):
        # Force the ACCESS_TOKEN_LIFETIME at runtime to avoid import-time caching issues
        # Construct a short-lived access token directly so we control the 'exp' claim
        from rest_framework_simplejwt.tokens import AccessToken

        token = AccessToken.for_user(self.user)
        # set expiration 1 second from now
        token['exp'] = int(time.time()) + 1
        short_lived = str(token)

        # Immediately usable
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {short_lived}')
        resp2 = self.client.get('/api/v1/library/borrowings/')
        self.assertIn(resp2.status_code, (200, 204, 404))

        # Wait for token expiration
        time.sleep(2)
        resp3 = self.client.get('/api/v1/library/borrowings/')
        self.assertIn(resp3.status_code, (401, 403))
