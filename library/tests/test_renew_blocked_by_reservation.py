from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from library.models import Author, Book, Borrowing, Reservation

User = get_user_model()


class RenewBlockedByReservationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='u1', email='u1@example.com', password='pass')
        self.user2 = User.objects.create_user(username='u2', email='u2@example.com', password='pass')
        self.author = Author.objects.create(name='Author Test')
        self.book = Book.objects.create(
            title='RenewBook', subtitle='', author=self.author, book_description='d', category='fiction', publisher='P', ISBN='ISBN-RB-1', page_count=10, language='EN'
        )

    def test_renew_blocked_when_other_user_reserved(self):
        # user1 borrows
        self.client.force_authenticate(self.user1)
        resp = self.client.post('/api/v1/library/borrowings/', {'book': str(self.book.id), 'days': 7}, format='json')
        self.assertEqual(resp.status_code, 201)
        borrow = Borrowing.objects.filter(user=self.user1, book=self.book, returned=False).first()

        # user2 reserves
        self.client.force_authenticate(self.user2)
        resp = self.client.post('/api/v1/library/reservations/', {'book': str(self.book.id)}, format='json')
        self.assertEqual(resp.status_code, 201)

        # user1 attempts to renew -> should be blocked
        self.client.force_authenticate(self.user1)
        resp = self.client.post(f'/api/v1/library/borrowings/{borrow.id}/renew/', {'extra_days': 7}, format='json')
        self.assertEqual(resp.status_code, 400)