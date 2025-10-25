from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from core.logger_service import get_logger
from django.db import models
from datetime import date

logger = get_logger()

from .models import (
    OEM, Program, CustomUser, University, Contract, ContractProgram, ContractStreamPricing, Batch,
    Billing, Payment, ContractFile, Stream, TaxRate, BatchSnapshot, Invoice,
    PaymentSchedule, PaymentReminder, PaymentDocument, PaymentScheduleRecipient,
    ChannelPartner, ChannelPartnerProgram, ChannelPartnerStudent, Student, ProgramBatch,
    UniversityEvent, Expense, StaffUniversityAssignment
)

# Base serializers for models without dependencies
class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = '__all__'

class OEMSerializer(serializers.ModelSerializer):
    class Meta:
        model = OEM
        fields = '__all__'

class StreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stream
        fields = '__all__'

class TaxRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxRate
        fields = '__all__'

# Serializers that depend on base models
class ProgramSerializer(serializers.ModelSerializer):
    provider = OEMSerializer(read_only=True)
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=OEM.objects.all(),
        write_only=True,
        source='provider'
    )

    class Meta:
        model = Program
        fields = ['id', 'name', 'program_code', 'provider', 'provider_id', 'duration', 'duration_unit', 'description', 'prerequisites']

class ContractFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractFile
        fields = ['id', 'contract', 'file_type', 'file', 'description', 'uploaded_by']
        read_only_fields = ['uploaded_by']

    def validate(self, data):
        # Log the incoming data for debugging
        print("Validating data:", data)
        
        # Check if required fields are present
        if 'file' not in data:
            raise serializers.ValidationError({"file": "This field is required."})
        if 'contract' not in data:
            raise serializers.ValidationError({"contract": "This field is required."})
        
        return data

class ContractProgramSerializer(serializers.ModelSerializer):
    program = ProgramSerializer()

    class Meta:
        model = ContractProgram
        fields = '__all__'

class ContractStreamPricingSerializer(serializers.ModelSerializer):
    program = ProgramSerializer(read_only=True)
    program_id = serializers.PrimaryKeyRelatedField(queryset=Program.objects.all(), source='program', write_only=True)
    stream = StreamSerializer(read_only=True)
    stream_id = serializers.PrimaryKeyRelatedField(queryset=Stream.objects.all(), source='stream', write_only=True)
    tax_rate = TaxRateSerializer(read_only=True)
    tax_rate_id = serializers.PrimaryKeyRelatedField(queryset=TaxRate.objects.all(), source='tax_rate', write_only=True)

    class Meta:
        model = ContractStreamPricing
        fields = [
            'id', 'program', 'program_id', 'stream', 'stream_id', 'year', 'cost_per_student', 
            'oem_transfer_price', 'tax_rate', 'tax_rate_id', 'created_at', 'updated_at'
        ]

class ContractSerializer(serializers.ModelSerializer):
    contract_programs = ContractProgramSerializer(many=True, read_only=True)
    contract_files = ContractFileSerializer(many=True, read_only=True)
    stream_pricing = ContractStreamPricingSerializer(many=True, read_only=True)
    streams = serializers.SerializerMethodField()
    oem = OEMSerializer(read_only=True)
    university = UniversitySerializer(read_only=True)
    programs = ProgramSerializer(many=True, read_only=True)
    oem_id = serializers.PrimaryKeyRelatedField(queryset=OEM.objects.all(), source='oem', write_only=True)
    university_id = serializers.PrimaryKeyRelatedField(queryset=University.objects.all(), source='university', write_only=True)
    programs_ids = serializers.PrimaryKeyRelatedField(many=True, queryset=Program.objects.all(), write_only=True, source='programs')
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def get_streams(self, obj):
        """Get unique streams from stream_pricing"""
        streams = obj.stream_pricing.values('stream_id', 'stream__name', 'stream__duration', 'stream__duration_unit', 'stream__description').distinct()
        return [{
            'id': stream['stream_id'],
            'name': stream['stream__name'],
            'duration': stream['stream__duration'],
            'duration_unit': stream['stream__duration_unit'],
            'description': stream['stream__description']
        } for stream in streams]

    class Meta:
        model = Contract
        fields = [
            'id', 'name', 'start_year', 'end_year', 'start_date', 'end_date', 
            'status', 'notes', 'contract_programs', 'contract_files', 
            'stream_pricing', 'streams', 'oem', 'university', 'programs', 
            'oem_id', 'university_id', 'programs_ids', 'created_at', 'updated_at'
        ]

class BatchSnapshotSerializer(serializers.ModelSerializer):
    batch_name = serializers.CharField(source='batch.name', read_only=True)
    batch_stream = serializers.SerializerMethodField()
    batch_university = serializers.SerializerMethodField()
    billing_name = serializers.SerializerMethodField()

    def get_batch_stream(self, obj):
        """Get the stream name safely, handling null values"""
        if obj.batch.stream:
            return obj.batch.stream.name
        return "No Stream"

    def get_batch_university(self, obj):
        """Get the university name safely, handling null values"""
        if obj.batch.university:
            return obj.batch.university.name
        return "No University"

    def get_billing_name(self, obj):
        """Get the billing name safely, handling null values"""
        if obj.billing:
            return obj.billing.name
        return "No Billing"

    class Meta:
        model = BatchSnapshot
        fields = [
            'id', 'batch', 'batch_name', 'batch_stream', 'batch_university',
            'billing_name', 'number_of_students', 'cost_per_student', 'tax_rate', 
            'oem_transfer_price', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class BatchSerializer(serializers.ModelSerializer):
    university = serializers.SerializerMethodField()
    university_id = serializers.PrimaryKeyRelatedField(queryset=University.objects.all(), source='university', write_only=True)
    stream = serializers.SerializerMethodField()
    stream_id = serializers.PrimaryKeyRelatedField(queryset=Stream.objects.all(), source='stream', write_only=True)
    effective_cost_per_student = serializers.SerializerMethodField()
    effective_tax_rate = serializers.SerializerMethodField()
    effective_oem_transfer_price = serializers.SerializerMethodField()
    snapshots = BatchSnapshotSerializer(many=True, read_only=True)

    def get_university(self, obj):
        """Get the university data safely, handling None values"""
        if obj.university:
            return UniversitySerializer(obj.university).data
        return None

    def get_stream(self, obj):
        """Get the stream data safely, handling None values"""
        if obj.stream:
            return StreamSerializer(obj.stream).data
        return None

    def get_effective_cost_per_student(self, obj):
        """Get the effective cost per student, handling None values"""
        cost = obj.get_cost_per_student()
        return cost if cost is not None else 0.00

    def get_effective_tax_rate(self, obj):
        """Get the effective tax rate, handling None values"""
        tax_rate_obj = obj.get_tax_rate()
        return tax_rate_obj.rate if tax_rate_obj else 0.00

    def get_effective_oem_transfer_price(self, obj):
        """Get the effective OEM transfer price, handling None values"""
        price = obj.get_oem_transfer_price()
        return price if price is not None else 0.00

    class Meta:
        model = Batch
        fields = [
            'id', 'name', 'university', 'university_id', 'stream', 'stream_id', 
            'number_of_students', 'start_year', 'end_year', 'start_date', 'end_date',
            'effective_cost_per_student', 'effective_tax_rate', 'effective_oem_transfer_price',
            'status', 'notes', 'snapshots', 'created_at', 'updated_at'
        ]


class PaymentDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentDocument
        fields = ['id', 'payment', 'file', 'description', 'uploaded_by', 'created_at', 'updated_at']
        read_only_fields = ['uploaded_by', 'created_at', 'updated_at']

class PaymentSerializer(serializers.ModelSerializer):
    documents = PaymentDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'name', 'invoice', 'amount', 'payment_date',
            'payment_method', 'status', 'transaction_reference',
            'notes', 'documents', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        if data['amount'] <= 0:
            raise serializers.ValidationError("Payment amount must be greater than zero")
        
        # Validate payment amount against remaining invoice amount
        invoice = data['invoice']
        remaining_amount = invoice.amount - invoice.amount_paid
        if data['amount'] > remaining_amount:
            raise serializers.ValidationError(
                f"Payment amount ({data['amount']}) exceeds remaining invoice amount ({remaining_amount})"
            )
        return data

class InvoiceSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remaining_amount = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'name', 'billing', 'issue_date', 'due_date', 'amount',
            'amount_paid', 'remaining_amount', 'status', 'notes',
            'proforma_invoice', 'actual_invoice', 'payments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'amount_paid', 'created_at', 'updated_at']

    def get_remaining_amount(self, obj):
        return obj.amount - obj.amount_paid

class BillingSerializer(serializers.ModelSerializer):
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_payments = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_oem_transfer_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    batch_snapshots = BatchSnapshotSerializer(many=True, read_only=True)

    class Meta:
        model = Billing
        fields = [
            'id', 'name', 'batches', 'batch_snapshots', 'notes', 'status',
            'total_amount', 'total_payments', 'balance_due',
            'total_oem_transfer_amount', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'status']

    def create(self, validated_data):
        """Create billing with proper handling of 0 values"""
        try:
            billing = super().create(validated_data)
            return billing
        except Exception as e:
            logger.error(f"Error creating billing: {str(e)}")
            raise serializers.ValidationError(f"Failed to create billing: {str(e)}")

class PaymentScheduleRecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentScheduleRecipient
        fields = ['id', 'payment_schedule', 'email']

class PaymentScheduleSerializer(serializers.ModelSerializer):
    recipients = PaymentScheduleRecipientSerializer(many=True, read_only=True)
    reminder_recipients = serializers.ListField(
        child=serializers.EmailField(),
        source='get_reminder_recipients',
        read_only=True
    )

    class Meta:
        model = PaymentSchedule
        fields = [
            'id', 'invoice', 'amount', 'due_date', 'frequency',
            'reminder_days', 'status', 'recipients', 'reminder_recipients',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'created_at', 'updated_at']

    def validate_reminder_recipients(self, value):
        if value:
            emails = [email.strip() for email in value.split(',')]
            for email in emails:
                if not email:
                    continue
                try:
                    validate_email(email)
                except ValidationError:
                    raise serializers.ValidationError(f"Invalid email address: {email}")
        return value

class PaymentReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentReminder
        fields = [
            'id', 'payment_schedule', 'scheduled_date', 'status',
            'sent_at', 'error_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'sent_at', 'error_message', 'created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'phone_number',
            'profile_picture',
            'address',
            'date_of_birth',
            'is_active',
            'is_staff',
            'is_superuser',
            'last_login',
            'date_joined',
            'oem_pocs',
            'university_pocs'
        ]
        read_only_fields = [
            'id', 
            'is_active', 
            'is_staff', 
            'is_superuser',
            'last_login',
            'date_joined',
            'oem_pocs',
            'university_pocs'
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'password', 'password2', 'email', 'role', 
                 'phone_number', 'address', 'date_of_birth')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(**validated_data)
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        
        # Add role information
        if user.is_superuser:
            role = 'admin'
        elif hasattr(user, 'is_university_poc') and user.is_university_poc():
            role = 'university_poc'
        elif hasattr(user, 'is_provider_poc') and user.is_provider_poc():
            role = 'provider_poc'
        else:
            role = 'user'
            
        data['role'] = role
        
        # Add user details
        data['user'] = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        
        return data

class DashboardInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'name', 'amount', 'status', 'created_at']

class DashboardPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'name', 'amount', 'payment_method', 'status', 'payment_date']

class DashboardBillingSerializer(serializers.ModelSerializer):
    days_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Billing
        fields = ['id', 'name', 'balance_due', 'days_overdue']

    def get_days_overdue(self, obj):
        # Get the earliest due date from associated invoices
        earliest_due = obj.invoices.aggregate(earliest_due=models.Min('due_date'))['earliest_due']
        if earliest_due and earliest_due < date.today():
            return (date.today() - earliest_due).days
        return 0

class ChannelPartnerSerializer(serializers.ModelSerializer):
    poc = UserSerializer(read_only=True)
    poc_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source='poc',
        write_only=True,
        required=False
    )

    class Meta:
        model = ChannelPartner
        fields = [
            'id', 'name', 'website', 'contact_email', 'contact_phone',
            'address', 'poc', 'poc_id', 'commission_rate', 'status',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ChannelPartnerProgramSerializer(serializers.ModelSerializer):
    channel_partner = ChannelPartnerSerializer(read_only=True)
    channel_partner_id = serializers.PrimaryKeyRelatedField(
        queryset=ChannelPartner.objects.all(),
        source='channel_partner',
        write_only=True
    )
    program = ProgramSerializer(read_only=True)
    program_id = serializers.PrimaryKeyRelatedField(
        queryset=Program.objects.all(),
        source='program',
        write_only=True
    )
    effective_commission_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True,
        source='get_effective_commission_rate'
    )

    class Meta:
        model = ChannelPartnerProgram
        fields = [
            'id', 'channel_partner', 'channel_partner_id', 'program',
            'program_id', 'transfer_price', 'commission_rate',
            'effective_commission_rate', 'is_active', 'start_date',
            'end_date', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            'id', 'name', 'email', 'phone', 'date_of_birth',
            'address', 'enrollment_source', 'status', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ChannelPartnerStudentSerializer(serializers.ModelSerializer):
    batch = serializers.PrimaryKeyRelatedField(
        queryset=Batch.objects.all(),
        required=False,
        allow_null=True
    )
    program_batch = serializers.PrimaryKeyRelatedField(
        queryset=ProgramBatch.objects.all(),
        required=False,
        allow_null=True
    )
    student = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all()
    )
    student_details = StudentSerializer(source='student', read_only=True)
    channel_partner = serializers.PrimaryKeyRelatedField(
        queryset=ChannelPartner.objects.all()
    )
    channel_partner_details = ChannelPartnerSerializer(source='channel_partner', read_only=True)
    program_details = serializers.SerializerMethodField()

    def get_program_details(self, obj):
        if obj.batch:
            program = obj.batch.contract.programs.first()
        elif obj.program_batch:
            program = obj.program_batch.program
        else:
            return None
        
        if program:
            return ProgramSerializer(program).data
        return None

    def validate(self, data):
        if not data.get('batch') and not data.get('program_batch'):
            raise serializers.ValidationError("Either batch or program_batch must be specified")
        if data.get('batch') and data.get('program_batch'):
            raise serializers.ValidationError("Cannot specify both batch and program_batch")
        return data

    class Meta:
        model = ChannelPartnerStudent
        fields = [
            'id', 'channel_partner', 'channel_partner_details', 
            'batch', 'program_batch', 'student', 'student_details',
            'program_details', 'enrollment_date', 'transfer_price', 
            'commission_amount', 'status', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ('transfer_price', 'commission_amount', 'created_at', 'updated_at')

class ProgramBatchSerializer(serializers.ModelSerializer):
    program_details = ProgramSerializer(source='program', read_only=True)
    
    class Meta:
        model = ProgramBatch
        fields = [
            'id', 'program', 'program_details', 'name', 'start_date', 
            'end_date', 'number_of_students', 'cost_per_student', 
            'status', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')




class UniversityEventSerializer(serializers.ModelSerializer):
    """Serializer for university events"""
    
    university_details = UniversitySerializer(source='university', read_only=True)
    batch_details = BatchSerializer(source='batch', read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)
    approved_by_details = UserSerializer(source='approved_by', read_only=True)
    invitees_list = serializers.SerializerMethodField()
    invitee_emails = serializers.SerializerMethodField()
    can_be_approved = serializers.SerializerMethodField()
    can_be_rejected = serializers.SerializerMethodField()
    can_be_submitted = serializers.SerializerMethodField()
    is_approved = serializers.SerializerMethodField()
    is_pending_approval = serializers.SerializerMethodField()
    
    class Meta:
        model = UniversityEvent
        fields = [
            'id', 'university', 'university_details', 'title', 'description',
            'start_datetime', 'end_datetime', 'location', 'batch', 'batch_details',
            'status', 'created_by', 'created_by_details', 'notes', 'invitees',
            'submitted_for_approval_at', 'approved_by', 'approved_by_details',
            'approved_at', 'rejection_reason', 'notion_page_id', 'notion_page_url', 
            'integration_status', 'integration_notes', 'invitees_list', 'invitee_emails', 
            'can_be_approved', 'can_be_rejected', 'can_be_submitted', 'is_approved', 
            'is_pending_approval', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'submitted_for_approval_at',
            'approved_by', 'approved_at', 'notion_page_id', 'notion_page_url', 
            'integration_status', 'integration_notes'
        ]

    def get_invitees_list(self, obj):
        """Get list of invitees for the event"""
        return obj.get_invitees()

    def get_invitee_emails(self, obj):
        """Get list of email addresses for the event"""
        return obj.get_invitee_emails()

    def get_can_be_approved(self, obj):
        """Check if event can be approved"""
        return obj.can_be_approved()

    def get_can_be_rejected(self, obj):
        """Check if event can be rejected"""
        return obj.can_be_rejected()

    def get_can_be_submitted(self, obj):
        """Check if event can be submitted for approval"""
        return obj.can_be_submitted()

    def get_is_approved(self, obj):
        """Check if event is approved"""
        return obj.is_approved()

    def get_is_pending_approval(self, obj):
        """Check if event is pending approval"""
        return obj.is_pending_approval()

    def validate(self, data):
        """Validate event data"""
        if 'start_datetime' in data and 'end_datetime' in data:
            if data['start_datetime'] >= data['end_datetime']:
                raise serializers.ValidationError("End datetime must be after start datetime.")
        
        if 'batch' in data and data['batch']:
            if 'university' in data and data['university']:
                if data['batch'].contract.university != data['university']:
                    raise serializers.ValidationError("The selected batch must belong to this university.")
        
        return data

    def create(self, validated_data):
        """Create event with current user as creator"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class UniversityEventApprovalSerializer(serializers.Serializer):
    """Serializer for event approval/rejection actions"""
    
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['action'] == 'reject' and not data.get('reason'):
            raise serializers.ValidationError("Rejection reason is required when rejecting an event.")
        return data


class UniversityEventSubmissionSerializer(serializers.Serializer):
    """Serializer for submitting event for approval"""
    
    def validate(self, data):
        event = self.context.get('event')
        if not event:
            raise serializers.ValidationError("Event context is required.")
        
        if not event.can_be_submitted():
            raise serializers.ValidationError("Event cannot be submitted for approval.")
        
        return data


class UniversityEventInviteeSerializer(serializers.Serializer):
    """Serializer for managing event invitees"""
    
    email = serializers.EmailField()
    action = serializers.ChoiceField(choices=['add', 'remove'])
    
    def validate_email(self, value):
        """Validate email format"""
        from django.core.validators import validate_email
        try:
            validate_email(value)
        except:
            raise serializers.ValidationError("Invalid email format.")
        return value


class ExpenseSerializer(serializers.ModelSerializer):
    university_details = UniversitySerializer(source='university', read_only=True)
    batch_details = BatchSerializer(source='batch', read_only=True)
    event_details = UniversityEventSerializer(source='event', read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'university', 'university_details', 'batch', 'batch_details', 'event', 'event_details',
            'category', 'amount', 'incurred_date', 'description', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        university = data.get('university') or getattr(self.instance, 'university', None)
        batch = data.get('batch') if 'batch' in data else getattr(self.instance, 'batch', None)
        event = data.get('event') if 'event' in data else getattr(self.instance, 'event', None)

        if batch and batch.contract.university_id != university.id:
            raise serializers.ValidationError("The selected batch must belong to the specified university.")
        if event and event.university_id != university.id:
            raise serializers.ValidationError("The selected event must belong to the specified university.")
        if batch and event and event.batch and event.batch_id != batch.id:
            raise serializers.ValidationError("Event's batch does not match the selected batch.")
        # amount is optional and can be null or zero
        return data


class StaffUniversityAssignmentSerializer(serializers.ModelSerializer):
    staff_details = UserSerializer(source='staff', read_only=True)
    university_details = UniversitySerializer(source='university', read_only=True)
    assigned_by_details = UserSerializer(source='assigned_by', read_only=True)

    class Meta:
        model = StaffUniversityAssignment
        fields = [
            'id', 'staff', 'staff_details', 'university', 'university_details',
            'assigned_at', 'assigned_by', 'assigned_by_details', 'created_at', 'updated_at'
        ]
        read_only_fields = ['assigned_at', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Set assigned_by to the current user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['assigned_by'] = request.user
        return super().create(validated_data)


class UserManagementSerializer(serializers.ModelSerializer):
    """Serializer for user management by superusers"""
    assigned_universities = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'phone_number', 'address', 'date_of_birth', 'is_active',
            'is_staff', 'is_superuser', 'last_login', 'date_joined',
            'assigned_universities'
        ]
        read_only_fields = ['id', 'last_login', 'date_joined', 'is_staff']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

    def get_assigned_universities(self, obj):
        if obj.is_staff_user():
            assignments = StaffUniversityAssignment.objects.filter(staff=obj)
            return StaffUniversityAssignmentSerializer(assignments, many=True).data
        return []

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ensure role is never null - default to 'staff' if null
        if not data.get('role'):
            data['role'] = 'staff'
        return data