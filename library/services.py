from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Book, Borrowing, Reservation


class BorrowingError(Exception):
    pass


class BookNotAvailable(BorrowingError):
    pass


class MaxActiveBorrowingsExceeded(BorrowingError):
    pass


class InactiveUserError(BorrowingError):
    pass


def borrow_book(user, book, days: int = 14):
    """Attempt to borrow a book for a user.

    Rules enforced:
    - user must be active
    - user may have at most 5 active (not returned) borrowings
    - book must be in `available` status

    Returns the created Borrowing instance.
    Raises BorrowingError subclasses on business-rule violations.
    """
    if not getattr(user, 'is_active', True):
        raise InactiveUserError('User account is inactive')

    active_count = Borrowing.objects.filter(user=user, returned=False).count()
    if active_count >= 5:
        raise MaxActiveBorrowingsExceeded('User has reached the active borrow limit (5)')

    if book.status != Book.STATUS_AVAILABLE:
        raise BookNotAvailable('Book is not available for borrowing')

    return_date = timezone.now() + timedelta(days=int(days))

    with transaction.atomic():
        # mark book as borrowed
        book.status = Book.STATUS_BORROWED
        book.save(update_fields=['status'])

        borrowing = Borrowing.objects.create(
            user=user,
            book=book,
            borrow_date=timezone.now(),
            return_date=return_date,
        )

    return borrowing


def return_book(borrowing: Borrowing):
    """Mark a borrowing as returned and make the book available again."""
    with transaction.atomic():
        if borrowing.returned:
            return borrowing

        borrowing.returned = True
        borrowing.save(update_fields=['returned'])

        book = borrowing.book
        # if there is a pending reservation, assign the book to the next reserver
        next_reservation = (
            Reservation.objects.filter(book=book, active=True)
            .order_by('created_at')
            .first()
        )

        if next_reservation:
            # create borrowing for reserved user
            reserve_user = next_reservation.user
            next_reservation.active = False
            next_reservation.save(update_fields=['active'])

            new_borrowing = Borrowing.objects.create(
                user=reserve_user,
                book=book,
                borrow_date=timezone.now(),
                return_date=timezone.now() + timedelta(days=14),
            )
            book.status = Book.STATUS_BORROWED
            book.save(update_fields=['status'])

            # optionally return the new borrowing for caller awareness
            return new_borrowing

        book.status = Book.STATUS_AVAILABLE
        book.save(update_fields=['status'])

    return borrowing


def reserve_book(user, book):
    """Create a reservation for a book. Users may reserve borrowed books.

    Raises BorrowingError on invalid state (e.g. duplicate reservation or inactive user).
    """
    if not getattr(user, 'is_active', True):
        raise InactiveUserError('User account is inactive')

    exists = Reservation.objects.filter(user=user, book=book, active=True).exists()
    if exists:
        raise BorrowingError('User already has an active reservation for this book')

    reservation = Reservation.objects.create(user=user, book=book)
    return reservation


def renew_borrowing(borrowing: Borrowing, extra_days: int = 7):
    """Extend the return_date of an active borrowing."""
    if borrowing.returned:
        raise BorrowingError('Cannot renew a returned borrowing')

    # cannot renew if another user has an active reservation for this book
    other_reservation_exists = (
        Reservation.objects.filter(book=borrowing.book, active=True)
        .exclude(user=borrowing.user)
        .exists()
    )
    if other_reservation_exists:
        raise BorrowingError('Cannot renew: another user has an active reservation for this book')

    borrowing.return_date = borrowing.return_date + timedelta(days=int(extra_days))
    borrowing.save(update_fields=['return_date'])
    return borrowing
