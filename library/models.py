import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import TimestampedModel


class Author(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	name = models.CharField(max_length=255)
	biography = models.TextField(blank=True)
	birth_date = models.DateField(null=True, blank=True)
	nationality = models.CharField(max_length=100, blank=True)

	def __str__(self):
		return self.name


class Book(TimestampedModel):
	STATUS_AVAILABLE = 'available'
	STATUS_BORROWED = 'borrowed'
	STATUS_RESERVED = 'reserved'

	STATUS_CHOICES = [
		(STATUS_AVAILABLE, 'Available'),
		(STATUS_BORROWED, 'Borrowed'),
		(STATUS_RESERVED, 'Reserved'),
	]

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(max_length=255)
	subtitle = models.CharField(max_length=255, blank=True)
	author = models.ForeignKey(Author, on_delete=models.PROTECT, related_name='books')
	book_description = models.TextField(blank=True)
	category = models.CharField(max_length=100, blank=True)
	publisher = models.CharField(max_length=255, blank=True)
	publication_date = models.DateField(null=True, blank=True)
	ISBN = models.CharField(max_length=32, unique=True)
	page_count = models.PositiveIntegerField(null=True, blank=True)
	last_edition = models.DateField(null=True, blank=True)
	language = models.CharField(max_length=50, blank=True)
	cover_url = models.URLField(blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)

	def __str__(self):
		return self.title


class Borrowing(TimestampedModel):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='borrowings')
	book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrowings')
	borrow_date = models.DateTimeField(default=timezone.now)
	return_date = models.DateTimeField()
	returned = models.BooleanField(default=False)

	class Meta:
		ordering = ['-borrow_date']

	def clean(self):
		# return_date must be after borrow_date
		if self.return_date <= self.borrow_date:
			from django.core.exceptions import ValidationError

			raise ValidationError('return_date must be after borrow_date')

	def save(self, *args, **kwargs):
		self.clean()
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.user} -> {self.book}"


class Reservation(TimestampedModel):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations')
	book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
	active = models.BooleanField(default=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"Reservation: {self.user} -> {self.book}"

