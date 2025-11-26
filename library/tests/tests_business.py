from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from ..models import Author, Book, Borrowing, Reservation
from datetime import timedelta

User = get_user_model()


class BusinessRulesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = Author.objects.create(name='Author BR')
        self.user = User.objects.create_user(username='userbr', email='userbr@example.com', password='Password123')
        self.other = User.objects.create_user(username='otherbr', email='otherbr@example.com', password='Password123')

    def _create_book(self, isbn_suffix='1'):
        return Book.objects.create(
            title=f'Book {isbn_suffix}',
            author=self.author,
            ISBN=f'ISBN-BR-{isbn_suffix}',
            publication_date=timezone.now().date(),
        )

    def test_user_cannot_borrow_more_than_five_books(self):
        self.client.force_authenticate(user=self.user)
        books = [self._create_book(isbn_suffix=str(i)) for i in range(6)]
        statuses = []
        for i, b in enumerate(books):
            resp = self.client.post('/api/v1/library/borrowings/', {'book': str(b.id), 'days': 7}, format='json')
            statuses.append(resp.status_code)
        # first five should be 201, sixth should be 400
        self.assertEqual(statuses[:5], [201]*5)
        self.assertEqual(statuses[5], 400)

    def test_inactive_user_cannot_borrow(self):
        self.user.is_active = False
        self.user.save()
        self.client.force_authenticate(user=self.user)
        b = self._create_book('inactive')
        resp = self.client.post('/api/v1/library/borrowings/', {'book': str(b.id), 'days': 7}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_borrow_updates_book_status_and_return_makes_available(self):
        self.client.force_authenticate(user=self.user)
        b = self._create_book('status')
        resp = self.client.post('/api/v1/library/borrowings/', {'book': str(b.id), 'days': 7}, format='json')
        self.assertEqual(resp.status_code, 201)
        b.refresh_from_db()
        self.assertEqual(b.status, Book.STATUS_BORROWED)

        borrow_id = resp.json().get('id')
        # return
        resp2 = self.client.post(f'/api/v1/library/borrowings/{borrow_id}/return/')
        self.assertEqual(resp2.status_code, 200)
        b.refresh_from_db()
        self.assertEqual(b.status, Book.STATUS_AVAILABLE)

    def test_renew_blocked_by_reservation(self):
        # user borrows
        self.client.force_authenticate(user=self.user)
        b = self._create_book('renew')
        resp = self.client.post('/api/v1/library/borrowings/', {'book': str(b.id), 'days': 7}, format='json')
        self.assertEqual(resp.status_code, 201)
        borrow_id = resp.json().get('id')

        # other reserves
        Reservation.objects.create(user=self.other, book=b)

        # attempt renew -> should be 400
        resp2 = self.client.post(f'/api/v1/library/borrowings/{borrow_id}/renew/', {'extra_days': 7}, format='json')
        self.assertEqual(resp2.status_code, 400)

    def test_return_assigns_to_reserver(self):
        # user borrows
        self.client.force_authenticate(user=self.user)
        b = self._create_book('assign')
        resp = self.client.post('/api/v1/library/borrowings/', {'book': str(b.id), 'days': 7}, format='json')
        self.assertEqual(resp.status_code, 201)
        borrow_id = resp.json().get('id')

        # other reserves
        Reservation.objects.create(user=self.other, book=b)

        # return -> should create new borrowing for reserver
        resp2 = self.client.post(f'/api/v1/library/borrowings/{borrow_id}/return/')
        self.assertEqual(resp2.status_code, 200)

        # reserver should have an active borrowing for that book
        self.client.force_authenticate(user=self.other)
        resp3 = self.client.get('/api/v1/library/borrowings/')
        data = resp3.json()
        found = any(item.get('book') == str(b.id) for item in data.get('results', data))
        self.assertTrue(found)

    def test_return_date_must_be_after_borrow_date_model_validation(self):
        b = self._create_book('validate')
        borrow = Borrowing(user=self.user, book=b, borrow_date=timezone.now(), return_date=timezone.now() - timedelta(days=1))
        with self.assertRaises(ValidationError):
            borrow.full_clean()

    def test_borrowed_books_by_user_endpoint(self):
        self.client.force_authenticate(user=self.user)
        b = self._create_book('listbyuser')
        resp = self.client.post('/api/v1/library/borrowings/', {'book': str(b.id), 'days': 7}, format='json')
        self.assertEqual(resp.status_code, 201)

        resp2 = self.client.get(f'/api/v1/library/users/{self.user.id}/borrowed-books/')
        self.assertEqual(resp2.status_code, 200)
        books = resp2.json()
        self.assertTrue(any(item.get('id') == str(b.id) for item in books))
