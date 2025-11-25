from django.contrib import admin

# Register your models here.

from . import apps
from .models import Author, Book, Borrowing


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
	list_display = ('name', 'birth_date', 'nationality')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
	list_display = ('title', 'author', 'ISBN', 'status')


@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
	list_display = ('user', 'book', 'borrow_date', 'return_date', 'returned')


@admin.register(getattr(__import__('library.models', fromlist=['Reservation']), 'Reservation'))
class ReservationAdmin(admin.ModelAdmin):
	list_display = ('user', 'book', 'created_at', 'active')

# Register your models here.
