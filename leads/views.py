from django.shortcuts import render
from rest_framework import viewsets, filters as drf_filters
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as django_filters
from .models import Lead
from .serializers import LeadSerializer
from core.permissions import IsAdminOrAgent

# Create your views here.

class LeadFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(lookup_expr='iexact')
    agent = django_filters.NumberFilter()
    assigned_to = django_filters.NumberFilter()
    created_by = django_filters.NumberFilter()

    class Meta:
        model = Lead
        fields = ['status', 'agent', 'assigned_to', 'created_by']

class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated, IsAdminOrAgent]
    filter_backends = [django_filters.DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = LeadFilter
    search_fields = ['name', 'mobile', 'email', 'address', 'notes']
    ordering_fields = ['created_at', 'updated_at', 'name', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        queryset = Lead.objects.all()

        if user.is_superuser:
            return queryset
        elif user.is_agent():
            return queryset.filter(agent=user)
        return queryset.none()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, agent=self.request.user)

    def perform_update(self, serializer):
        # Get the instance from the serializer
        instance = serializer.instance
        serializer.save(created_by=instance.created_by)
