from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import filters as drf_filters
from django_filters import rest_framework as django_filters
from rest_framework.permissions import IsAuthenticated
from .models import Lead
from .serializers import LeadSerializer
from core.permissions import IsAuthenticatedAndReadOnly

# Create your views here.

class LeadFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status')
    agent = django_filters.NumberFilter(field_name='agent__id')
    assigned_to = django_filters.NumberFilter(field_name='assigned_to__id')
    
    class Meta:
        model = Lead
        fields = ['status', 'agent', 'assigned_to']

class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        django_filters.DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter
    ]
    filterset_class = LeadFilter
    search_fields = ['name', 'mobile', 'email', 'address', 'notes']
    ordering_fields = ['name', 'status', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            # Agents can only see their own leads
            queryset = queryset.filter(agent=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(agent=self.request.user)
