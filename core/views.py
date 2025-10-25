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
import requests
import logging

logger = get_logger()

from .models import (
    OEM, Program, University, Stream, Contract, ContractProgram, Batch,
    Billing, Payment, ContractFile, TaxRate, CustomUser, Invoice, ChannelPartner,
    ChannelPartnerProgram, ChannelPartnerStudent, Student, ProgramBatch,
    UniversityEvent, Expense, StaffUniversityAssignment, ContractStreamPricing
)
from .serializers import (
    OEMSerializer, ProgramSerializer, UniversitySerializer, StreamSerializer,
    ContractSerializer, ContractProgramSerializer, BatchSerializer, BillingSerializer,
    PaymentSerializer, ContractFileSerializer, TaxRateSerializer, RegisterSerializer,
    UserSerializer, CustomTokenObtainPairSerializer, InvoiceSerializer, DashboardBillingSerializer,
    DashboardInvoiceSerializer, DashboardPaymentSerializer, ChannelPartnerSerializer,
    ChannelPartnerProgramSerializer, ChannelPartnerStudentSerializer, StudentSerializer,
    ProgramBatchSerializer, UniversityEventSerializer, UniversityEventApprovalSerializer,
    UniversityEventSubmissionSerializer, UniversityEventInviteeSerializer, ExpenseSerializer,
    StaffUniversityAssignmentSerializer, UserManagementSerializer
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

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # If user is university POC, show only their university
        if user.is_university_poc():
            queryset = queryset.filter(poc=user)
        # If user is staff, show only their assigned universities
        elif user.is_staff_user():
            assigned_universities = user.get_assigned_universities()
            queryset = queryset.filter(id__in=assigned_universities)
        # Provider POC and superusers can see all universities
        
        return queryset.select_related('poc')

    def update(self, request, *args, **kwargs):
        """Update university with permission check"""
        instance = self.get_object()
        user = request.user
        
        # Check if user has permission to edit this university
        if user.is_university_poc() and instance.poc != user:
            return Response(
                {"error": "You can only edit your assigned university"},
                status=status.HTTP_403_FORBIDDEN
            )
        elif user.is_staff_user():
            assigned_universities = user.get_assigned_universities()
            if instance.id not in assigned_universities:
                return Response(
                    {"error": "You can only edit universities assigned to you"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete university with permission check"""
        instance = self.get_object()
        user = request.user
        
        # Check if user has permission to delete this university
        if user.is_university_poc() and instance.poc != user:
            return Response(
                {"error": "You can only delete your assigned university"},
                status=status.HTTP_403_FORBIDDEN
            )
        elif user.is_staff_user():
            assigned_universities = user.get_assigned_universities()
            if instance.id not in assigned_universities:
                return Response(
                    {"error": "You can only delete universities assigned to you"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().destroy(request, *args, **kwargs)

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

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # If user is university POC, show only streams for their university
        if user.is_university_poc():
            queryset = queryset.filter(university__poc=user)
        # If user is staff, show only streams for their assigned universities
        elif user.is_staff_user():
            assigned_universities = user.get_assigned_universities()
            queryset = queryset.filter(university__in=assigned_universities)
        # Provider POC and superusers can see all streams
        
        return queryset.select_related('university')

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

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # If user is university POC, show only contracts for their university
        if user.is_university_poc():
            queryset = queryset.filter(university__poc=user)
        # If user is provider POC, show only contracts for their OEMs
        elif user.is_provider_poc():
            queryset = queryset.filter(oem__poc=user)
        # If user is staff, show only contracts for their assigned universities
        elif user.is_staff_user():
            assigned_universities = user.get_assigned_universities()
            queryset = queryset.filter(university__in=assigned_universities)
        # Superusers can see all contracts
        
        return queryset.select_related('university', 'oem').prefetch_related('stream_pricing__stream', 'stream_pricing__tax_rate')

    def create(self, request, *args, **kwargs):
        try:
            logger.info(f"Creating new contract")
            logger.info(f"Request data: {request.data}")
            
            # Handle contract data
            contract_data = {
                'name': request.data.get('name'),
                'university_id': request.data.get('university'),
                'oem_id': request.data.get('oem'),
                'start_year': request.data.get('start_year'),
                'end_year': request.data.get('end_year'),
                'start_date': request.data.get('start_date'),
                'end_date': request.data.get('end_date'),
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
            required_fields = ['name', 'university_id', 'oem_id', 'start_year', 'end_year']
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

            # Handle stream pricing data
            stream_pricing_data = []
            i = 0
            
            # Try different field name patterns for stream pricing
            field_patterns = [
                'stream_pricing[0][stream_id]',
                '1_stream_pricing[0][stream_id]',  # With prefix
            ]
            
            # Find which pattern works
            field_pattern = None
            for pattern in field_patterns:
                if pattern in request.data:
                    field_pattern = pattern
                    break
            
            print(f"🔧 Backend: Field pattern detection - checking patterns: {field_patterns}")
            print(f"🔧 Backend: Available keys in request.data: {list(request.data.keys())}")
            print(f"🔧 Backend: Selected field pattern: {field_pattern}")
            
            if field_pattern:
                # Extract the base pattern for other fields
                # Remove [0][stream_id] to get just 'stream_pricing'
                base_pattern = field_pattern.replace('[0][stream_id]', '')
                print(f"🔧 Backend: Base pattern extracted: {base_pattern}")
                
                while f'{base_pattern}[{i}][stream_id]' in request.data:
                    print(f"🔧 Backend: Found pricing entry {i} with pattern: {base_pattern}[{i}][stream_id]")
                    # Get program_id from the pricing data, or fall back to the first program in the contract
                    program_id = request.data.get(f'{base_pattern}[{i}][program_id]')
                    if not program_id:
                        # If no program_id in pricing data, use the first program from the contract
                        programs = request.data.getlist('programs_ids[]') or request.data.getlist('programs[]')
                        if programs:
                            program_id = programs[0]  # Use the first program
                    
                    pricing_data = {
                        'contract': serializer.instance,
                        'program_id': program_id,
                        'stream_id': request.data.get(f'{base_pattern}[{i}][stream_id]'),
                        'year': request.data.get(f'{base_pattern}[{i}][year]'),
                        'cost_per_student': request.data.get(f'{base_pattern}[{i}][cost_per_student]'),
                        'oem_transfer_price': request.data.get(f'{base_pattern}[{i}][oem_transfer_price]'),
                        'tax_rate_id': request.data.get(f'{base_pattern}[{i}][tax_rate_id]'),
                    }
                    stream_pricing_data.append(pricing_data)
                    i += 1
                    
                    # Safety check to prevent infinite loops
                    if i > 1000:
                        break

            # Create stream pricing entries
            print(f"🔧 Backend: Processing {len(stream_pricing_data)} stream pricing entries")
            
            # Safety limit to prevent infinite loops
            if len(stream_pricing_data) > 100:
                print(f"🔧 ❌ Too many stream pricing entries ({len(stream_pricing_data)}), limiting to 100")
                stream_pricing_data = stream_pricing_data[:100]
            
            created_count = 0
            skipped_count = 0
            
            for i, pricing_data in enumerate(stream_pricing_data):
                print(f"🔧 Backend: Processing pricing entry {i}: {pricing_data}")
                
                # Check if any required field is empty - if so, skip the entire entry
                cost_per_student = pricing_data['cost_per_student']
                oem_transfer_price = pricing_data['oem_transfer_price']
                tax_rate_id = pricing_data['tax_rate_id']
                program_id = pricing_data['program_id']
                
                # Skip entry if any required field is empty or null
                if (not cost_per_student or cost_per_student == '' or cost_per_student == '0' or
                    not oem_transfer_price or oem_transfer_price == '' or oem_transfer_price == '0' or
                    not tax_rate_id or tax_rate_id == '' or tax_rate_id == '0' or
                    not program_id or program_id == '' or program_id == '0'):
                    print(f"🔧 Backend: Skipping entry {i} - missing required fields")
                    skipped_count += 1
                    continue
                
                try:
                    pricing_obj, created = ContractStreamPricing.objects.get_or_create(
                        contract=pricing_data['contract'],
                        program_id=program_id,
                        stream_id=pricing_data['stream_id'],
                        year=pricing_data['year'],
                        defaults={
                            'cost_per_student': cost_per_student,
                            'oem_transfer_price': oem_transfer_price,
                            'tax_rate_id': tax_rate_id,
                        }
                    )
                    if created:
                        print(f"🔧 Backend: ✅ Created pricing entry {i}: {pricing_obj}")
                        created_count += 1
                    else:
                        print(f"🔧 Backend: ⚠️ Pricing entry {i} already exists: {pricing_obj}")
                except Exception as e:
                    print(f"🔧 Backend: ❌ Error creating pricing entry {i}: {e}")
            
            print(f"🔧 Backend: Summary - Created: {created_count}, Skipped: {skipped_count}")

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

            # Log final contract data
            print(f"🔧 Backend: Contract created with ID: {serializer.instance.id}")
            print(f"🔧 Backend: Contract name: {serializer.instance.name}")
            print(f"🔧 Backend: Contract programs: {list(serializer.instance.programs.values_list('id', flat=True))}")
            
            # Get streams from stream_pricing relationship
            streams_from_pricing = list(serializer.instance.stream_pricing.values_list('stream_id', flat=True).distinct())
            print(f"🔧 Backend: Contract streams (from pricing): {streams_from_pricing}")
            
            # Check stream pricing in database
            pricing_count = ContractStreamPricing.objects.filter(contract=serializer.instance).count()
            print(f"🔧 Backend: Stream pricing entries in DB: {pricing_count}")
            
            if pricing_count > 0:
                pricing_entries = ContractStreamPricing.objects.filter(contract=serializer.instance)
                for entry in pricing_entries:
                    print(f"🔧 Backend: DB Entry - Program: {entry.program_id}, Stream: {entry.stream_id}, Year: {entry.year}, Cost: {entry.cost_per_student}")

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
            print(f"🔧 CONTRACT UPDATE CALLED - Contract ID: {instance.id}")
            
            logger.info(f"Updating contract {instance.id}")
            
            # Handle contract data
            contract_data = {
                'name': request.data.get('name'),
                'university_id': request.data.get('university'),
                'oem_id': request.data.get('oem'),
                'start_year': request.data.get('start_year'),
                'end_year': request.data.get('end_year'),
                'start_date': request.data.get('start_date'),
                'end_date': request.data.get('end_date'),
                'status': request.data.get('status'),
                'notes': request.data.get('notes'),
            }
            
            print(f"🔧 Contract data extracted: {contract_data}")

            # Handle array fields
            programs = request.data.getlist('programs_ids[]') or request.data.getlist('programs[]')
            streams = request.data.getlist('streams_ids[]') or request.data.getlist('streams[]')
            
            print(f"🔧 Programs found: {programs}")
            print(f"🔧 Streams found: {streams}")
            
            if programs:
                contract_data['programs_ids'] = programs
            if streams:
                contract_data['streams_ids'] = streams
            
            # Remove None values
            contract_data = {k: v for k, v in contract_data.items() if v is not None}
            
            print(f"🔧 Final contract data: {contract_data}")
            logger.info(f"Processed contract data: {contract_data}")

            # Update contract
            print(f"🔧 Updating contract with serializer...")
            serializer = self.get_serializer(instance, data=contract_data, partial=True)
            if not serializer.is_valid():
                print(f"🔧 ❌ Serializer validation failed: {serializer.errors}")
                logger.error(f"Validation errors: {serializer.errors}")
                return Response(
                    {"errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            print(f"🔧 ✅ Serializer validation passed, performing update...")
            self.perform_update(serializer)
            print(f"🔧 ✅ Contract update completed")

            # Handle stream pricing data - replace all existing pricing with new data
            print(f"🔧 Processing stream pricing data...")
            # First, get all existing stream pricing entries for this contract
            existing_pricing = ContractStreamPricing.objects.filter(contract=instance)
            existing_pricing_ids = set(existing_pricing.values_list('id', flat=True))
            print(f"🔧 Found {len(existing_pricing_ids)} existing pricing entries: {existing_pricing_ids}")
            
            # Collect new pricing data
            new_pricing_ids = set()
            stream_pricing_data = []
            i = 0
            
            # Try different field name patterns for stream pricing
            field_patterns = [
                'stream_pricing[0][stream_id]',
                '1_stream_pricing[0][stream_id]',  # With prefix
                f'{instance.id}_stream_pricing[0][stream_id]'  # With contract ID prefix
            ]
            
            print(f"🔧 Trying field patterns: {field_patterns}")
            print(f"🔧 Available keys in request.data: {list(request.data.keys())}")
            logger.info(f"Trying field patterns: {field_patterns}")
            
            # Find which pattern works
            field_pattern = None
            for pattern in field_patterns:
                if pattern in request.data:
                    field_pattern = pattern
                    break
            
            print(f"🔧 Update: Selected field pattern: {field_pattern}")
            
            if field_pattern:
                # Extract the base pattern for other fields
                # Remove [0][stream_id] to get just the base pattern
                base_pattern = field_pattern.replace('[0][stream_id]', '')
                print(f"🔧 Update: Base pattern extracted: {base_pattern}")
                
                while f'{base_pattern}[{i}][stream_id]' in request.data:
                    print(f"🔧 Update: Found pricing entry {i} with pattern: {base_pattern}[{i}][stream_id]")
                    # Get program_id from the pricing data, or fall back to the first program in the contract
                    program_id = request.data.get(f'{base_pattern}[{i}][program_id]')
                    if not program_id:
                        # If no program_id in pricing data, use the first program from the contract
                        programs = request.data.getlist('programs_ids[]') or request.data.getlist('programs[]')
                        if programs:
                            program_id = programs[0]  # Use the first program
                    
                    year_value = request.data.get(f'{base_pattern}[{i}][year]')
                    cost_per_student = request.data.get(f'{base_pattern}[{i}][cost_per_student]')
                    oem_transfer_price = request.data.get(f'{base_pattern}[{i}][oem_transfer_price]')
                    
                    pricing_data = {
                        'contract': instance,
                        'program_id': program_id,
                        'stream_id': request.data.get(f'{base_pattern}[{i}][stream_id]'),
                        'year': year_value,
                        'cost_per_student': cost_per_student,
                        'oem_transfer_price': oem_transfer_price,
                        'tax_rate_id': request.data.get(f'{base_pattern}[{i}][tax_rate_id]'),
                    }
                    stream_pricing_data.append(pricing_data)
                    print(f"🔧 Added pricing data for index {i}: {pricing_data}")
                    i += 1
                    
                    # Safety check to prevent infinite loops
                    if i > 1000:
                        print(f"🔧 ❌ Breaking loop at index {i} to prevent infinite loop")
                        break
                
                print(f"🔧 Total stream pricing entries found: {len(stream_pricing_data)}")
            else:
                print(f"🔧 ❌ No field pattern matched for stream pricing data")
            
            # Safety limit to prevent infinite loops
            if len(stream_pricing_data) > 100:
                print(f"🔧 ❌ Too many stream pricing entries ({len(stream_pricing_data)}), limiting to 100")
                stream_pricing_data = stream_pricing_data[:100]
            
            for pricing_data in stream_pricing_data:
                # Check if any required field is empty - if so, skip the entire entry
                cost_per_student = pricing_data['cost_per_student']
                oem_transfer_price = pricing_data['oem_transfer_price']
                tax_rate_id = pricing_data['tax_rate_id']
                program_id = pricing_data['program_id']
                
                # Skip entry if any required field is empty or null
                if (not cost_per_student or cost_per_student == '' or cost_per_student == '0' or
                    not oem_transfer_price or oem_transfer_price == '' or oem_transfer_price == '0' or
                    not tax_rate_id or tax_rate_id == '' or tax_rate_id == '0' or
                    not program_id or program_id == '' or program_id == '0'):
                    continue
                
                pricing_obj, created = ContractStreamPricing.objects.update_or_create(
                    contract=instance,
                    program_id=pricing_data['program_id'],
                    stream_id=pricing_data['stream_id'],
                    year=pricing_data['year'],
                    defaults={
                        'cost_per_student': cost_per_student,
                        'oem_transfer_price': oem_transfer_price,
                        'tax_rate_id': tax_rate_id,
                    }
                )
                new_pricing_ids.add(pricing_obj.id)
            
            # Remove stream pricing entries that are no longer in the request
            pricing_to_remove = existing_pricing_ids - new_pricing_ids
            if pricing_to_remove:
                ContractStreamPricing.objects.filter(id__in=pricing_to_remove).delete()

            # Handle files if present
            files = request.FILES.getlist('files')
            if files:
                for file in files:
                    ContractFile.objects.create(
                        contract=instance,
                        file=file,
                        file_type='document',
                        description=file.name,
                        uploaded_by=request.user
                    )

            print(f"🔧 ✅ Contract update completed successfully!")
            return Response(serializer.data)

        except Exception as e:
            print(f"🔧 ❌ Contract update error: {str(e)}")
            logger.error(f"Contract update error: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def pricing(self, request):
        """Get pricing for a specific university, stream, and year"""
        university_id = request.query_params.get('university')
        program_id = request.query_params.get('program')
        stream_id = request.query_params.get('stream')
        year = request.query_params.get('year')
        
        if not all([university_id, program_id, stream_id, year]):
            return Response(
                {"error": "university, program, stream, and year parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Find the contract with matching stream pricing
            contract = Contract.objects.get(
                university_id=university_id,
                stream_pricing__program_id=program_id,
                stream_pricing__stream_id=stream_id,
                stream_pricing__year=year,
                start_year__lte=year,
                end_year__gte=year
            )
            
            # Get the specific pricing
            pricing = contract.get_stream_pricing(program_id, stream_id, int(year))
            if pricing:
                return Response({
                    'cost_per_student': str(pricing.cost_per_student),
                    'oem_transfer_price': str(pricing.oem_transfer_price),
                    'tax_rate': str(pricing.tax_rate.rate) if pricing.tax_rate else "0.00"
                })
            else:
                return Response({
                    'cost_per_student': "0.00",
                    'oem_transfer_price': "0.00",
                    'tax_rate': "0.00"
                })
                
        except Contract.DoesNotExist:
            return Response({
                'cost_per_student': "0.00",
                'oem_transfer_price': "0.00",
                'tax_rate': "0.00"
            })
        except Exception as e:
            logger.error(f"Error fetching pricing: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ContractProgramViewSet(viewsets.ModelViewSet):
    queryset = ContractProgram.objects.all()
    serializer_class = ContractProgramSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]

class BatchFilter(filters.FilterSet):
    stream = filters.NumberFilter(field_name='stream__id')
    university = filters.NumberFilter(field_name='university__id')
    status = filters.CharFilter(field_name='status')
    
    class Meta:
        model = Batch
        fields = ['stream', 'university', 'status']

class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = BatchFilter
    ordering_fields = ['name', 'start_year', 'end_year', 'created_at', 'updated_at']
    ordering = ['-created_at']
    search_fields = ['name', 'notes', 'university__name', 'stream__name']

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # If user is university POC, show only batches for their university
        if user.is_university_poc():
            queryset = queryset.filter(university__poc=user)
        # If user is provider POC, show only batches for their OEMs
        elif user.is_provider_poc():
            # Get contracts for this OEM and filter batches by university
            oem_contracts = Contract.objects.filter(oem__poc=user)
            university_ids = oem_contracts.values_list('university_id', flat=True)
            queryset = queryset.filter(university_id__in=university_ids)
        # If user is staff, show only batches for their assigned universities
        elif user.is_staff_user():
            assigned_universities = user.get_assigned_universities()
            queryset = queryset.filter(university__in=assigned_universities)
        # Superusers can see all batches
        
        return queryset.select_related('university', 'stream').prefetch_related('snapshots')

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

    @action(detail=False, methods=['post'])
    def create_university_year_billing(self, request):
        """Create a billing for a university for a given year with all operational batches"""
        university_id = request.data.get('university_id')
        year = request.data.get('year')
        billing_name = request.data.get('name', f'Billing for {year}')
        notes = request.data.get('notes', '')
        
        if not university_id or not year:
            return Response(
                {"error": "university_id and year are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get the university
            university = University.objects.get(id=university_id)
            
            # Find all operational batches for this university and year
            operational_batches = Batch.objects.filter(
                university=university,
                start_year__lte=year,
                end_year__gte=year,
                status='ongoing'
            ).select_related('stream')
            
            if not operational_batches.exists():
                return Response(
                    {"error": f"No operational batches found for {university.name} in {year}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the billing
            billing = Billing.objects.create(
                name=billing_name,
                notes=notes,
                status='draft'
            )
            
            # Add all operational batches to the billing
            billing.batches.set(operational_batches)
            
            # Calculate totals
            billing.update_totals()
            
            # Return billing data with batch details
            serializer = self.get_serializer(billing)
            batch_data = []
            for batch in operational_batches:
                batch_data.append({
                    'id': batch.id,
                    'name': batch.name,
                    'stream': batch.stream.name,
                    'number_of_students': batch.number_of_students,
                    'start_year': batch.start_year,
                    'end_year': batch.end_year,
                    'cost_per_student': str(batch.get_cost_per_student()),
                    'oem_transfer_price': str(batch.get_oem_transfer_price()),
                    'tax_rate': str(batch.get_tax_rate().rate) if batch.get_tax_rate() else "0.00"
                })
            
            response_data = {
                **serializer.data,
                'batches': batch_data,
                'university': {
                    'id': university.id,
                    'name': university.name
                },
                'year': year,
                'redirect': {
                    'id': billing.id,
                    'path': f'/billings/{billing.id}/edit'
                }
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except University.DoesNotExist:
            return Response(
                {"error": "University not found"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creating university year billing: {str(e)}")
            return Response(
                {"error": str(e)},
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
            logger.info(f"Login attempt for: {request.data.get('username', request.data.get('email'))}")
            
            # First try to authenticate with the provided credentials
            response = super().post(request, *args, **kwargs)
            
            logger.info(f"Authentication response status: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"Authentication failed: {response.data}")
            
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
                    user_data = {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'username': user.username,
                        'role': user.role,
                        'is_superuser': user.is_superuser,
                        'is_staff': user.is_staff,
                        'is_active': user.is_active,
                        'date_joined': user.date_joined,
                        'last_login': user.last_login,
                    }
                    
                    response.data.update({
                        'role': role,
                        'user': user_data
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
    def quarterly_expenses(self, request):
        """Return quarterly expenses aggregated by university and optionally batch"""
        year = int(request.query_params.get('year', datetime.now().year))
        university_id = request.query_params.get('university')
        batch_id = request.query_params.get('batch')

        expenses = Expense.objects.filter(incurred_date__year=year)
        if university_id:
            expenses = expenses.filter(university_id=university_id)
        if batch_id:
            expenses = expenses.filter(batch_id=batch_id)

        data = {1: Decimal('0'), 2: Decimal('0'), 3: Decimal('0'), 4: Decimal('0')}
        for exp in expenses.values('incurred_date', 'amount'):
            month = exp['incurred_date'].month
            quarter = (month - 1) // 3 + 1
            data[quarter] += Decimal(str(exp['amount']))

        return Response({
            'year': year,
            'quarters': [
                {'name': f'Q{q}', 'total': float(total)} for q, total in data.items()
            ]
        })

    @action(detail=False, methods=['get'])
    def profitability(self, request):
        """Return quarterly profitability: revenue - expenses at university or batch level"""
        year = int(request.query_params.get('year', datetime.now().year))
        university_id = request.query_params.get('university')
        batch_id = request.query_params.get('batch')

        payments = Payment.objects.filter(status='completed', payment_date__year=year)
        if batch_id:
            payments = payments.filter(invoice__billing__batches__id=batch_id)
        elif university_id:
            payments = payments.filter(invoice__billing__batches__contract__university_id=university_id)

        revenue_by_quarter = {1: Decimal('0'), 2: Decimal('0'), 3: Decimal('0'), 4: Decimal('0')}
        for p in payments.values('payment_date', 'amount'):
            month = p['payment_date'].month
            quarter = (month - 1) // 3 + 1
            revenue_by_quarter[quarter] += Decimal(str(p['amount']))

        expenses = Expense.objects.filter(incurred_date__year=year)
        if batch_id:
            expenses = expenses.filter(batch_id=batch_id)
        elif university_id:
            expenses = expenses.filter(university_id=university_id)

        expense_by_quarter = {1: Decimal('0'), 2: Decimal('0'), 3: Decimal('0'), 4: Decimal('0')}
        for e in expenses.values('incurred_date', 'amount'):
            month = e['incurred_date'].month
            quarter = (month - 1) // 3 + 1
            expense_by_quarter[quarter] += Decimal(str(e['amount']))

        result = []
        for q in [1,2,3,4]:
            revenue = revenue_by_quarter[q]
            expense = expense_by_quarter[q]
            profit = revenue - expense
            result.append({
                'name': f'Q{q}',
                'revenue': float(revenue),
                'expenses': float(expense),
                'profit': float(profit)
            })

        return Response({
            'year': year,
            'quarters': result
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
            # Get contracts for this OEM and filter events by university
            oem_contracts = Contract.objects.filter(oem__poc=user)
            university_ids = oem_contracts.values_list('university_id', flat=True)
            queryset = queryset.filter(university_id__in=university_ids)
        # If user is staff, show events for their assigned universities
        elif user.is_staff_user():
            assigned_universities = user.get_assigned_universities()
            queryset = queryset.filter(university__in=assigned_universities)
        # Superusers can see all events
        
        return queryset.select_related(
            'university', 'batch', 'created_by', 'approved_by'
        )

    def list(self, request, *args, **kwargs):
        """Override list method to add debugging"""
        # Call parent list method
        response = super().list(request, *args, **kwargs)
        return response

    def update(self, request, *args, **kwargs):
        """Update event with permission check"""
        instance = self.get_object()
        user = request.user
        
        # Check if user has permission to edit this event
        if user.is_university_poc() and instance.university.poc != user:
            return Response(
                {"error": "You can only edit events for your assigned university"},
                status=status.HTTP_403_FORBIDDEN
            )
        elif user.is_staff_user():
            assigned_universities = user.get_assigned_universities()
            if instance.university.id not in assigned_universities:
                return Response(
                    {"error": "You can only edit events for universities assigned to you"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete event with permission check"""
        instance = self.get_object()
        user = request.user
        
        # Check if user has permission to delete this event
        if user.is_university_poc() and instance.university.poc != user:
            return Response(
                {"error": "You can only delete events for your assigned university"},
                status=status.HTTP_403_FORBIDDEN
            )
        elif user.is_staff_user():
            assigned_universities = user.get_assigned_universities()
            if instance.university.id not in assigned_universities:
                return Response(
                    {"error": "You can only delete events for universities assigned to you"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().destroy(request, *args, **kwargs)

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
            'email_sent_count': event.email_sent_count,
            'email_sent_at': event.email_sent_at,
            'notion_page_id': event.notion_page_id,
            'notion_page_url': event.notion_page_url,
            'integration_notes': event.integration_notes
        }, status=status.HTTP_200_OK)


class ExpenseFilter(filters.FilterSet):
    university = filters.NumberFilter(field_name='university__id')
    batch = filters.NumberFilter(field_name='batch__id')
    event = filters.NumberFilter(field_name='event__id')
    category = filters.CharFilter(field_name='category')
    start_date = filters.DateFilter(field_name='incurred_date', lookup_expr='gte')
    end_date = filters.DateFilter(field_name='incurred_date', lookup_expr='lte')

    class Meta:
        model = Expense
        fields = ['university', 'batch', 'event', 'category', 'start_date', 'end_date']


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticatedWithRoleBasedAccess]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ExpenseFilter
    ordering_fields = ['incurred_date', 'amount', 'category', 'created_at']
    ordering = ['-incurred_date']
    search_fields = ['description', 'notes', 'event__title', 'batch__name', 'university__name']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_university_poc():
            queryset = queryset.filter(university__poc=user)
        elif user.is_provider_poc():
            queryset = queryset.filter(batch__contract__oem__poc=user)
        elif user.is_staff_user():
            assigned_universities = user.get_assigned_universities()
            queryset = queryset.filter(university__in=assigned_universities)
        return queryset.select_related('university', 'batch', 'event')

    def update(self, request, *args, **kwargs):
        """Update expense with permission check"""
        instance = self.get_object()
        user = request.user
        
        # Check if user has permission to edit this expense
        if user.is_university_poc() and instance.university.poc != user:
            return Response(
                {"error": "You can only edit expenses for your assigned university"},
                status=status.HTTP_403_FORBIDDEN
            )
        elif user.is_staff_user():
            assigned_universities = user.get_assigned_universities()
            if instance.university.id not in assigned_universities:
                return Response(
                    {"error": "You can only edit expenses for universities assigned to you"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete expense with permission check"""
        instance = self.get_object()
        user = request.user
        
        # Check if user has permission to delete this expense
        if user.is_university_poc() and instance.university.poc != user:
            return Response(
                {"error": "You can only delete expenses for your assigned university"},
                status=status.HTTP_403_FORBIDDEN
            )
        elif user.is_staff_user():
            assigned_universities = user.get_assigned_universities()
            if instance.university.id not in assigned_universities:
                return Response(
                    {"error": "You can only delete expenses for universities assigned to you"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().destroy(request, *args, **kwargs)


class StaffUniversityAssignmentFilter(filters.FilterSet):
    staff = filters.NumberFilter(field_name='staff__id')
    university = filters.NumberFilter(field_name='university__id')
    
    class Meta:
        model = StaffUniversityAssignment
        fields = ['staff', 'university']


class StaffUniversityAssignmentViewSet(viewsets.ModelViewSet):
    queryset = StaffUniversityAssignment.objects.all()
    serializer_class = StaffUniversityAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = StaffUniversityAssignmentFilter
    ordering_fields = ['assigned_at', 'staff__username', 'university__name']
    ordering = ['-assigned_at']
    search_fields = ['staff__username', 'staff__email', 'university__name']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Only superusers can manage staff assignments
        if not user.is_superuser:
            return StaffUniversityAssignment.objects.none()
        
        return queryset.select_related('staff', 'university', 'assigned_by')


class UserManagementFilter(filters.FilterSet):
    role = filters.CharFilter(field_name='role')
    is_active = filters.BooleanFilter(field_name='is_active')
    is_superuser = filters.BooleanFilter(field_name='is_superuser')
    
    class Meta:
        model = CustomUser
        fields = ['role', 'is_active', 'is_superuser']


class UserManagementViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserManagementSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = UserManagementFilter
    ordering_fields = ['username', 'email', 'date_joined', 'last_login']
    ordering = ['-date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Only superusers can manage users
        if not user.is_superuser:
            return CustomUser.objects.none()
        
        return queryset.prefetch_related('staff_assignments__university')

    def create(self, request, *args, **kwargs):
        """Create a new user"""
        if not request.user.is_superuser:
            return Response(
                {"error": "Only superusers can create users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create user with password
        password = request.data.get('password')
        if not password:
            return Response(
                {"error": "Password is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = CustomUser.objects.create_user(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            password=password,
            first_name=serializer.validated_data.get('first_name', ''),
            last_name=serializer.validated_data.get('last_name', ''),
            role=serializer.validated_data.get('role'),
            phone_number=serializer.validated_data.get('phone_number', ''),
            address=serializer.validated_data.get('address', ''),
            date_of_birth=serializer.validated_data.get('date_of_birth'),
            is_active=serializer.validated_data.get('is_active', True),
            is_superuser=serializer.validated_data.get('is_superuser', False)
        )
        
        return Response(UserManagementSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def assign_universities(self, request, pk=None):
        """Assign universities to a staff user"""
        if not request.user.is_superuser:
            return Response(
                {"error": "Only superusers can assign universities"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        if not user.is_staff_user():
            return Response(
                {"error": "Only staff users can be assigned to universities"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        university_ids = request.data.get('university_ids', [])
        if not university_ids:
            return Response(
                {"error": "university_ids is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Clear existing assignments
        StaffUniversityAssignment.objects.filter(staff=user).delete()
        
        # Create new assignments
        assignments = []
        for university_id in university_ids:
            try:
                university = University.objects.get(id=university_id)
                assignment = StaffUniversityAssignment.objects.create(
                    staff=user,
                    university=university,
                    assigned_by=request.user
                )
                assignments.append(assignment)
            except University.DoesNotExist:
                return Response(
                    {"error": f"University with id {university_id} not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response({
            "message": f"Successfully assigned {len(assignments)} universities to {user.username}",
            "assignments": StaffUniversityAssignmentSerializer(assignments, many=True).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def assigned_universities(self, request, pk=None):
        """Get universities assigned to a staff user"""
        user = self.get_object()
        if not user.is_staff_user():
            return Response({"universities": []})
        
        assignments = StaffUniversityAssignment.objects.filter(staff=user)
        return Response(StaffUniversityAssignmentSerializer(assignments, many=True).data)


