from django.contrib.auth.models import AbstractUser
from django.db import models
from core.models import TimestampedModel

class User(AbstractUser, TimestampedModel):
     full_name = models.CharField(max_length=255, verbose_name="Complete Name")
     email = models.EmailField(unique=True, verbose_name="Email Address")
     birthdate = models.DateField(null=True, blank=True, verbose_name="Birthdate")

     EMAIL_FIELD = 'email'
     REQUIRED_FIELDS = ['email', 'full_name']

     class Meta:
         verbose_name = "User"
         verbose_name_plural = "Users"
    
     def __str__(self):
            return self.username
                         



