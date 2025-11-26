#!/usr/bin/env python
"""Extended API requests script: renew/return/reservation/overdue/borrowers and filters.

Run with:
C:/Users/beatr/Biblioteca-Pemberley/venv/Scripts/python.exe scripts/api_requests_extended.py
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
from library.models import Book, Author

# ensure allowed hosts for test client
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
    results = {}
    # create unique usernames per run to avoid interference with previous test data
    suffix = uuid.uuid4().hex[:8]
    apiuser_name = f'apiuser_{suffix}'
    reserver_name = f'reserver_{suffix}'

    ensure_user(apiuser_name, 'Password123', email=f'{apiuser_name}@example.com')
    ensure_user(reserver_name, 'Password123', email=f'{reserver_name}@example.com')

    # get tokens
    s, t = obtain_token(apiuser_name, 'Password123')
    results['apiuser_token_status'] = s
    results['apiuser_token'] = t
    access = t.get('access') if isinstance(t, dict) else None
    headers = {}
    if access:
        headers['HTTP_AUTHORIZATION'] = f'Bearer {access}'

    # create author
    author_payload = {
        'name': 'Extended Author',
        'biography': 'Bio ext',
        'birth_date': '1970-01-01',
        'nationality': 'US',
    }
    resp = client.post('/api/v1/library/authors/', json.dumps(author_payload), content_type='application/json', **headers)
    results['create_author_status'] = resp.status_code
    try:
        results['create_author'] = json.loads(resp.content)
    except Exception:
        results['create_author'] = resp.content.decode('utf-8')

    # create book
    author_id = results['create_author'].get('id') if isinstance(results['create_author'], dict) else None
    book_payload = {
        'title': 'Extended Book',
        'subtitle': '',
        'author_id': author_id,
        'book_description': 'desc',
        'category': 'Nonfiction',
        'publisher': 'P',
        'publication_date': '2022-01-01',
        'ISBN': f'ISBN-EXT-{uuid.uuid4().hex[:8]}',
        'page_count': 200,
        'last_edition': '2024-01-01',
        'language': 'EN',
        'cover_url': 'http://example.com/cover.png'
    }
    resp = client.post('/api/v1/library/books/', json.dumps(book_payload), content_type='application/json', **headers)
    results['create_book_status'] = resp.status_code
    try:
        results['create_book'] = json.loads(resp.content)
    except Exception:
        results['create_book'] = resp.content.decode('utf-8')

    book_id = results['create_book'].get('id') if isinstance(results['create_book'], dict) else None

    # borrow as apiuser
    resp = client.post('/api/v1/library/borrowings/', json.dumps({'book': book_id, 'days': 7}), content_type='application/json', **headers)
    results['borrow_status'] = resp.status_code
    try:
        results['borrow'] = json.loads(resp.content)
    except Exception:
        results['borrow'] = resp.content.decode('utf-8')

    borrow_id = results.get('borrow', {}).get('id') if isinstance(results.get('borrow'), dict) else None

    # attempt renew (should succeed if no reservation)
    resp = client.post(f'/api/v1/library/borrowings/{borrow_id}/renew/', json.dumps({'extra_days': 7}), content_type='application/json', **headers)
    results['renew_status_first'] = resp.status_code
    try:
        results['renew_first'] = json.loads(resp.content)
    except Exception:
        results['renew_first'] = resp.content.decode('utf-8')

    # reserver reserves the book
    s2, t2 = obtain_token(reserver_name, 'Password123')
    results['reserver_token_status'] = s2
    results['reserver_token'] = t2
    access2 = t2.get('access') if isinstance(t2, dict) else None
    headers2 = {'HTTP_AUTHORIZATION': f'Bearer {access2}'} if access2 else {}
    resp = client.post('/api/v1/library/reservations/', json.dumps({'book': book_id}), content_type='application/json', **headers2)
    results['reserve_status'] = resp.status_code
    try:
        results['reserve'] = json.loads(resp.content)
    except Exception:
        results['reserve'] = resp.content.decode('utf-8')

    # now original user attempts to renew again -> should be blocked
    resp = client.post(f'/api/v1/library/borrowings/{borrow_id}/renew/', json.dumps({'extra_days': 7}), content_type='application/json', **headers)
    results['renew_status_blocked'] = resp.status_code
    try:
        results['renew_blocked'] = json.loads(resp.content)
    except Exception:
        results['renew_blocked'] = resp.content.decode('utf-8')

    # return book as apiuser -> should create new borrowing for reserver
    resp = client.post(f'/api/v1/library/borrowings/{borrow_id}/return/', **headers)
    results['return_status'] = resp.status_code
    try:
        results['return'] = json.loads(resp.content)
    except Exception:
        results['return'] = resp.content.decode('utf-8')

    # list borrowings for reserver
    # authenticate as reserver
    client.credentials = {}
    if access2:
        client.defaults.update({'HTTP_AUTHORIZATION': f'Bearer {access2}'})
    resp = client.get('/api/v1/library/borrowings/')
    results['reserver_borrowings_status'] = resp.status_code
    try:
        results['reserver_borrowings'] = json.loads(resp.content)
    except Exception:
        results['reserver_borrowings'] = resp.content.decode('utf-8')

    # overdue list
    resp = client.get('/api/v1/library/borrowings/overdue/')
    results['overdue_status'] = resp.status_code
    try:
        results['overdue'] = json.loads(resp.content)
    except Exception:
        results['overdue'] = resp.content.decode('utf-8')

    # borrowers list
    resp = client.get('/api/v1/library/borrowings/borrowers/')
    results['borrowers_status'] = resp.status_code
    try:
        results['borrowers'] = json.loads(resp.content)
    except Exception:
        results['borrowers'] = resp.content.decode('utf-8')

    # users list filtered by status
    resp = client.get('/api/v1/users/?status=active')
    results['users_active_status'] = resp.status_code
    try:
        results['users_active'] = json.loads(resp.content)
    except Exception:
        results['users_active'] = resp.content.decode('utf-8')

    # books search/filter
    resp = client.get('/api/v1/library/books/?search=Extended&category=Nonfiction')
    results['books_search_status'] = resp.status_code
    try:
        results['books_search'] = json.loads(resp.content)
    except Exception:
        results['books_search'] = resp.content.decode('utf-8')

    pprint.pprint(results)


if __name__ == '__main__':
    main()
