from rest_framework import serializers
from django.utils import timezone

from .models import Author, Book, Borrowing
from . import services


class ReservationSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = getattr(__import__('library.models', fromlist=['Reservation']), 'Reservation')
        fields = ['id', 'user', 'book', 'created_at', 'active']
        read_only_fields = ['id', 'user', 'created_at', 'active']

    def create(self, validated_data):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError('Authentication required to reserve a book')

        book = validated_data['book']
        try:
            reservation = services.reserve_book(request.user, book)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))
        return reservation


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'biography', 'birth_date', 'nationality']


class BookSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), source='author', write_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'subtitle', 'author', 'author_id', 'book_description', 'category',
            'publisher', 'publication_date', 'ISBN', 'page_count', 'last_edition', 'language', 'cover_url', 'status'
        ]

    def update(self, instance, validated_data):
        # prevent non-staff users from changing the status field
        request = self.context.get('request')
        if request is not None and not request.user.is_staff:
            if 'status' in validated_data and validated_data['status'] != instance.status:
                raise serializers.ValidationError('Only staff users can change book status')

        return super().update(instance, validated_data)


class BorrowingSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Borrowing
        fields = ['id', 'user', 'book', 'borrow_date', 'return_date', 'returned']
        read_only_fields = ['id', 'user', 'borrow_date', 'return_date', 'returned']

    def create(self, validated_data):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError('Authentication required to borrow a book')

        book = validated_data['book']
        # allow client to pass a 'days' integer in request data to control the period
        days = request.data.get('days', 14)

        try:
            borrowing = services.borrow_book(request.user, book, days=int(days))
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

        return borrowing
