from django.db import models

# Create your models here.
import uuid
from django.core.validators import EmailValidator

class Account(models.Model):
    email = models.EmailField(unique=True)
    account_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    account_name = models.CharField(max_length=100)
    app_secret_token = models.UUIDField(default=uuid.uuid4, editable=False)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.account_name
    

class Destination(models.Model):
    HTTP_METHODS = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT')
    ]

    account = models.ForeignKey(Account, related_name='destinations', on_delete=models.CASCADE)
    url = models.URLField()
    http_method = models.CharField(max_length=4, choices=HTTP_METHODS)
    headers = models.JSONField()

    def __str__(self):
        return f"{self.account.account_name} - {self.url}"