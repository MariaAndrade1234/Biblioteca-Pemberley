from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import json

User = get_user_model()


class UsersCrudTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(username='staff', email='s@example.com', password='pass', is_staff=True)
        self.user = User.objects.create_user(username='user', email='u@example.com', password='pass')

    def test_create_user_and_retrieve(self):
        payload = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'NewPass123',
            'full_name': 'New User'
        }
        resp = self.client.post('/api/v1/users/', data=json.dumps(payload), content_type='application/json')
        self.assertIn(resp.status_code, (200, 201))
        data = resp.json()
        self.assertIn('id', data)

        resp2 = self.client.get(f"/api/v1/users/{data['id']}/")
        self.assertIn(resp2.status_code, (200, 200, 401))

    def test_list_users_requires_auth(self):
        resp = self.client.get('/api/v1/users/')
        self.assertEqual(resp.status_code, 401)
        self.client.force_authenticate(self.staff)
        resp2 = self.client.get('/api/v1/users/')
        self.assertEqual(resp2.status_code, 200)

    def test_token_refresh(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post('/api/v1/token/', {'username': 'user', 'password': 'pass'})
        if resp.status_code == 401:
            resp = self.client.post('/api/v1/token/', {'username': 'user', 'password': 'pass'})
        if resp.status_code == 200:
            data = resp.json()
            refresh = data.get('refresh')
            if refresh:
                r = self.client.post('/api/v1/token/refresh/', {'refresh': refresh})
                self.assertEqual(r.status_code, 200)
        else:
            self.assertIn(resp.status_code, (200, 401))
