from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import OrderingFilter
from core.logger_service import get_logger
from django.db.models import Q

logger = get_logger()

from .models import (
    OEM, Program, University, Stream, Contract, ContractProgram, Batch,
    Billing, Payment, ContractFile, TaxRate, CustomUser
)
from .serializers import (
    OEMSerializer, ProgramSerializer, UniversitySerializer, StreamSerializer, 
    ContractSerializer, ContractProgramSerializer, BatchSerializer, BillingSerializer, 
    PaymentSerializer, ContractFileSerializer, TaxRateSerializer, RegisterSerializer, 
    UserSerializer, CustomTokenObtainPairSerializer
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
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']  # default ordering

class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticatedAndReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    filterset_class = ProgramFilter
    ordering_fields = ['name', 'program_code', 'created_at', 'updated_at']
    ordering = ['name']

class UniversityViewSet(viewsets.ModelViewSet):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [IsAuthenticatedAndReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['name', 'established_year', 'created_at', 'updated_at']
    ordering = ['name']

class StreamViewSet(viewsets.ModelViewSet):
    queryset = Stream.objects.all()
    serializer_class = StreamSerializer
    permission_classes = [IsAuthenticatedAndReadOnly]

class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticatedAndReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    filterset_class = ContractFilter
    parser_classes = (MultiPartParser, FormParser)
    ordering_fields = ['name', 'status', 'start_date', 'end_date', 'created_at', 'updated_at']
    ordering = ['-created_at']  # newest first

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
                'tax_rate': request.data.get('tax_rate'),
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
            required_fields = ['name', 'university_id', 'oem_id', 'cost_per_student', 'tax_rate']
            missing_fields = [field for field in required_fields if field not in contract_data]
            if missing_fields:
                return Response(
                    {"errors": f"Missing required fields: {', '.join(missing_fields)}"},
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

            # Handle files if present
            files = request.FILES.getlist('files')
            if files:
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
                'tax_rate': request.data.get('tax_rate'),
                'status': request.data.get('status'),
                'notes': request.data.get('notes'),
            }

            # Handle array fields
            programs = request.data.getlist('programs_ids[]') or request.data.getlist('programs[]')
            streams = request.data.getlist('streams_ids[]') or request.data.getlist('streams[]')

            logger.info(f"Programs: {programs}")
            logger.info(f"Streams: {streams}")
            
            if programs:
                contract_data['programs_ids'] = programs
            if streams:
                contract_data['streams_ids'] = streams
            
            # Remove None values
            contract_data = {k: v for k, v in contract_data.items() if v is not None}
            
            logger.info(f"Processed contract data: {contract_data}")

            # Update contract
            contract_serializer = self.get_serializer(instance, data=contract_data, partial=True)
            if not contract_serializer.is_valid():
                logger.error(f"Validation errors: {contract_serializer.errors}")
                return Response(
                    {"errors": contract_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            self.perform_update(contract_serializer)

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

            return Response(contract_serializer.data)

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

class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticatedAndReadOnly]
    pagination_class = StandardResultsSetPagination

class BillingViewSet(viewsets.ModelViewSet):
    queryset = Billing.objects.all()
    serializer_class = BillingSerializer
    permission_classes = [IsAuthenticatedAndReadOnly]

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