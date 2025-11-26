import os
import sys
import django
from django.test import Client
from django.conf import settings
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

try:
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ['testserver', 'localhost']
except Exception:
    settings.ALLOWED_HOSTS = ['testserver', 'localhost']

client = Client()

print('GET / ->', client.get('/').status_code)
print('GET /api/v1/ ->', client.get('/api/v1/').status_code)
print('GET /api/v1/users/ ->', client.get('/api/v1/users/').status_code)

payload = json.dumps({
    'username': 'apiuser',
    'email': 'apiuser@example.com',
    'password': 'Testpass123',
    'full_name': 'API User'
})
resp = client.post('/api/v1/users/', data=payload, content_type='application/json')
print('POST /api/v1/users/ ->', resp.status_code)
try:
    print('Response:', resp.json())
except Exception:
    print('Response body (text):', resp.content[:500])
