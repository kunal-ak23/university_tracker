from django.contrib import admin
from .models import Lead

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'mobile', 'email', 'status', 'agent', 'assigned_to', 'created_at')
    list_filter = ('status', 'agent', 'assigned_to', 'created_at')
    search_fields = ('name', 'mobile', 'email', 'address', 'notes')
    ordering = ('-created_at',)
