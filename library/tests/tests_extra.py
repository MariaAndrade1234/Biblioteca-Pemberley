from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from ..models import Author, Book
import json

User = get_user_model()


class BookCrudAndNegativeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(username='staff', email='s@example.com', password='pass', is_staff=True)
        self.user = User.objects.create_user(username='user', email='u@example.com', password='pass')
        self.author = Author.objects.create(name='Author X')

    def test_book_crud(self):
        self.client.force_authenticate(self.staff)
        payload = {
            'title': 'CRUD Book',
            'subtitle': '',
            'author_id': str(self.author.id),
            'book_description': 'desc',
            'category': 'Test',
            'publisher': 'Pub',
            'publication_date': '2020-01-01',
            'ISBN': 'TEST-ISBN-001',
            'page_count': 100,
            'last_edition': '2021-01-01',
            'language': 'EN',
            'cover_url': 'http://example.com/cover.jpg'
        }
        resp = self.client.post('/api/v1/library/books/', data=json.dumps(payload), content_type='application/json')
        self.assertIn(resp.status_code, (200,201))
        data = resp.json()
        book_id = data.get('id')
        self.assertIsNotNone(book_id)

        r = self.client.get(f'/api/v1/library/books/{book_id}/')
        self.assertEqual(r.status_code, 200)

        self.client.force_authenticate(self.user)
        patch = {'status': 'borrowed'}
        rp = self.client.patch(f'/api/v1/library/books/{book_id}/', data=json.dumps(patch), content_type='application/json')
        self.assertIn(rp.status_code, (400,403))

    def test_cannot_borrow_reserved_book(self):
        self.client.force_authenticate(self.staff)
        payload = {
            'title': 'Reserve Book',
            'subtitle': '',
            'author_id': str(self.author.id),
            'book_description': 'desc',
            'category': 'Test',
            'publisher': 'Pub',
            'publication_date': '2020-01-01',
            'ISBN': 'TEST-ISBN-RES',
            'page_count': 50,
            'last_edition': '2021-01-01',
            'language': 'EN',
            'cover_url': 'http://example.com/cover.jpg'
        }
        resp = self.client.post('/api/v1/library/books/', data=json.dumps(payload), content_type='application/json')
        book = resp.json()
        book_id = book.get('id')

        u1 = User.objects.create_user(username='u1', email='u1@example.com', password='p')
        self.client.force_authenticate(u1)
        rb = self.client.post('/api/v1/library/borrowings/', data=json.dumps({'book': book_id}), content_type='application/json')
        self.assertIn(rb.status_code, (200,201))

        u2 = User.objects.create_user(username='u2', email='u2@example.com', password='p')
        self.client.force_authenticate(u2)
        r2 = self.client.post('/api/v1/library/borrowings/', data=json.dumps({'book': book_id}), content_type='application/json')
        self.assertEqual(r2.status_code, 400)

    def test_renew_blocked_by_other_reservation(self):
        self.client.force_authenticate(self.staff)
        payload = {
            'title': 'RenewBook',
            'subtitle': '',
            'author_id': str(self.author.id),
            'book_description': 'desc',
            'category': 'Test',
            'publisher': 'Pub',
            'publication_date': '2020-01-01',
            'ISBN': 'TEST-ISBN-REN',
            'page_count': 50,
            'last_edition': '2021-01-01',
            'language': 'EN',
            'cover_url': 'http://example.com/cover.jpg'
        }
        resp = self.client.post('/api/v1/library/books/', data=json.dumps(payload), content_type='application/json')
        book_id = resp.json().get('id')

        a = User.objects.create_user(username='a', email='a@example.com', password='p')
        b = User.objects.create_user(username='b', email='b@example.com', password='p')

        self.client.force_authenticate(a)
        borrow = self.client.post('/api/v1/library/borrowings/', data=json.dumps({'book': book_id}), content_type='application/json')
        self.assertIn(borrow.status_code, (200,201))
        borrow_id = borrow.json().get('id')

        self.client.force_authenticate(b)
        res = self.client.post('/api/v1/library/reservations/', data=json.dumps({'book': book_id}), content_type='application/json')
        self.assertIn(res.status_code, (200,201))

        self.client.force_authenticate(a)
        rn = self.client.post(f'/api/v1/library/borrowings/{borrow_id}/renew/', data=json.dumps({'extra_days':7}), content_type='application/json')
        self.assertEqual(rn.status_code, 400)
