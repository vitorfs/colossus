from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    timezone = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'auth_user'
