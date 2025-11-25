from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import AuthorViewSet, BookViewSet, BorrowingViewSet, ReservationViewSet, borrowed_books_by_user

router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'books', BookViewSet, basename='book')
router.register(r'borrowings', BorrowingViewSet, basename='borrowing')
router.register(r'reservations', ReservationViewSet, basename='reservation')

urlpatterns = [
    path('', include(router.urls)),
    path('users/<int:user_id>/borrowed-books/', borrowed_books_by_user, name='borrowed-books-by-user'),
]
