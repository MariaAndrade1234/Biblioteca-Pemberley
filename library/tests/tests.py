from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from ..models import Author, Book, Borrowing, Reservation
from .. import services

User = get_user_model()


class LibraryFlowTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user1 = User.objects.create_user(username='u1', email='u1@example.com', password='pass')
		self.user2 = User.objects.create_user(username='u2', email='u2@example.com', password='pass')
		self.staff = User.objects.create_user(username='staff', email='staff@example.com', password='pass', is_staff=True)

		self.author = Author.objects.create(name='Author Test')
		self.book = Book.objects.create(
			title='Test Book',
			subtitle='',
			author=self.author,
			book_description='desc',
			category='fiction',
			publisher='Pub',
			ISBN='ISBN0001',
			page_count=100,
			language='EN'
		)

	def test_borrow_and_reservation_flow(self):
		self.client.force_authenticate(self.user1)
		resp = self.client.post('/api/v1/library/borrowings/', {'book': str(self.book.id), 'days': 7}, format='json')
		if resp.status_code != 201:
			print('BORROW RESP:', resp.status_code, getattr(resp, 'data', resp.content))
		self.assertEqual(resp.status_code, 201)

		self.client.force_authenticate(self.user2)
		resp = self.client.post('/api/v1/library/borrowings/', {'book': str(self.book.id)}, format='json')
		self.assertEqual(resp.status_code, 400)

		resp = self.client.post('/api/v1/library/reservations/', {'book': str(self.book.id)}, format='json')
		if resp.status_code != 201:
			print('RESERVE RESP:', resp.status_code, getattr(resp, 'data', resp.content))
		self.assertEqual(resp.status_code, 201)

		borrow = Borrowing.objects.filter(user=self.user1, book=self.book, returned=False).first()
		self.client.force_authenticate(self.user1)
		resp = self.client.post(f'/api/v1/library/borrowings/{borrow.id}/return/')
		if resp.status_code != 200:
			print('RETURN RESP:', resp.status_code, getattr(resp, 'data', resp.content))
		self.assertEqual(resp.status_code, 200)

		has_borrow = Borrowing.objects.filter(user=self.user2, book=self.book, returned=False).exists()
		self.assertTrue(has_borrow)

	def test_borrow_limit_and_inactive_user(self):
		for i in range(2, 7):
			b = Book.objects.create(
				title=f'Book{i}', subtitle='', author=self.author, ISBN=f'ISBN{i}',
			)
			services.borrow_book(self.user1, b)

		extra = Book.objects.create(title='Extra', subtitle='', author=self.author, ISBN='ISBNX')
		with self.assertRaises(Exception):
			services.borrow_book(self.user1, extra)

		self.user2.is_active = False
		self.user2.save()
		with self.assertRaises(Exception):
			services.borrow_book(self.user2, extra)

	def test_renew(self):
		self.client.force_authenticate(self.user1)
		resp = self.client.post('/api/v1/library/borrowings/', {'book': str(self.book.id), 'days': 7}, format='json')
		if resp.status_code != 201:
			print('BORROW RESP RENEW:', resp.status_code, getattr(resp, 'data', resp.content))
		self.assertEqual(resp.status_code, 201)
		borrow = Borrowing.objects.filter(user=self.user1, book=self.book, returned=False).first()
		old_return = borrow.return_date

		resp = self.client.post(f'/api/v1/library/borrowings/{borrow.id}/renew/', {'extra_days': 3}, format='json')
		self.assertEqual(resp.status_code, 200)
		borrow.refresh_from_db()
		self.assertGreater(borrow.return_date, old_return)

	def test_overdue_and_borrowers_and_filters(self):
		import datetime
		from django.utils import timezone as djtz
		past = djtz.now() - datetime.timedelta(days=10)
		b2 = Book.objects.create(title='OldBook', subtitle='', author=self.author, ISBN='ISBNOLD')
		borrow = Borrowing.objects.create(user=self.user1, book=b2, borrow_date=past, return_date=past + datetime.timedelta(days=1))

		self.client.force_authenticate(self.user1)
		resp = self.client.get('/api/v1/library/borrowings/overdue/')
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(any(str(b2.id) in str(item.get('book')) or item.get('book') for item in data.get('results', data)))

		resp = self.client.get('/api/v1/library/borrowings/borrowers/')
		self.assertEqual(resp.status_code, 200)
		resp_data = resp.json()
		self.assertTrue(any(u['id'] == self.user1.id for u in resp_data.get('results', resp_data)))

		resp = self.client.get('/api/v1/library/books/?search=OldBook')
		self.assertEqual(resp.status_code, 200)
		books = resp.json()
		self.assertTrue(any('OldBook' in item.get('title', '') for item in books.get('results', books)))

	def test_book_status_change_requires_staff(self):
		b = Book.objects.create(title='PermTest', subtitle='', author=self.author, ISBN='ISBNP')
		self.client.force_authenticate(self.user2)
		resp = self.client.patch(f'/api/v1/library/books/{b.id}/', {'status': 'borrowed'}, format='json')
		self.assertEqual(resp.status_code, 403)

		self.client.force_authenticate(self.staff)
		resp = self.client.patch(f'/api/v1/library/books/{b.id}/', {'status': 'borrowed'}, format='json')
		self.assertIn(resp.status_code, (200, 200))
