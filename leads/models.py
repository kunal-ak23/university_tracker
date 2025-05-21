from django.db import models
from core.models import BaseModel, CustomUser

class Lead(BaseModel):
    LEAD_STATUS_CHOICES = [
        ('hot', 'Hot'),
        ('warm', 'Warm'),
        ('cold', 'Cold'),
        ('closed', 'Closed'),
        ('converted', 'Converted'),
        ('lost', 'Lost'),
        ('not_interested', 'Not Interested'),
    ]

    name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=LEAD_STATUS_CHOICES, default='warm')
    notes = models.TextField(blank=True, null=True)
    agent = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='leads')
    assigned_to = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_leads'
    )

    def __str__(self):
        return f"{self.name} ({self.status})"

    class Meta:
        ordering = ['-created_at']
