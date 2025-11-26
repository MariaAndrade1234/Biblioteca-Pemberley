import pytest
from django.utils import timezone
from datetime import timedelta

from library.models import Book, Author, Reservation, Borrowing
from library import services
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_borrow_book_success():
    user = User.objects.create_user(username='u1', email='u1@example.com', password='pw')
    author = Author.objects.create(name='A')
    book = Book.objects.create(title='B', author=author, ISBN='ISBN1')

    borrowing = services.DefaultBorrowingService.borrow(user, book, days=7)

    assert borrowing.user == user
    assert borrowing.book == book
    assert book.status == Book.STATUS_BORROWED


@pytest.mark.django_db
def test_borrow_book_not_available_raises():
    user = User.objects.create_user(username='u2', email='u2@example.com', password='pw')
    author = Author.objects.create(name='A')
    book = Book.objects.create(title='B2', author=author, ISBN='ISBN2', status=Book.STATUS_BORROWED)

    with pytest.raises(services.BookNotAvailable):
        services.DefaultBorrowingService.borrow(user, book)


@pytest.mark.django_db
def test_max_active_borrowings_exceeded():
    user = User.objects.create_user(username='u3', email='u3@example.com', password='pw')
    author = Author.objects.create(name='A')
    # create 5 active borrowings
    for i in range(5):
        b = Book.objects.create(title=f'Book{i}', author=author, ISBN=f'ISBN-max-{i}')
        services.DefaultBorrowingService.borrow(user, b)

    extra_book = Book.objects.create(title='Extra', author=author, ISBN='ISBN-extra')
    with pytest.raises(services.MaxActiveBorrowingsExceeded):
        services.DefaultBorrowingService.borrow(user, extra_book)


@pytest.mark.django_db
def test_renew_blocked_by_reservation():
    user1 = User.objects.create_user(username='u4', email='u4@example.com', password='pw')
    user2 = User.objects.create_user(username='u5', email='u5@example.com', password='pw')
    author = Author.objects.create(name='A')
    book = Book.objects.create(title='BR', author=author, ISBN='ISBN-R')

    borrowing = services.DefaultBorrowingService.borrow(user1, book, days=7)
    # user2 reserves the book
    Reservation.objects.create(user=user2, book=book)

    with pytest.raises(services.BorrowingError):
        services.DefaultBorrowingService.renew(borrowing, extra_days=7)


@pytest.mark.django_db
def test_return_assigns_to_next_reservation():
    user1 = User.objects.create_user(username='u6', email='u6@example.com', password='pw')
    user2 = User.objects.create_user(username='u7', email='u7@example.com', password='pw')
    author = Author.objects.create(name='A')
    book = Book.objects.create(title='BR2', author=author, ISBN='ISBN-R2')

    borrowing = services.DefaultBorrowingService.borrow(user1, book, days=7)
    # user2 reserves
    Reservation.objects.create(user=user2, book=book)

    new_borrowing = services.DefaultBorrowingService.return_borrowing(borrowing)

    # new_borrowing should be for user2 and book should remain borrowed
    assert new_borrowing.user == user2
    assert book.status == Book.STATUS_BORROWED
