from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from core.logger_service import get_logger

logger = get_logger()

from .models import (
    OEM, Program, CustomUser, University, Contract, ContractProgram, Batch,
    Billing, Payment, ContractFile, Stream, TaxRate, BatchSnapshot, Invoice, PaymentSchedule, PaymentReminder
)

# University Serializer
class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = '__all__'


# OEM Serializer
class OEMSerializer(serializers.ModelSerializer):
    class Meta:
        model = OEM
        fields = '__all__'


# Stream Serializer
class StreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stream
        fields = '__all__'


# ContractFile Serializer
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


# Program Serializer
class ProgramSerializer(serializers.ModelSerializer):
    provider = OEMSerializer()

    class Meta:
        model = Program
        fields = '__all__'


# ContractProgram Serializer
class ContractProgramSerializer(serializers.ModelSerializer):
    program = ProgramSerializer()

    class Meta:
        model = ContractProgram
        fields = '__all__'


# Contract Serializer
class ContractSerializer(serializers.ModelSerializer):
    # Read-only nested serializers for GET requests
    contract_programs = ContractProgramSerializer(many=True, read_only=True)
    contract_files = ContractFileSerializer(many=True, read_only=True)
    streams = StreamSerializer(many=True, read_only=True)
    oem = OEMSerializer(read_only=True)
    university = UniversitySerializer(read_only=True)
    programs = ProgramSerializer(many=True, read_only=True)
    
    # Write-only fields for PUT/PATCH requests
    streams_ids = serializers.PrimaryKeyRelatedField(
        queryset=Stream.objects.all(),
        many=True,
        write_only=True,
        source='streams'
    )
    programs_ids = serializers.PrimaryKeyRelatedField(
        queryset=Program.objects.all(),
        many=True,
        write_only=True,
        source='programs'
    )
    oem_id = serializers.PrimaryKeyRelatedField(
        queryset=OEM.objects.all(),
        write_only=True,
        source='oem'
    )
    university_id = serializers.PrimaryKeyRelatedField(
        queryset=University.objects.all(),
        write_only=True,
        source='university'
    )

    class Meta:
        model = Contract
        fields = [
            'id', 'name', 'cost_per_student', 'oem_transfer_price',
            'start_date', 'end_date', 'status', 'notes', 'tax_rate',
            'contract_programs', 'contract_files', 'streams', 'oem', 
            'university', 'programs', 'streams_ids', 'programs_ids', 
            'oem_id', 'university_id'
        ]


# Batch Serializer
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

    class Meta:
        model = Batch
        fields = [
            'id', 'name', 'contract', 'stream', 'number_of_students',
            'start_year', 'end_year', 'start_date', 'end_date',
            'cost_per_student_override', 'tax_rate_override',
            'effective_cost_per_student', 'effective_tax_rate',
            'status', 'notes'
        ]


# Billing Serializer
class BillingSerializer(serializers.ModelSerializer):
    batch = BatchSerializer(read_only=True)
    batch_id = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all(), source='batch', write_only=True)
    total_payments = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Billing
        fields = '__all__'


# Payment Serializer
class PaymentSerializer(serializers.ModelSerializer):
    billing = BillingSerializer(read_only=True)
    billing_id = serializers.PrimaryKeyRelatedField(queryset=Billing.objects.all(), source='billing', write_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'billing', 'invoice', 'amount', 'payment_date',
            'payment_method', 'status', 'transaction_reference',
            'notes', 'attachment', 'created_at', 'updated_at'
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


class TaxRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxRate
        fields = '__all__'


class BatchSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchSnapshot
        fields = [
            'id', 'batch', 'number_of_students', 'start_date', 'end_date',
            'cost_per_student', 'tax_rate', 'status', 'notes'
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remaining_amount = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'billing', 'issue_date', 'due_date', 'amount',
            'amount_paid', 'remaining_amount', 'status', 'notes',
            'proforma_invoice', 'actual_invoice', 'payments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'amount_paid', 'created_at', 'updated_at']

    def get_remaining_amount(self, obj):
        return obj.amount - obj.amount_paid


class PaymentScheduleSerializer(serializers.ModelSerializer):
    reminder_recipients_list = serializers.ListField(
        child=serializers.EmailField(),
        source='get_reminder_recipients',
        read_only=True
    )

    class Meta:
        model = PaymentSchedule
        fields = [
            'id', 'invoice', 'amount', 'due_date', 'frequency',
            'reminder_days', 'reminder_recipients', 'reminder_recipients_list',
            'status', 'notes', 'created_at', 'updated_at'
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
            # Add related fields
            'oem_pocs',          # OEMs where user is POC
            'university_pocs',   # Universities where user is POC
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
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        return token