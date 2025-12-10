from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

User = settings.AUTH_USER_MODEL

class Company(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive'), ('pending', 'Pending')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile')
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    website = models.TextField(blank=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255)
    industry = models.CharField(max_length=255)
    company_size = models.CharField(max_length=100)
    plan = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    softdelete = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    updated_at = models.DateTimeField(auto_now=True)
    company_since = models.CharField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)

    def __str__(self):
        return self.name

class CompanyUser(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive'), ('pending', 'Pending')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='users')
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=100)
    softdelete = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='company_user_images/', blank=True, null=True)
