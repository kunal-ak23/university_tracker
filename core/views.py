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

logger = get_logger()

from .models import (
    OEM, Program, University, Stream, Contract, ContractProgram, Batch,
    Billing, Payment, ContractFile, TaxRate, CustomUser, Invoice, ChannelPartner,
    ChannelPartnerProgram, ChannelPartnerStudent, Student, ProgramBatch
)
from .serializers import (
    OEMSerializer, ProgramSerializer, UniversitySerializer, StreamSerializer,
    ContractSerializer, ContractProgramSerializer, BatchSerializer, BillingSerializer,
    PaymentSerializer, ContractFileSerializer, TaxRateSerializer, RegisterSerializer,
    UserSerializer, CustomTokenObtainPairSerializer, InvoiceSerializer, DashboardBillingSerializer,
    DashboardInvoiceSerializer, DashboardPaymentSerializer, ChannelPartnerSerializer,
    ChannelPartnerProgramSerializer, ChannelPartnerStudentSerializer, StudentSerializer,
    ProgramBatchSerializer
)
from .permissions import IsAuthenticatedAndReadOnly

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
    permission_classes = [IsAuthenticatedAndReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']  # default ordering
    search_fields = ['name', 'website', 'contact_email', 'contact_phone', 'address']

class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticatedAndReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ProgramFilter
    ordering_fields = ['name', 'program_code', 'created_at', 'updated_at']
    ordering = ['name']
    search_fields = ['name', 'program_code', 'description', 'prerequisites', 'provider__name']

class UniversityViewSet(viewsets.ModelViewSet):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [IsAuthenticatedAndReadOnly]
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
    permission_classes = [IsAuthenticatedAndReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = StreamFilter
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    search_fields = ['name', 'description', 'university__name']

class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticatedAndReadOnly]
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
    permission_classes = [IsAuthenticatedAndReadOnly]

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
    permission_classes = [IsAuthenticatedAndReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = BatchFilter
    ordering_fields = ['name', 'start_year', 'end_year', 'created_at', 'updated_at']
    ordering = ['-created_at']
    search_fields = ['name', 'notes', 'contract__name', 'stream__name']

class BillingViewSet(viewsets.ModelViewSet):
    queryset = Billing.objects.all()
    serializer_class = BillingSerializer
    permission_classes = [IsAuthenticatedAndReadOnly]
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
    permission_classes = [IsAuthenticatedAndReadOnly]

class ContractFileViewSet(viewsets.ModelViewSet):
    queryset = ContractFile.objects.all()
    serializer_class = ContractFileSerializer
    permission_classes = [IsAuthenticatedAndReadOnly]
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

class TaxRateViewSet(viewsets.ModelViewSet):
    queryset = TaxRate.objects.all()
    serializer_class = TaxRateSerializer
    permission_classes = [IsAuthenticatedAndReadOnly]

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
    permission_classes = [IsAuthenticatedAndReadOnly]
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
    permission_classes = [IsAuthenticatedAndReadOnly]
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
    permission_classes = [IsAuthenticatedAndReadOnly]

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
    permission_classes = [IsAuthenticatedAndReadOnly]
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
    permission_classes = [IsAuthenticatedAndReadOnly]
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
    permission_classes = [IsAuthenticatedAndReadOnly]
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
    permission_classes = [IsAuthenticatedAndReadOnly]
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
    permission_classes = [IsAuthenticatedAndReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ProgramBatchFilter
    ordering_fields = ['name', 'start_date', 'end_date', 'status', 'created_at', 'updated_at']
    ordering = ['-start_date']
    search_fields = ['name', 'notes', 'program__name']