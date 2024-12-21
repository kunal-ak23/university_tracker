# core/admin.py
from datetime import date

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .logger_service import get_logger
from .models import Billing, Payment, OEM, Program, University, Stream, TaxRate, Contract, ContractProgram, Batch, \
    Invoice, ContractFile, CustomUser, BatchSnapshot


logger = get_logger()

def duplicate_billing(modeladmin, request, queryset):
    for billing in queryset:
        billing.pk = None  # Reset the primary key to create a new instance
        billing.save()

duplicate_billing.short_description = "Duplicate selected Billing"

class InvoiceInline(admin.TabularInline):
    model = Invoice
    readonly_fields = [field.name for field in Invoice._meta.fields]
    extra = 0

class PaymentInline(admin.TabularInline):
    model = Payment
    readonly_fields = [field.name for field in Payment._meta.fields]
    extra = 0

@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    inlines = [InvoiceInline, PaymentInline]
    readonly_fields = ['total_amount', 'created_at', 'updated_at', 'total_payments', 'balance_due', 'created_at', 'updated_at', 'version']
    list_display = ['id', 'name', 'total_amount', 'total_payments', 'balance_due', 'created_at', 'updated_at', 'add_invoice_link']
    search_fields = ['id', 'name', 'notes']
    list_filter = ['created_at', 'updated_at']
    actions = [duplicate_billing]

    def get_readonly_fields(self, request, obj=None):
        logger.info(obj)
        if obj is None:  # If editing an existing object
            return self.readonly_fields
        return self.readonly_fields + ['batch_snapshots']

    def get_exclude(self, request, obj=None):
        if obj is None:
            logger.info('Excluding batch_snapshot')
            return ['batch_snapshots']
        return []

    def add_invoice_link(self, obj):
        url = reverse('admin:core_invoice_add') + f'?billing={obj.id}'
        return mark_safe(f'<a href="{url}" class="button" onclick="return showAddAnotherPopup(this);">Add Invoice</a>')
    add_invoice_link.short_description = 'Add Invoice'
    add_invoice_link.allow_tags = True

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    readonly_fields = ['amount', 'payment_date', 'payment_method', 'status', 'transaction_reference', 'created_at', 'updated_at', 'version']
    list_display = ['id', 'billing', 'amount', 'payment_date', 'payment_method', 'status', 'created_at', 'updated_at']
    search_fields = ['id', 'billing__id', 'transaction_reference']
    list_filter = ['payment_date', 'status', 'created_at', 'updated_at']

@admin.register(OEM)
class OEMAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at', 'version']
    list_display = ['id', 'name', 'website', 'contact_email', 'contact_phone', 'created_at', 'updated_at']
    search_fields = ['id', 'name', 'website', 'contact_email', 'contact_phone']
    list_filter = ['created_at', 'updated_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_provider_poc():
            return qs.filter(poc=request.user)
        return qs.none()

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at', 'version']
    list_display = ['id', 'name', 'program_code', 'provider', 'duration', 'duration_unit', 'created_at', 'updated_at']
    search_fields = ['id', 'name', 'program_code', 'provider__name']
    list_filter = ['duration_unit', 'created_at', 'updated_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_provider_poc():
            return qs.filter(provider__poc=request.user)
        return qs.none()

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at', 'version']
    list_display = ['id', 'name', 'website', 'established_year', 'accreditation', 'contact_email', 'contact_phone', 'created_at', 'updated_at']
    search_fields = ['id', 'name', 'website', 'contact_email', 'contact_phone']
    list_filter = ['established_year', 'created_at', 'updated_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_university_poc():
            return qs.filter(poc=request.user)
        return qs.none()

@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at', 'version']
    list_display = ['id', 'name', 'duration', 'duration_unit', 'university', 'created_at', 'updated_at']
    search_fields = ['id', 'name', 'university__name']
    list_filter = ['duration_unit', 'created_at', 'updated_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_university_poc():
            return qs.filter(university__poc=request.user)
        return qs.none()

@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at', 'version']
    list_display = ['id', 'name', 'rate', 'description']
    search_fields = ['id', 'name', 'rate']
    list_filter = ['rate']

class ContractFileInline(admin.TabularInline):
    model = ContractFile
    extra = 0

class ContractProgramInline(admin.TabularInline):
    model = ContractProgram
    extra = 0

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at', 'version']
    list_display = ['id', 'name', 'cost_per_student', 'tax_rate', 'oem_transfer_price', 'start_date', 'end_date', 'status', 'created_at', 'updated_at']
    search_fields = ['id', 'name', 'tax_rate__name']
    list_filter = ['status', 'created_at', 'updated_at']
    inlines = [ContractFileInline, ContractProgramInline]

@admin.register(ContractProgram)
class ContractProgramAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at', 'version']
    list_display = ['id', 'contract', 'program', 'created_at', 'updated_at']
    search_fields = ['id', 'contract__name', 'program__name']
    list_filter = ['created_at', 'updated_at']


@admin.action(description=('Duplicate selected batch with incremented years'))
def duplicate_batch(modeladmin, request, queryset):
    if queryset.count() != 1:
        modeladmin.message_user(request, "Please select exactly one batch to duplicate.", level='error')
        return
    batch = queryset.first()
    url = reverse('admin:core_batch_add')
    initial_data = {
        'contract': batch.contract.id,
        'stream': batch.stream.id,
        'name': batch.name,
        'start_year': batch.start_year + 1,
        'end_year': batch.end_year + 1,
        'number_of_students': batch.number_of_students,
        'start_date': date(batch.start_date.year + 1, batch.start_date.month, batch.start_date.day) if batch.start_date else None,
        'end_date': date(batch.end_date.year + 1, batch.end_year.month, batch.end_date.day) if batch.end_date else None,
        'status': batch.status,
        'notes': batch.notes,
    }
    query_string = '&'.join([f'{key}={value}' for key, value in initial_data.items()])
    return HttpResponseRedirect(f'{url}?{query_string}')

class BatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'contract', 'stream', 'number_of_students', 'status']
    search_fields = ['name', 'contract__name', 'stream__name']
    list_filter = ['status', 'contract', 'stream']
    fieldsets = (
        (None, {
            'fields': ('name', 'contract', 'stream', 'number_of_students')
        }),
        ('Dates', {
            'fields': ('start_year', 'end_year', 'start_date', 'end_date')
        }),
        ('Cost Overrides', {
            'fields': ('cost_per_student_override', 'tax_rate_override', 'oem_transfer_price_override'),
            'classes': ('collapse',),
            'description': 'Override contract costs for this specific batch'
        }),
        ('Status', {
            'fields': ('status', 'notes')
        })
    )

admin.site.register(Batch, BatchAdmin)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at', 'version']
    list_display = ['id', 'billing', 'issue_date', 'due_date', 'amount', 'status', 'created_at', 'updated_at']
    search_fields = ['id', 'billing__id', 'status']
    list_filter = ['issue_date', 'due_date', 'status', 'created_at', 'updated_at']

@admin.register(ContractFile)
class ContractFileAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at', 'version']
    list_display = ['id', 'contract', 'file_type', 'uploaded_by', 'created_at', 'updated_at']
    search_fields = ['id', 'contract__name', 'file_type', 'uploaded_by']
    list_filter = ['created_at', 'updated_at']

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'phone_number', 'profile_picture', 'address', 'date_of_birth')}),
    )
    list_display = ['username', 'email', 'role', 'is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'role']
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser']

@admin.register(BatchSnapshot)
class BatchSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'batch', 
        'number_of_students', 
        'cost_per_student',
        'tax_rate',
        'oem_transfer_price',
        'status',
        'created_at'
    ]
    search_fields = ['batch__name']
    list_filter = ['status', 'created_at']
    readonly_fields = [
        'batch',
        'number_of_students',
        'start_date',
        'end_date',
        'cost_per_student',
        'tax_rate',
        'oem_transfer_price',
        'status',
        'notes',
        'created_at',
        'updated_at',
        'version'
    ]