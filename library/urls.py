from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import (
    AuthorViewSet,
    BookViewSet,
    BorrowingViewSet,
    ReservationViewSet,
    borrowed_books_by_user,
)

app_name = 'library'

router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'books', BookViewSet, basename='book')
router.register(r'borrowings', BorrowingViewSet, basename='borrowing')
router.register(r'reservations', ReservationViewSet, basename='reservation')

urlpatterns = [
    path('', include(router.urls)),

    # custom borrowing actions
    path('borrowings/<uuid:pk>/return/', BorrowingViewSet.as_view({'post': 'do_return'}), name='borrowing-return'),
    path('borrowings/<uuid:pk>/renew/', BorrowingViewSet.as_view({'post': 'do_renew'}), name='borrowing-renew'),
    path('borrowings/overdue/', BorrowingViewSet.as_view({'get': 'overdue'}), name='borrowing-overdue'),
    path('borrowings/borrowers/', BorrowingViewSet.as_view({'get': 'borrowers'}), name='borrowing-borrowers'),

    # convenience endpoint
    path('users/<int:user_id>/borrowed-books/', borrowed_books_by_user, name='borrowed-books-by-user'),
]
