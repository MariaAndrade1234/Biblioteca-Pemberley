#!/usr/bin/env python
"""Simple smoke test script that exercises key API endpoints using
the Django test Client (no external HTTP required).

Run with the project's venv python:
C:/Users/beatr/Biblioteca-Pemberley/venv/Scripts/python.exe scripts/api_smoke_test.py
"""
import os
import json
import pprint
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.conf import settings
from django.test import Client
from django.contrib.auth import get_user_model

# make testserver/hosts allowed for the test client
for host in ('testserver', '127.0.0.1', 'localhost'):
    if host not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append(host)

User = get_user_model()
client = Client()

def ensure_user(username='apiuser', password='Password123', email='apiuser@example.com'):
    user, created = User.objects.get_or_create(username=username, defaults={'email': email})
    if created:
        user.set_password(password)
        user.save()
    return user


def obtain_token(username='apiuser', password='Password123'):
    resp = client.post('/api/v1/token/', {'username': username, 'password': password})
    try:
        data = json.loads(resp.content)
    except Exception:
        data = {'error': resp.content.decode('utf-8')}
    return resp.status_code, data


def main():
    ensure_user()

    status, token_data = obtain_token()
    results = {'token_post_status': status, 'token_data': token_data}

    headers = {}
    access = token_data.get('access') if isinstance(token_data, dict) else None
    if access:
        headers['HTTP_AUTHORIZATION'] = f'Bearer {access}'

    # create author
    author_payload = {
        'name': 'Test Author',
        'biography': 'Bio',
        'birth_date': '1980-01-01',
        'nationality': 'BR',
    }
    resp = client.post('/api/v1/library/authors/', json.dumps(author_payload), content_type='application/json', **headers)
    try:
        results['create_author_response'] = json.loads(resp.content)
    except Exception:
        results['create_author_response'] = {'text': resp.content.decode('utf-8')}
    results['create_author_status'] = resp.status_code

    # create book (use author id if created)
    book_resp_json = None
    if resp.status_code in (200, 201):
        author_id = results['create_author_response'].get('id')
        book_payload = {
            'title': 'Test Book',
            'subtitle': 'Sub',
            'author_id': author_id,
            'book_description': 'Desc',
            'category': 'Fiction',
            'publisher': 'Pemberley Press',
            'publication_date': '2020-01-01',
            # generate a short unique ISBN per run to avoid unique-constraint errors
            # and respect model max length constraints
            'ISBN': f"ISBN-SMOKE-{uuid.uuid4().hex[:12]}",
            'page_count': 123,
            'last_edition': '2023-01-01',
            'language': 'EN',
            'cover_url': 'http://example.com/cover.jpg'
        }
        resp_b = client.post('/api/v1/library/books/', json.dumps(book_payload), content_type='application/json', **headers)
        try:
            book_resp_json = json.loads(resp_b.content)
        except Exception:
            book_resp_json = {'text': resp_b.content.decode('utf-8')}
        results['create_book_status'] = resp_b.status_code
        results['create_book_response'] = book_resp_json

    # borrow the book
    if book_resp_json and isinstance(book_resp_json, dict) and book_resp_json.get('id'):
        borrow_payload = {'book': book_resp_json['id'], 'days': 7}
        resp_borrow = client.post('/api/v1/library/borrowings/', json.dumps(borrow_payload), content_type='application/json', **headers)
        try:
            results['borrow_response'] = json.loads(resp_borrow.content)
        except Exception:
            results['borrow_response'] = {'text': resp_borrow.content.decode('utf-8')}
        results['borrow_status'] = resp_borrow.status_code

    # list borrowings for the authenticated user
    resp_list = client.get('/api/v1/library/borrowings/', **headers)
    try:
        results['list_borrowings_response'] = json.loads(resp_list.content)
    except Exception:
        results['list_borrowings_response'] = {'text': resp_list.content.decode('utf-8')}
    results['list_borrowings_status'] = resp_list.status_code

    pprint.pprint(results)


if __name__ == '__main__':
    main()
