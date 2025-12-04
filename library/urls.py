from django.urls import path

from .views import (
    AuthorViewSet,
    BookViewSet,
    BorrowingViewSet,
    ReservationViewSet,
    borrowed_books_by_user,
)

app_name = 'library'

urlpatterns = [
    # Authors
    path('authors/', AuthorViewSet.as_view({'get': 'list', 'post': 'create'}), name='author-list'),
    path('authors/<uuid:pk>/', AuthorViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='author-detail'),

    # Books
    path('books/', BookViewSet.as_view({'get': 'list', 'post': 'create'}), name='book-list'),
    path('books/<uuid:pk>/', BookViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='book-detail'),

    # Borrowings
    path('borrowings/', BorrowingViewSet.as_view({'get': 'list', 'post': 'create'}), name='borrowing-list'),
    path('borrowings/<uuid:pk>/', BorrowingViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='borrowing-detail'),
    path('borrowings/<uuid:pk>/return/', BorrowingViewSet.as_view({'post': 'do_return'}), name='borrowing-return'),
    path('borrowings/<uuid:pk>/renew/', BorrowingViewSet.as_view({'post': 'do_renew'}), name='borrowing-renew'),
    path('borrowings/overdue/', BorrowingViewSet.as_view({'get': 'overdue'}), name='borrowing-overdue'),
    path('borrowings/borrowers/', BorrowingViewSet.as_view({'get': 'borrowers'}), name='borrowing-borrowers'),

    # Reservations
    path('reservations/', ReservationViewSet.as_view({'get': 'list', 'post': 'create'}), name='reservation-list'),
    path('reservations/<uuid:pk>/', ReservationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='reservation-detail'),

    # Convenience: borrowed books by user
    path('users/<int:user_id>/borrowed-books/', borrowed_books_by_user, name='borrowed-books-by-user'),
]
