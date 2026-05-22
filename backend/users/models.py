from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    STATUS_CHOICES = (
        ('pending', 'Under Review'),
        ('approved', 'Approved / Ticket Generated'),
        ('rejected', 'Rejected / Full'),
    )
    email = models.EmailField(unique=True)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    ticket_file = models.FileField(upload_to='tickets/', null=True, blank=True)
    is_registered = models.BooleanField(default=False)
    
    # Stores dynamic form answers
    registration_data = models.JSONField(default=dict, blank=True)
    
    # NEW: Status field for the dashboard!
    registration_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username'] 

    def __str__(self):
        return self.email