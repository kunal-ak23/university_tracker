from rest_framework import serializers
from .models import Lead
from core.serializers import UserSerializer

class LeadSerializer(serializers.ModelSerializer):
    agent_details = UserSerializer(source='agent', read_only=True)
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'name', 'mobile', 'email', 'address', 'status',
            'notes', 'agent', 'agent_details', 'assigned_to',
            'assigned_to_details', 'created_by', 'created_by_details',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by'] 