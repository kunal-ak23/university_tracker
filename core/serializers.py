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
    OEM, Program, CustomUser, University, Contract, ContractProgram, Batch,
    Billing, Payment, ContractFile, Stream, TaxRate, BatchSnapshot, Invoice,
    PaymentSchedule, PaymentReminder, PaymentDocument, PaymentScheduleRecipient,
    ChannelPartner, ChannelPartnerProgram, ChannelPartnerStudent, Student, ProgramBatch
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

class ContractSerializer(serializers.ModelSerializer):
    contract_programs = ContractProgramSerializer(many=True, read_only=True)
    contract_files = ContractFileSerializer(many=True, read_only=True)
    streams = StreamSerializer(many=True, read_only=True)
    oem = OEMSerializer(read_only=True)
    university = UniversitySerializer(read_only=True)
    programs = ProgramSerializer(many=True, read_only=True)
    tax_rate = TaxRateSerializer(read_only=True)
    oem_id = serializers.PrimaryKeyRelatedField(queryset=OEM.objects.all(), source='oem', write_only=True)
    university_id = serializers.PrimaryKeyRelatedField(queryset=University.objects.all(), source='university', write_only=True)
    tax_rate_id = serializers.PrimaryKeyRelatedField(queryset=TaxRate.objects.all(), source='tax_rate', write_only=True)
    programs_ids = serializers.PrimaryKeyRelatedField(many=True, queryset=Program.objects.all(), write_only=True, source='programs')
    streams_ids = serializers.PrimaryKeyRelatedField(many=True, queryset=Stream.objects.all(), write_only=True, source='streams')
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Contract
        fields = [
            'id', 'name', 'cost_per_student', 'oem_transfer_price',
            'start_date', 'end_date', 'status', 'notes', 'tax_rate',
            'contract_programs', 'contract_files', 'streams', 'oem', 
            'university', 'programs', 'oem_id', 'university_id', 'tax_rate_id',
            'programs_ids', 'streams_ids', 'created_at', 'updated_at'
        ]

class BatchSerializer(serializers.ModelSerializer):
    effective_cost_per_student = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2,
        read_only=True,
        source='get_cost_per_student'
    )
    effective_tax_rate = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2,
        read_only=True,
        source='get_tax_rate.rate'
    )
    effective_oem_transfer_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
        source='get_oem_transfer_price'
    )

    class Meta:
        model = Batch
        fields = [
            'id', 'name', 'contract', 'stream', 'number_of_students',
            'start_year', 'end_year', 'start_date', 'end_date',
            'cost_per_student_override', 'tax_rate_override',
            'oem_transfer_price_override', 'effective_cost_per_student',
            'effective_tax_rate', 'effective_oem_transfer_price',
            'status', 'notes'
        ]

class BatchSnapshotSerializer(serializers.ModelSerializer):
    batch_name = serializers.CharField(source='batch.name', read_only=True)
    batch_stream = serializers.CharField(source='batch.stream.name', read_only=True)
    batch_contract = serializers.CharField(source='batch.contract.name', read_only=True)

    class Meta:
        model = BatchSnapshot
        fields = [
            'id', 'batch', 'batch_name', 'batch_stream', 'batch_contract',
            'number_of_students', 'cost_per_student', 'tax_rate', 
            'oem_transfer_price', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

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
    channel_partner = ChannelPartnerSerializer(read_only=True)
    channel_partner_id = serializers.PrimaryKeyRelatedField(
        queryset=ChannelPartner.objects.all(),
        source='channel_partner',
        write_only=True
    )
    batch = BatchSerializer(read_only=True)
    batch_id = serializers.PrimaryKeyRelatedField(
        queryset=Batch.objects.all(),
        source='batch',
        write_only=True
    )
    student = StudentSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        source='student',
        write_only=True
    )

    class Meta:
        model = ChannelPartnerStudent
        fields = [
            'id', 'channel_partner', 'channel_partner_id', 'batch',
            'batch_id', 'student', 'student_id', 'enrollment_date',
            'transfer_price', 'commission_amount', 'status', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

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