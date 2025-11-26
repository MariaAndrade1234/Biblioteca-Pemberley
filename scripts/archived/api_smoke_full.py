"""Full smoke test script that exercises API endpoints using Django test Client.

Covers: token obtain/refresh, users list/retrieve, authors list/create/retrieve,
books list/create/retrieve, reservations create/list/delete, borrow/renew/return,
OpenAPI schema/docs endpoints.

Run with the project's venv python:
.venv\Scripts\python.exe scripts\api_smoke_full.py
"""
import os
import sys
import json
import pprint
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.conf import settings
from django.test import Client
from django.contrib.auth import get_user_model

for host in ('testserver', '127.0.0.1', 'localhost'):
    if host not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append(host)

User = get_user_model()
client = Client()
pp = pprint.PrettyPrinter(indent=2)


def ensure_user(username='apiuser', password='Password123', email='apiuser@example.com'):
    user, created = User.objects.get_or_create(username=username, defaults={'email': email})
    user.set_password(password)
    user.email = email
    user.save()
    return user


def obtain_token(username='apiuser', password='Password123'):
    resp = client.post('/api/v1/token/', {'username': username, 'password': password})
    try:
        data = json.loads(resp.content)
    except Exception:
        data = {'error': resp.content.decode('utf-8')}
    return resp.status_code, data


def refresh_token(refresh_token):
    resp = client.post('/api/v1/token/refresh/', {'refresh': refresh_token})
    try:
        data = json.loads(resp.content)
    except Exception:
        data = {'error': resp.content.decode('utf-8')}
    return resp.status_code, data


def run():
    results = {}

    user = ensure_user()
    results['test_user_id'] = str(user.pk)

    status, token_data = obtain_token()
    results['token_post_status'] = status
    results['token_data'] = token_data

    access = token_data.get('access') if isinstance(token_data, dict) else None
    refresh = token_data.get('refresh') if isinstance(token_data, dict) else None

    headers = {}
    if access:
        headers['HTTP_AUTHORIZATION'] = f'Bearer {access}'

    if refresh:
        r_status, r_data = refresh_token(refresh)
        results['token_refresh_status'] = r_status
        results['token_refresh_data'] = r_data

    resp = client.get('/api/v1/users/', **headers)
    try:
        results['users_list'] = json.loads(resp.content)
    except Exception:
        results['users_list'] = {'text': resp.content.decode('utf-8')}
    results['users_list_status'] = resp.status_code

    resp = client.get(f'/api/v1/users/{user.pk}/', **headers)
    try:
        results['users_retrieve'] = json.loads(resp.content)
    except Exception:
        results['users_retrieve'] = {'text': resp.content.decode('utf-8')}
    results['users_retrieve_status'] = resp.status_code

    author_payload = {'name': 'Full Smoke Author', 'biography': 'Smoke bio', 'birth_date': '1970-01-01', 'nationality': 'BR'}
    resp = client.post('/api/v1/library/authors/', json.dumps(author_payload), content_type='application/json', **headers)
    try:
        results['create_author_response'] = json.loads(resp.content)
    except Exception:
        results['create_author_response'] = {'text': resp.content.decode('utf-8')}
    results['create_author_status'] = resp.status_code

    author_id = None
    if resp.status_code in (200, 201):
        author_id = results['create_author_response'].get('id')

    resp = client.get('/api/v1/library/authors/', **headers)
    try:
        results['authors_list'] = json.loads(resp.content)
    except Exception:
        results['authors_list'] = {'text': resp.content.decode('utf-8')}
    results['authors_list_status'] = resp.status_code

    if author_id:
        resp = client.get(f'/api/v1/library/authors/{author_id}/', **headers)
        try:
            results['authors_retrieve'] = json.loads(resp.content)
        except Exception:
            results['authors_retrieve'] = {'text': resp.content.decode('utf-8')}
        results['authors_retrieve_status'] = resp.status_code

    book_resp_json = None
    if author_id:
        book_payload = {
            'title': 'Full Smoke Book',
            'subtitle': 'Smoke',
            'author_id': author_id,
            'book_description': 'Desc',
            'category': 'Fiction',
            'publisher': 'Pemberley Press',
            'publication_date': '2020-01-01',
            'ISBN': f"ISBN-FULL-{uuid.uuid4().hex[:12]}",
            'page_count': 123,
            'last_edition': '2023-01-01',
            'language': 'EN',
            'cover_url': 'http://example.com/cover.jpg'
        }
        resp = client.post('/api/v1/library/books/', json.dumps(book_payload), content_type='application/json', **headers)
        try:
            book_resp_json = json.loads(resp.content)
        except Exception:
            book_resp_json = {'text': resp.content.decode('utf-8')}
        results['create_book_status'] = resp.status_code
        results['create_book_response'] = book_resp_json

    resp = client.get('/api/v1/library/books/', **headers)
    try:
        results['books_list'] = json.loads(resp.content)
    except Exception:
        results['books_list'] = {'text': resp.content.decode('utf-8')}
    results['books_list_status'] = resp.status_code

    if book_resp_json and isinstance(book_resp_json, dict) and book_resp_json.get('id'):
        book_id = book_resp_json['id']
        resp = client.get(f'/api/v1/library/books/{book_id}/', **headers)
        try:
            results['books_retrieve'] = json.loads(resp.content)
        except Exception:
            results['books_retrieve'] = {'text': resp.content.decode('utf-8')}
        results['books_retrieve_status'] = resp.status_code

    reserve_id = None
    if book_resp_json and isinstance(book_resp_json, dict) and book_resp_json.get('id'):
        resp = client.post('/api/v1/library/reservations/', json.dumps({'book': book_resp_json['id']}), content_type='application/json', **headers)
        try:
            results['create_reservation'] = json.loads(resp.content)
        except Exception:
            results['create_reservation'] = {'text': resp.content.decode('utf-8')}
        results['create_reservation_status'] = resp.status_code
        if resp.status_code in (200, 201):
            reserve_id = results['create_reservation'].get('id')

        resp = client.get('/api/v1/library/reservations/', **headers)
        try:
            results['reservations_list'] = json.loads(resp.content)
        except Exception:
            results['reservations_list'] = {'text': resp.content.decode('utf-8')}
        results['reservations_list_status'] = resp.status_code

    borrow_id = None
    if book_resp_json and isinstance(book_resp_json, dict) and book_resp_json.get('id'):
        resp = client.post('/api/v1/library/borrowings/', json.dumps({'book': book_resp_json['id'], 'days': 7}), content_type='application/json', **headers)
        try:
            results['borrow_response'] = json.loads(resp.content)
        except Exception:
            results['borrow_response'] = {'text': resp.content.decode('utf-8')}
        results['borrow_status'] = resp.status_code
        if resp.status_code in (200, 201):
            borrow_id = results['borrow_response'].get('id')

    resp = client.get('/api/v1/library/borrowings/', **headers)
    try:
        results['borrowings_list'] = json.loads(resp.content)
    except Exception:
        results['borrowings_list'] = {'text': resp.content.decode('utf-8')}
    results['borrowings_list_status'] = resp.status_code

    if borrow_id:
        resp = client.post(f'/api/v1/library/borrowings/{borrow_id}/renew/', json.dumps({'extra_days': 2}), content_type='application/json', **headers)
        try:
            results['renew_response'] = json.loads(resp.content)
        except Exception:
            results['renew_response'] = {'text': resp.content.decode('utf-8')}
        results['renew_status'] = resp.status_code

        resp = client.post(f'/api/v1/library/borrowings/{borrow_id}/return/', **headers)
        try:
            results['return_response'] = json.loads(resp.content)
        except Exception:
            results['return_response'] = {'text': resp.content.decode('utf-8')}
        results['return_status'] = resp.status_code

    resp = client.get('/api/schema/')
    results['openapi_schema_status'] = resp.status_code
    resp = client.get('/api/docs/')
    results['openapi_docs_status'] = resp.status_code

    pp.pprint(results)


if __name__ == '__main__':
    run()
