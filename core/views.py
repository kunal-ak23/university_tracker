from rest_framework import viewsets, generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import OrderingFilter, SearchFilter
from core.logger_service import get_logger
from django.db.models import Q
from decimal import Decimal
from datetime import datetime, timedelta
from calendar import monthrange
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import msal
import requests
import logging

logger = get_logger()

from .models import (
    OEM, Program, University, Stream, Contract, ContractProgram, Batch,
    Billing, Payment, ContractFile, TaxRate, CustomUser, Invoice, ChannelPartner,
    ChannelPartnerProgram, ChannelPartnerStudent, Student, ProgramBatch,
    UniversityEvent
)
from .serializers import (
    OEMSerializer, ProgramSerializer, UniversitySerializer, StreamSerializer,
    ContractSerializer, ContractProgramSerializer, BatchSerializer, BillingSerializer,
    PaymentSerializer, ContractFileSerializer, TaxRateSerializer, RegisterSerializer,
    UserSerializer, CustomTokenObtainPairSerializer, InvoiceSerializer, DashboardBillingSerializer,
    DashboardInvoiceSerializer, DashboardPaymentSerializer, ChannelPartnerSerializer,
    ChannelPartnerProgramSerializer, ChannelPartnerStudentSerializer, StudentSerializer,
    ProgramBatchSerializer, UniversityEventSerializer, UniversityEventApprovalSerializer,
    UniversityEventSubmissionSerializer, UniversityEventInviteeSerializer
)
from .permissions import IsAuthenticatedAndReadOnly, IsAuthenticatedWithRoleBasedAccess

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

# Add a filter class for Program
class ProgramFilter(filters.FilterSet):
    oem = filters.NumberFilter(field_name='provider__id')  # Filter by OEM ID
    provider = filters.NumberFilter(field_name='provider__id')  # Alternative name
    
    class Meta:
        model = Program
        fields = ['oem', 'provider']  # Allow filtering by either name

class ContractFilter(filters.FilterSet):
    oem = filters.NumberFilter(field_name='oem__id')
    university = filters.NumberFilter(field_name='university__id')
    
    class Meta:
        model = Contract
        fields = ['oem', 'university', 'status']

class OEMViewSet(viewsets.ModelViewSet):
    queryset = OEM.objects.all()
    serializer_class = OEMSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']  # default ordering
    search_fields = ['name', 'website', 'contact_email', 'contact_phone', 'address']

class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ProgramFilter
    ordering_fields = ['name', 'program_code', 'created_at', 'updated_at']
    ordering = ['name']
    search_fields = ['name', 'program_code', 'description', 'prerequisites', 'provider__name']

class UniversityViewSet(viewsets.ModelViewSet):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['name', 'established_year', 'created_at', 'updated_at']
    ordering = ['name']
    search_fields = ['name', 'website', 'contact_email', 'contact_phone', 'address', 'accreditation']

class StreamFilter(filters.FilterSet):
    university = filters.NumberFilter(field_name='university__id')
    
    class Meta:
        model = Stream
        fields = ['university']

class StreamViewSet(viewsets.ModelViewSet):
    queryset = Stream.objects.all()
    serializer_class = StreamSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = StreamFilter
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    search_fields = ['name', 'description', 'university__name']

class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ContractFilter
    parser_classes = (MultiPartParser, FormParser)
    ordering_fields = ['name', 'status', 'start_date', 'end_date', 'created_at', 'updated_at']
    ordering = ['-created_at']  # newest first
    search_fields = ['name', 'status', 'notes', 'oem__name', 'university__name']

    def create(self, request, *args, **kwargs):
        try:
            logger.info(f"Creating new contract")
            logger.info(f"Request data: {request.data}")
            
            # Handle contract data
            contract_data = {
                'name': request.data.get('name'),
                'university_id': request.data.get('university'),
                'oem_id': request.data.get('oem'),
                'cost_per_student': request.data.get('cost_per_student'),
                'oem_transfer_price': request.data.get('oem_transfer_price'),
                'start_date': request.data.get('start_date'),
                'end_date': request.data.get('end_date'),
                'tax_rate_id': request.data.get('tax_rate'),
                'status': request.data.get('status', 'active'),
                'notes': request.data.get('notes'),
            }

            # Log tax_rate for debugging
            logger.info(f"Tax Rate from request: {request.data.get('tax_rate')}")

            # Handle array fields
            programs = request.data.getlist('programs_ids[]') or request.data.getlist('programs[]')
            streams = request.data.getlist('streams_ids[]') or request.data.getlist('streams[]')
            
            if programs:
                contract_data['programs_ids'] = programs
            if streams:
                contract_data['streams_ids'] = streams
            
            # Remove None values but keep empty strings
            contract_data = {k: v for k, v in contract_data.items() if v is not None}
            
            logger.info(f"Processed contract data: {contract_data}")

            # Validate required fields
            required_fields = ['name', 'university_id', 'oem_id', 'cost_per_student', 'tax_rate_id']
            missing_fields = [field for field in required_fields if field not in contract_data]
            if missing_fields:
                return Response(
                    {"errors": f"Missing required fields: {', '.join(missing_fields)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if files are present
            files = request.FILES.getlist('files')
            if not files:
                return Response(
                    {"errors": "At least one contract file is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create contract
            serializer = self.get_serializer(data=contract_data)
            if not serializer.is_valid():
                logger.error(f"Validation errors: {serializer.errors}")
                return Response(
                    {"errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            self.perform_create(serializer)

            # Handle files
            logger.info(f"Processing {len(files)} files")
            for file in files:
                ContractFile.objects.create(
                    contract=serializer.instance,
                    file=file,
                    file_type='document',
                    description=file.name,
                    uploaded_by=request.user
                )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Contract creation error: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            logger.info(f"Updating contract {instance.id}")
            logger.info(f"Request data: {request.data}")
            
            # Handle contract data
            contract_data = {
                'name': request.data.get('name'),
                'university_id': request.data.get('university'),
                'oem_id': request.data.get('oem'),
                'cost_per_student': request.data.get('cost_per_student'),
                'oem_transfer_price': request.data.get('oem_transfer_price'),
                'start_date': request.data.get('start_date'),
                'end_date': request.data.get('end_date'),
                'tax_rate_id': request.data.get('tax_rate'),
                'status': request.data.get('status'),
                'notes': request.data.get('notes'),
            }

            # Handle array fields
            programs = request.data.getlist('programs_ids[]') or request.data.getlist('programs[]')
            streams = request.data.getlist('streams_ids[]') or request.data.getlist('streams[]')
            
            if programs:
                contract_data['programs_ids'] = programs
            if streams:
                contract_data['streams_ids'] = streams
            
            # Remove None values
            contract_data = {k: v for k, v in contract_data.items() if v is not None}
            
            logger.info(f"Processed contract data: {contract_data}")

            # Update contract
            serializer = self.get_serializer(instance, data=contract_data, partial=True)
            if not serializer.is_valid():
                logger.error(f"Validation errors: {serializer.errors}")
                return Response(
                    {"errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            self.perform_update(serializer)

            # Handle files if present
            files = request.FILES.getlist('files')
            if files:
                logger.info(f"Processing {len(files)} files")
                for file in files:
                    ContractFile.objects.create(
                        contract=instance,
                        file=file,
                        file_type='document',
                        description=file.name,
                        uploaded_by=request.user
                    )

            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Contract update error: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class ContractProgramViewSet(viewsets.ModelViewSet):
    queryset = ContractProgram.objects.all()
    serializer_class = ContractProgramSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]

class BatchFilter(filters.FilterSet):
    stream = filters.NumberFilter(field_name='stream__id')
    contract = filters.NumberFilter(field_name='contract__id')
    status = filters.CharFilter(field_name='status')
    
    class Meta:
        model = Batch
        fields = ['stream', 'contract', 'status']

class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = BatchFilter
    ordering_fields = ['name', 'start_year', 'end_year', 'created_at', 'updated_at']
    ordering = ['-created_at']
    search_fields = ['name', 'notes', 'contract__name', 'stream__name']

class BillingViewSet(viewsets.ModelViewSet):
    queryset = Billing.objects.all()
    serializer_class = BillingSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['name', 'created_at', 'updated_at', 'status']
    ordering = ['-created_at']
    search_fields = ['name', 'notes']
    filterset_fields = ['status']

    def create(self, request, *args, **kwargs):
        """Create a new billing and return with redirect info"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        billing = serializer.save()
        headers = self.get_success_headers(serializer.data)
        
        response_data = {
            **serializer.data,
            'redirect': {
                'id': billing.id,
                'path': f'/billings/{billing.id}/edit'
            }
        }
        
        return Response(
            response_data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a billing by setting it to active and creating snapshots"""
        try:
            billing = self.get_object()
            billing.publish()
            serializer = self.get_serializer(billing)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error publishing billing {pk}: {str(e)}")
            return Response(
                {"error": "Failed to publish billing"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a billing"""
        try:
            billing = self.get_object()
            billing.archive()
            serializer = self.get_serializer(billing)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error archiving billing {pk}: {str(e)}")
            return Response(
                {"error": "Failed to archive billing"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]

class ContractFileViewSet(viewsets.ModelViewSet):
    queryset = ContractFile.objects.all()
    serializer_class = ContractFileSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

class TaxRateViewSet(viewsets.ModelViewSet):
    queryset = TaxRate.objects.all()
    serializer_class = TaxRateSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]

class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        try:
            # First try to authenticate with the provided credentials
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                # Get user by email or username
                lookup_field = request.data.get('email', request.data.get('username'))
                
                try:
                    if '@' in lookup_field:
                        user = CustomUser.objects.get(email=lookup_field)
                    else:
                        user = CustomUser.objects.get(username=lookup_field)

                    # Determine role
                    if user.is_superuser:
                        role = 'admin'
                    else:
                        role = user.role

                    # Add user info to response
                    response.data.update({
                        'role': role,
                        'user_id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'full_name': f"{user.first_name} {user.last_name}".strip() or user.email
                    })
                    
                except CustomUser.DoesNotExist:
                    return Response(
                        {'error': 'User not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                    
            return response
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    authentication_classes = []

    def perform_create(self, serializer):
        user = serializer.save()
        # Set the role to university_poc for testing
        user.role = 'university_poc'
        user.save()

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Add UserFilter class
class UserFilter(filters.FilterSet):
    role = filters.CharFilter(method='filter_role')
    roles = filters.CharFilter(method='filter_multiple_roles')
    
    class Meta:
        model = CustomUser
        fields = ['role', 'roles']
    
    def filter_role(self, queryset, name, value):
        if value == 'university_poc':
            return queryset.filter(role='university_poc')
        elif value == 'provider_poc':
            return queryset.filter(role='provider_poc')
        elif value == 'superuser':
            return queryset.filter(is_superuser=True)
        return queryset

    def filter_multiple_roles(self, queryset, name, value):
        roles = value.split(',')
        q = Q()
        for role in roles:
            role = role.strip()
            if role == 'university_poc':
                q |= Q(role='university_poc')
            elif role == 'provider_poc':
                q |= Q(role='provider_poc')
            elif role == 'superuser':
                q |= Q(is_superuser=True)
        return queryset.filter(q)

# Add UserViewSet
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = UserFilter
    queryset = CustomUser.objects.all().prefetch_related(
        'oem_pocs',
        'university_pocs'
    ).select_related()

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Get role from query params
        role = self.request.query_params.get('role', None)
        if role:
            if role == 'university_poc':
                queryset = queryset.filter(role='university_poc')
            elif role == 'provider_poc':
                queryset = queryset.filter(role='provider_poc')
            elif role == 'superuser':
                queryset = queryset.filter(is_superuser=True)
        
        return queryset.order_by('username')

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['issue_date', 'due_date', 'amount', 'status', 'created_at']
    ordering = ['-created_at']
    search_fields = ['notes']
    filterset_fields = ['status', 'billing']
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        try:
            data = request.data.dict() if hasattr(request.data, 'dict') else request.data
            proforma_invoice = request.FILES.get('proforma_invoice')
            actual_invoice = request.FILES.get('actual_invoice')
            
            if proforma_invoice:
                data['proforma_invoice'] = proforma_invoice
            if actual_invoice:
                data['actual_invoice'] = actual_invoice

            # Convert amount to Decimal if it's a string
            if 'amount' in data and isinstance(data['amount'], str):
                data['amount'] = Decimal(data['amount'])

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            logger.error(f"Error creating invoice: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            data = request.data.dict() if hasattr(request.data, 'dict') else request.data

            proforma_invoice = request.FILES.get('proforma_invoice')
            actual_invoice = request.FILES.get('actual_invoice')
            
            if proforma_invoice:
                data['proforma_invoice'] = proforma_invoice
            if actual_invoice:
                data['actual_invoice'] = actual_invoice

            serializer = self.get_serializer(instance, data=data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error updating invoice: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def upload_proforma(self, request, pk=None):
        """Upload proforma invoice file"""
        try:
            invoice = self.get_object()
            proforma_file = request.FILES.get('proforma_invoice')
            
            if not proforma_file:
                return Response(
                    {"error": "No file provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            invoice.proforma_invoice = proforma_file
            invoice.save()
            
            serializer = self.get_serializer(invoice)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error uploading proforma invoice: {str(e)}")
            return Response(
                {"error": "Failed to upload proforma invoice"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def upload_actual(self, request, pk=None):
        """Upload actual invoice file"""
        try:
            invoice = self.get_object()
            actual_file = request.FILES.get('actual_invoice')
            
            if not actual_file:
                return Response(
                    {"error": "No file provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            invoice.actual_invoice = actual_file
            invoice.save()
            
            serializer = self.get_serializer(invoice)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error uploading actual invoice: {str(e)}")
            return Response(
                {"error": "Failed to upload actual invoice"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Blacklist the refresh token if you're using it
            # Add any cleanup needed
            return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get dashboard summary including revenue, batches, invoices, and payments"""
        today = timezone.now()
        current_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

        # Calculate total revenue
        current_revenue = Payment.objects.filter(
            status='completed',
            payment_date__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0

        previous_revenue = Payment.objects.filter(
            status='completed',
            payment_date__gte=previous_month_start,
            payment_date__lt=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0

        percentage_change = (
            ((current_revenue - previous_revenue) / previous_revenue * 100)
            if previous_revenue > 0 else 0
        )

        # Get active batches info
        active_batches = Batch.objects.filter(status='ongoing')
        new_batches = active_batches.filter(created_at__gte=current_month_start)

        # Get pending invoices
        pending_invoices = Invoice.objects.exclude(status='paid')
        
        # Get overdue payments (invoices past due date with unpaid amount)
        overdue_payments = Invoice.objects.filter(
            due_date__lt=today,
            status__in=['unpaid', 'partially_paid']
        )

        return Response({
            'total_revenue': {
                'current': current_revenue,
                'previous': previous_revenue,
                'percentage_change': round(percentage_change, 2)
            },
            'active_batches': {
                'current': active_batches.count(),
                'new_this_month': new_batches.count()
            },
            'pending_invoices': {
                'count': pending_invoices.count(),
                'total_value': pending_invoices.aggregate(
                    total=Sum('amount') - Sum('amount_paid')
                )['total'] or 0
            },
            'overdue_payments': {
                'count': overdue_payments.count(),
                'total_value': overdue_payments.aggregate(
                    total=Sum('amount') - Sum('amount_paid')
                )['total'] or 0
            }
        })

    @action(detail=False, methods=['get'])
    def revenue_overview(self, request):
        """Get monthly revenue overview"""
        year = int(request.query_params.get('year', datetime.now().year))
        month = request.query_params.get('month')

        payments = Payment.objects.filter(
            status='completed',
            payment_date__year=year
        )

        if month:
            payments = payments.filter(payment_date__month=int(month))

        revenue_data = (
            payments
            .annotate(month=TruncMonth('payment_date'))
            .values('month')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )

        return Response({
            'data': [
                {
                    'name': item['month'].strftime('%B'),
                    'total': item['total']
                }
                for item in revenue_data
            ]
        })

    @action(detail=False, methods=['get'])
    def recent_invoices(self, request):
        """Get recent invoices with pagination"""
        limit = int(request.query_params.get('limit', 5))
        page = int(request.query_params.get('page', 1))

        invoices = Invoice.objects.all().order_by('-created_at')
        paginator = StandardResultsSetPagination()
        paginator.page_size = limit
        
        paginated_invoices = paginator.paginate_queryset(invoices, request)
        serializer = DashboardInvoiceSerializer(paginated_invoices, many=True)
        
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent_payments(self, request):
        """Get recent payments with pagination"""
        limit = int(request.query_params.get('limit', 5))
        page = int(request.query_params.get('page', 1))

        payments = Payment.objects.all().order_by('-created_at')
        paginator = StandardResultsSetPagination()
        paginator.page_size = limit
        
        paginated_payments = paginator.paginate_queryset(payments, request)
        serializer = DashboardPaymentSerializer(paginated_payments, many=True)
        
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue_billings(self, request):
        """Get overdue billings with pagination"""
        limit = int(request.query_params.get('limit', 5))
        page = int(request.query_params.get('page', 1))

        today = timezone.now().date()
        
        # Get billings with overdue invoices
        overdue_billings = (
            Billing.objects
            .filter(
                status__in=['active', 'paid'],
                invoices__due_date__lt=today,
                invoices__status__in=['unpaid', 'partially_paid']
            )
            .distinct()
            .order_by('invoices__due_date')
        )

        paginator = StandardResultsSetPagination()
        paginator.page_size = limit
        
        paginated_billings = paginator.paginate_queryset(overdue_billings, request)
        serializer = DashboardBillingSerializer(paginated_billings, many=True)
        
        return paginator.get_paginated_response(serializer.data)

class ChannelPartnerFilter(filters.FilterSet):
    status = filters.CharFilter(field_name='status')
    poc = filters.NumberFilter(field_name='poc__id')
    
    class Meta:
        model = ChannelPartner
        fields = ['status', 'poc']

class ChannelPartnerViewSet(viewsets.ModelViewSet):
    queryset = ChannelPartner.objects.all()
    serializer_class = ChannelPartnerSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ChannelPartnerFilter
    ordering_fields = ['name', 'status', 'created_at', 'updated_at']
    ordering = ['-created_at']
    search_fields = ['name', 'contact_email', 'contact_phone', 'notes']

class ChannelPartnerProgramFilter(filters.FilterSet):
    channel_partner = filters.NumberFilter(field_name='channel_partner__id')
    program = filters.NumberFilter(field_name='program__id')
    is_active = filters.BooleanFilter(field_name='is_active')
    
    class Meta:
        model = ChannelPartnerProgram
        fields = ['channel_partner', 'program', 'is_active']

class ChannelPartnerProgramViewSet(viewsets.ModelViewSet):
    queryset = ChannelPartnerProgram.objects.all()
    serializer_class = ChannelPartnerProgramSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ChannelPartnerProgramFilter
    ordering_fields = ['transfer_price', 'created_at', 'updated_at']
    ordering = ['-created_at']
    search_fields = ['notes']

class ChannelPartnerStudentFilter(filters.FilterSet):
    channel_partner = filters.NumberFilter(field_name='channel_partner__id')
    batch = filters.NumberFilter(field_name='batch__id')
    status = filters.CharFilter(field_name='status')
    
    class Meta:
        model = ChannelPartnerStudent
        fields = ['channel_partner', 'batch', 'status']

class ChannelPartnerStudentViewSet(viewsets.ModelViewSet):
    queryset = ChannelPartnerStudent.objects.all()
    serializer_class = ChannelPartnerStudentSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ChannelPartnerStudentFilter
    ordering_fields = ['student_name', 'enrollment_date', 'created_at', 'updated_at']
    ordering = ['-created_at']
    search_fields = ['student_name', 'student_email', 'student_phone', 'notes']

class StudentFilter(filters.FilterSet):
    enrollment_source = filters.CharFilter(field_name='enrollment_source')
    status = filters.CharFilter(field_name='status')
    
    class Meta:
        model = Student
        fields = ['enrollment_source', 'status']

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = StudentFilter
    ordering_fields = ['name', 'email', 'enrollment_source', 'status', 'created_at', 'updated_at']
    ordering = ['name']
    search_fields = ['name', 'email', 'phone', 'address', 'notes']

class ProgramBatchFilter(filters.FilterSet):
    program = filters.NumberFilter(field_name='program__id')
    status = filters.CharFilter(field_name='status')
    
    class Meta:
        model = ProgramBatch
        fields = ['program', 'status']

class ProgramBatchViewSet(viewsets.ModelViewSet):
    queryset = ProgramBatch.objects.all()
    serializer_class = ProgramBatchSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ProgramBatchFilter
    ordering_fields = ['name', 'start_date', 'end_date', 'status', 'created_at', 'updated_at']
    ordering = ['-start_date']
    search_fields = ['name', 'notes', 'program__name']

class UniversityEventFilter(filters.FilterSet):
    university = filters.NumberFilter(field_name='university__id')
    batch = filters.NumberFilter(field_name='batch__id')
    status = filters.CharFilter(field_name='status')
    created_by = filters.NumberFilter(field_name='created_by__id')
    approved_by = filters.NumberFilter(field_name='approved_by__id')
    start_date = filters.DateFilter(field_name='start_datetime', lookup_expr='gte')
    end_date = filters.DateFilter(field_name='end_datetime', lookup_expr='lte')
    
    class Meta:
        model = UniversityEvent
        fields = ['university', 'batch', 'status', 'created_by', 'approved_by', 'start_date', 'end_date']


class UniversityEventViewSet(viewsets.ModelViewSet):
    queryset = UniversityEvent.objects.all()
    serializer_class = UniversityEventSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = UniversityEventFilter
    ordering_fields = ['title', 'start_datetime', 'end_datetime', 'status', 'created_at', 'updated_at']
    ordering = ['-start_datetime']  # upcoming events first
    search_fields = ['title', 'description', 'location', 'notes', 'university__name', 'batch__name']

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # If user is university POC, show only events for their university
        if user.is_university_poc():
            queryset = queryset.filter(university__poc=user)
        # If user is provider POC, show events for their OEMs
        elif user.is_provider_poc():
            queryset = queryset.filter(batch__contract__oem__poc=user)
        
        return queryset.select_related(
            'university', 'batch', 'created_by', 'approved_by'
        )

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        """Submit event for approval"""
        event = self.get_object()
        
        try:
            event.submit_for_approval()
            return Response({
                'message': 'Event submitted for approval successfully.',
                'status': event.status
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve or reject an event"""
        event = self.get_object()
        serializer = UniversityEventApprovalSerializer(data=request.data)
        
        if serializer.is_valid():
            action = serializer.validated_data['action']
            reason = serializer.validated_data.get('reason', '')
            
            try:
                if action == 'approve':
                    event.approve(request.user)
                    return Response({
                        'message': 'Event approved successfully.',
                        'status': event.status
                    }, status=status.HTTP_200_OK)
                elif action == 'reject':
                    event.reject(request.user, reason)
                    return Response({
                        'message': 'Event rejected successfully.',
                        'status': event.status,
                        'rejection_reason': reason
                    }, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update event status based on current time"""
        event = self.get_object()
        
        try:
            event.update_status()
            return Response({
                'message': 'Event status updated successfully.',
                'status': event.status
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def invitees(self, request, pk=None):
        """Get list of invitees for the event"""
        event = self.get_object()
        invitees = event.get_invitees()
        return Response(invitees, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def manage_invitees(self, request, pk=None):
        """Add or remove invitees from the event"""
        event = self.get_object()
        serializer = UniversityEventInviteeSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            action = serializer.validated_data['action']
            
            if action == 'add':
                event.add_invitee(email)
                return Response({
                    'message': f'Email {email} added to invitees successfully.',
                    'invitees': event.invitees
                }, status=status.HTTP_200_OK)
            elif action == 'remove':
                event.remove_invitee(email)
                return Response({
                    'message': f'Email {email} removed from invitees successfully.',
                    'invitees': event.invitees
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def integration_status(self, request, pk=None):
        """Get integration status for the event"""
        event = self.get_object()
        return Response({
            'integration_status': event.integration_status,
            'outlook_calendar_id': event.outlook_calendar_id,
            'outlook_calendar_url': event.outlook_calendar_url,
            'notion_page_id': event.notion_page_id,
            'notion_page_url': event.notion_page_url,
            'integration_notes': event.integration_notes
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def trigger_outlook_integration(self, request, pk=None):
        """Manually trigger Outlook integration for an event"""
        event = self.get_object()
        
        if not event.is_approved():
            return Response(
                {"error": "Event must be approved before triggering Outlook integration"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is authenticated with Microsoft Graph
        access_token = request.session.get("access_token")
        if not access_token:
            return Response(
                {"error": "Not authenticated with Microsoft Graph. Please complete the OAuth flow first."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            success = event.trigger_outlook_integration(request)
            if success:
                return Response({
                    "message": "Outlook integration triggered successfully",
                    "outlook_calendar_id": event.outlook_calendar_id,
                    "outlook_calendar_url": event.outlook_calendar_url,
                })
            else:
                return Response(
                    {"error": "Failed to trigger Outlook integration. Check logs for details."}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return Response(
                {"error": f"Failed to trigger Outlook integration: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MicrosoftGraphAuthViewSet(viewsets.ViewSet):
    """ViewSet for Microsoft Graph authentication and event creation"""
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['login', 'callback', 'create_event_form']:
            # No authentication required for auth flow
            permission_classes = []
        else:
            # Authentication required for other actions
            permission_classes = [IsAuthenticatedWithRoleBasedAccess]
        return [permission() for permission in permission_classes]
    
    def _build_msal_app(self):
        """Build MSAL application instance"""
        return msal.ConfidentialClientApplication(
            settings.GRAPH_CLIENT_ID,
            authority=settings.GRAPH_AUTHORITY,
            client_credential=settings.GRAPH_CLIENT_SECRET
        )
    
    @action(detail=False, methods=['get'])
    def login(self, request):
        """Initiate Microsoft Graph OAuth2 login flow"""
        # Check configuration
        missing_config = []
        if not settings.GRAPH_CLIENT_ID:
            missing_config.append("GRAPH_CLIENT_ID")
        if not settings.GRAPH_CLIENT_SECRET:
            missing_config.append("GRAPH_CLIENT_SECRET")
        if not settings.GRAPH_TENANT:
            missing_config.append("GRAPH_TENANT")
        
        if missing_config:
            error_msg = f"Microsoft Graph configuration incomplete. Missing: {', '.join(missing_config)}"
            logger.error(error_msg)
            return Response(
                {"error": error_msg}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            flow = self._build_msal_app().initiate_auth_code_flow(
                scopes=settings.GRAPH_SCOPES,
                redirect_uri=request.build_absolute_uri("/api/auth/outlook/callback")
            )
            request.session["auth_flow"] = flow
            logger.info("Auth flow initiated successfully")
            return redirect(flow["auth_uri"])
        except Exception as e:
            logger.error(f"Failed to initiate auth flow: {str(e)}")
            return Response(
                {"error": f"Failed to initiate authentication: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def callback(self, request):
        """Handle Microsoft Graph OAuth2 callback"""
        try:
            flow = request.session.pop("auth_flow", {})
            if not flow:
                return Response(
                    {"error": "No auth flow found in session"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = self._build_msal_app().acquire_token_by_auth_code_flow(
                flow, request.GET.dict()
            )
            
            if "error" in result:
                return Response(
                    {"error": result.get("error_description", "Authentication failed")}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            request.session["access_token"] = result["access_token"]
            request.session["graph_user"] = result.get("id_token_claims", {})
            
            return redirect("/api/university-events/")  # Redirect to events page
            
        except Exception as e:
            logger.error(f"Auth callback failed: {str(e)}")
            return Response(
                {"error": "Authentication callback failed"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def create_group_event(self, request):
        """Create an event in the M365 Group calendar"""
        token = request.session.get("access_token")
        if not token:
            return Response(
                {"error": "No access token found. Please authenticate first."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not settings.GRAPH_GROUP_ID:
            return Response(
                {"error": "Group ID not configured"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            # Extract event data from request - support both POST data and JSON
            if request.content_type == 'application/json':
                event_data = request.data
            else:
                event_data = request.POST
            
            # Prepare the payload for Microsoft Graph
            payload = {
                "subject": event_data.get("title"),
                "body": {
                    "contentType": "HTML", 
                    "content": event_data.get("description", "")
                },
                "start": {
                    "dateTime": event_data.get("start_iso") or event_data.get("start_datetime"),
                    "timeZone": "India Standard Time"
                },
                "end": {
                    "dateTime": event_data.get("end_iso") or event_data.get("end_datetime"),
                    "timeZone": "India Standard Time"
                },
                "location": {
                    "displayName": event_data.get("location", "")
                }
            }
            
            # Add Teams meeting if requested
            if event_data.get("is_teams_meeting", False):
                payload["isOnlineMeeting"] = True
                payload["onlineMeetingProvider"] = "teamsForBusiness"
            
            # Add attendees if provided
            attendees_csv = event_data.get("attendees_csv", "")
            if attendees_csv:
                payload["attendees"] = [
                    {
                        "emailAddress": {"address": e.strip()},
                        "type": "required"
                    } for e in attendees_csv.split(",") if e.strip()
                ]
            
            # Make the API call to Microsoft Graph
            response = requests.post(
                f"https://graph.microsoft.com/v1.0/groups/{settings.GRAPH_GROUP_ID}/events",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=20
            )
            
            return Response(response.json(), status=response.status_code)
                
        except Exception as e:
            logger.error(f"Failed to create group event: {str(e)}")
            return Response(
                {"error": f"Failed to create event: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get', 'post'])
    def create_event_form(self, request):
        """Simple form for creating events (for testing)"""
        if request.method == 'GET':
            # Return a simple HTML form
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Create M365 Group Event</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .form-group { margin-bottom: 15px; }
                    label { display: block; margin-bottom: 5px; font-weight: bold; }
                    input, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                    button { background: #0078d4; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                    button:hover { background: #106ebe; }
                </style>
            </head>
            <body>
                <h1>Create M365 Group Event</h1>
                <form method="POST">
                    <div class="form-group">
                        <label for="title">Title:</label>
                        <input type="text" id="title" name="title" required>
                    </div>
                    <div class="form-group">
                        <label for="description">Description:</label>
                        <textarea id="description" name="description" rows="4"></textarea>
                    </div>
                    <div class="form-group">
                        <label for="start_iso">Start Date/Time (ISO):</label>
                        <input type="datetime-local" id="start_iso" name="start_iso" required>
                    </div>
                    <div class="form-group">
                        <label for="end_iso">End Date/Time (ISO):</label>
                        <input type="datetime-local" id="end_iso" name="end_iso" required>
                    </div>
                    <div class="form-group">
                        <label for="location">Location:</label>
                        <input type="text" id="location" name="location">
                    </div>
                    <div class="form-group">
                        <label for="attendees_csv">Attendees (comma-separated emails):</label>
                        <input type="text" id="attendees_csv" name="attendees_csv" placeholder="user1@example.com,user2@example.com">
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" name="is_teams_meeting" value="true">
                            Make it a Teams meeting
                        </label>
                    </div>
                    <button type="submit">Create Event</button>
                </form>
                <script>
                    // Set default times
                    const now = new Date();
                    const startTime = new Date(now.getTime() + 60*60*1000); // 1 hour from now
                    const endTime = new Date(now.getTime() + 2*60*60*1000); // 2 hours from now
                    
                    document.getElementById('start_iso').value = startTime.toISOString().slice(0, 16);
                    document.getElementById('end_iso').value = endTime.toISOString().slice(0, 16);
                </script>
            </body>
            </html>
            """
            return HttpResponse(html)
        
        # Handle POST request
        return self.create_group_event(request)
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Check authentication status"""
        token = request.session.get("access_token")
        user = request.session.get("graph_user", {})
        
        # Check configuration
        config_status = {
            "client_id": bool(settings.GRAPH_CLIENT_ID),
            "client_secret": bool(settings.GRAPH_CLIENT_SECRET),
            "tenant": bool(settings.GRAPH_TENANT),
            "group_id": bool(settings.GRAPH_GROUP_ID),
            "authority": bool(settings.GRAPH_AUTHORITY),
            "scopes": bool(settings.GRAPH_SCOPES)
        }
        
        return Response({
            "authenticated": bool(token),
            "user": user,
            "group_id": settings.GRAPH_GROUP_ID,
            "configuration": config_status,
            "configured": all(config_status.values())
        })
    
    @action(detail=False, methods=['post'])
    def test_integration(self, request):
        """Test the complete integration flow with a sample event"""
        # Check authentication
        access_token = request.session.get("access_token")
        if not access_token:
            return Response(
                {"error": "Not authenticated with Microsoft Graph. Please complete the OAuth flow first."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            from datetime import datetime, timedelta
            from .models import UniversityEvent, University, CustomUser
            
            # Create a test university event
            university, _ = University.objects.get_or_create(
                name="Test University for Integration",
                defaults={
                    'website': 'https://testuniversity.edu',
                    'established_year': 2020,
                    'accreditation': 'Test Accreditation'
                }
            )
            
            user, _ = CustomUser.objects.get_or_create(
                username='integration_test_user',
                defaults={
                    'email': 'integration@test.com',
                    'first_name': 'Integration',
                    'last_name': 'Test',
                    'role': 'university_poc'
                }
            )
            
            # Create test event
            start_time = datetime.now() + timedelta(hours=1)
            end_time = start_time + timedelta(hours=2)
            
            event = UniversityEvent.objects.create(
                university=university,
                title="Integration Test Event",
                description="This is a test event for Microsoft Graph integration",
                start_datetime=start_time,
                end_datetime=end_time,
                location="Virtual Test Room",
                created_by=user,
                status='approved',
                invitees="test1@example.com,test2@example.com"
            )
            
            # Trigger Outlook integration
            success = event.trigger_outlook_integration(request)
            
            if success:
                return Response({
                    "message": "Integration test successful!",
                    "event_id": event.id,
                    "outlook_calendar_id": event.outlook_calendar_id,
                    "outlook_calendar_url": event.outlook_calendar_url,
                })
            else:
                return Response(
                    {"error": "Integration test failed. Check logs for details."}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Integration test failed: {str(e)}")
            return Response(
                {"error": f"Integration test failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


