from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Book, Borrowing, Reservation


class BorrowingError(Exception):
    """Base exception for borrowing domain errors."""
    pass


class BookNotAvailable(BorrowingError):
    pass


class MaxActiveBorrowingsExceeded(BorrowingError):
    pass


class InactiveUserError(BorrowingError):
    pass


class BorrowingService:
    """Service object that encapsulates borrowing business rules.

    Methods mirror the previous module-level functions. This class makes it
    easier to test and to inject into views (Dependency Inversion).
    """

    def borrow(self, user, book, days: int = 14):
        if not getattr(user, 'is_active', True):
            raise InactiveUserError('User account is inactive')

        active_count = Borrowing.objects.filter(user=user, returned=False).count()
        if active_count >= 5:
            raise MaxActiveBorrowingsExceeded('User has reached the active borrow limit (5)')

        if book.status != Book.STATUS_AVAILABLE:
            raise BookNotAvailable('Book is not available for borrowing')

        return_date = timezone.now() + timedelta(days=int(days))

        with transaction.atomic():
            locked_book = Book.objects.select_for_update().get(pk=book.pk)
            if locked_book.status != Book.STATUS_AVAILABLE:
                raise BookNotAvailable('Book is not available for borrowing')
            locked_book.status = Book.STATUS_BORROWED
            locked_book.save(update_fields=['status'])

            borrowing = Borrowing.objects.create(
                user=user,
                book=locked_book,
                borrow_date=timezone.now(),
                return_date=return_date,
            )

        return borrowing

    def return_borrowing(self, borrowing: Borrowing):
        with transaction.atomic():
            if borrowing.returned:
                return borrowing

            borrowing.returned = True
            borrowing.save(update_fields=['returned'])

            book = Book.objects.select_for_update().get(pk=borrowing.book.pk)
            next_reservation = (
                Reservation.objects.filter(book=book, active=True)
                .order_by('created_at')
                .first()
            )

            if next_reservation:
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

                return new_borrowing

            book.status = Book.STATUS_AVAILABLE
            book.save(update_fields=['status'])

        return borrowing

    def reserve(self, user, book):
        if not getattr(user, 'is_active', True):
            raise InactiveUserError('User account is inactive')

        exists = Reservation.objects.filter(user=user, book=book, active=True).exists()
        if exists:
            raise BorrowingError('User already has an active reservation for this book')

        reservation = Reservation.objects.create(user=user, book=book)
        return reservation

    def renew(self, borrowing: Borrowing, extra_days: int = 7):
        if borrowing.returned:
            raise BorrowingError('Cannot renew a returned borrowing')

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


DefaultBorrowingService = BorrowingService()


def borrow_book(user, book, days: int = 14):
    return DefaultBorrowingService.borrow(user, book, days=days)


def return_book(borrowing: Borrowing):
    return DefaultBorrowingService.return_borrowing(borrowing)


def reserve_book(user, book):
    return DefaultBorrowingService.reserve(user, book)


def renew_borrowing(borrowing: Borrowing, extra_days: int = 7):
    return DefaultBorrowingService.renew(borrowing, extra_days=extra_days)
