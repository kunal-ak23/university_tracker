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
    Invoice, ContractFile, CustomUser, BatchSnapshot, PaymentDocument, PaymentScheduleRecipient, PaymentSchedule, \
    ChannelPartner, ChannelPartnerProgram, ChannelPartnerStudent, Student, ProgramBatch, UniversityEvent


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
    extra = 0
    fields = ['amount', 'payment_date', 'payment_method', 'status', 'transaction_reference', 'notes']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    inlines = [InvoiceInline]
    list_display = ['id', 'name', 'get_total_amount', 'get_total_payments', 'get_balance_due', 'created_at', 'updated_at', 'add_invoice_link']
    search_fields = ['id', 'name', 'notes']
    list_filter = ['created_at', 'updated_at']
    actions = [duplicate_billing]
    readonly_fields = ['get_total_amount', 'get_total_payments', 'get_balance_due', 'get_total_oem_transfer_amount', 'created_at', 'updated_at', 'version']
    fields = ['name', 'batches', 'notes', 'get_total_amount', 'get_total_payments', 'get_balance_due', 'get_total_oem_transfer_amount']

    def get_total_amount(self, obj):
        return obj.total_amount
    get_total_amount.short_description = 'Total Amount'

    def get_total_payments(self, obj):
        return obj.total_payments
    get_total_payments.short_description = 'Total Payments'

    def get_balance_due(self, obj):
        return obj.balance_due
    get_balance_due.short_description = 'Balance Due'

    def get_total_oem_transfer_amount(self, obj):
        return obj.total_oem_transfer_amount
    get_total_oem_transfer_amount.short_description = 'Total OEM Transfer Amount'

    def get_readonly_fields(self, request, obj=None):
        if obj is None:  # If creating a new object
            return ['get_total_amount', 'get_total_payments', 'get_balance_due', 'get_total_oem_transfer_amount', 'created_at', 'updated_at', 'version']
        return self.readonly_fields

    def get_exclude(self, request, obj=None):
        if obj is None:
            return ['batch_snapshots']
        return []

    def add_invoice_link(self, obj):
        url = reverse('admin:core_invoice_add') + f'?billing={obj.id}'
        return mark_safe(f'<a href="{url}" class="button" onclick="return showAddAnotherPopup(this);">Add Invoice</a>')
    add_invoice_link.short_description = 'Add Invoice'
    add_invoice_link.allow_tags = True

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
    inlines = [PaymentInline]
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
    list_display = ['id', 'batch', 'number_of_students', 'cost_per_student', 'tax_rate', 'oem_transfer_price', 'status']
    list_filter = ['status', 'batch']
    search_fields = ['batch__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PaymentDocument)
class PaymentDocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'payment', 'description', 'uploaded_by', 'created_at']
    list_filter = ['uploaded_by']
    search_fields = ['description', 'payment__transaction_reference']
    readonly_fields = ['uploaded_by', 'created_at', 'updated_at']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'invoice', 'amount', 'payment_date', 'payment_method', 'status', 'transaction_reference']
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = ['transaction_reference', 'notes']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PaymentScheduleRecipient)
class PaymentScheduleRecipientAdmin(admin.ModelAdmin):
    list_display = ['id', 'payment_schedule', 'email']
    list_filter = ['payment_schedule']
    search_fields = ['email']

class PaymentScheduleRecipientInline(admin.TabularInline):
    model = PaymentScheduleRecipient
    extra = 1
    fields = ['email']

@admin.register(PaymentSchedule)
class PaymentScheduleAdmin(admin.ModelAdmin):
    list_display = ['id', 'invoice', 'amount', 'due_date', 'frequency', 'status']
    list_filter = ['status', 'frequency', 'due_date']
    search_fields = ['invoice__reference_number']
    readonly_fields = ['status', 'created_at', 'updated_at']
    inlines = [PaymentScheduleRecipientInline]

class ChannelPartnerProgramInline(admin.TabularInline):
    model = ChannelPartnerProgram
    extra = 0

@admin.register(ChannelPartner)
class ChannelPartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_email', 'contact_phone', 'commission_rate', 'status']
    search_fields = ['name', 'contact_email', 'contact_phone']
    list_filter = ['status', 'created_at', 'updated_at']
    inlines = [ChannelPartnerProgramInline]

@admin.register(ChannelPartnerProgram)
class ChannelPartnerProgramAdmin(admin.ModelAdmin):
    list_display = ['channel_partner', 'program', 'transfer_price', 'commission_rate', 'is_active']
    search_fields = ['channel_partner__name', 'program__name']
    list_filter = ['is_active', 'created_at', 'updated_at']

@admin.register(ChannelPartnerStudent)
class ChannelPartnerStudentAdmin(admin.ModelAdmin):
    list_display = ('get_student_name', 'channel_partner', 'batch', 'enrollment_date', 'transfer_price', 'commission_amount', 'status')
    search_fields = ('student__name', 'student__email', 'channel_partner__name', 'batch__name')
    list_filter = ('status', 'enrollment_date', 'channel_partner', 'batch')
    ordering = ('-enrollment_date',)

    def get_student_name(self, obj):
        return obj.student.name
    get_student_name.short_description = 'Student Name'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'enrollment_source', 'status']
    search_fields = ['name', 'email', 'phone', 'address', 'notes']
    list_filter = ['enrollment_source', 'status', 'created_at', 'updated_at']
    ordering = ['name']

@admin.register(ProgramBatch)
class ProgramBatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'program', 'start_date', 'end_date', 'number_of_students', 'cost_per_student', 'status')
    search_fields = ('name', 'program__name', 'notes')
    list_filter = ('status', 'start_date', 'end_date', 'program')
    ordering = ('-start_date',)




@admin.register(UniversityEvent)
class UniversityEventAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'university', 'start_datetime', 'end_datetime', 
        'location', 'status', 'integration_status', 'created_by', 'approved_by'
    ]
    list_filter = [
        'status', 'integration_status', 'university', 'batch', 
        'start_datetime', 'end_datetime', 'created_at', 'updated_at'
    ]
    search_fields = [
        'title', 'description', 'location', 'notes', 
        'university__name', 'batch__name', 'created_by__username'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'version', 'submitted_for_approval_at',
        'approved_at', 'outlook_calendar_id', 'outlook_calendar_url',
        'notion_page_id', 'notion_page_url', 'integration_notes'
    ]
    fieldsets = (
        ('Event Information', {
            'fields': ('title', 'description', 'start_datetime', 'end_datetime', 'location')
        }),
        ('Organization', {
            'fields': ('university', 'batch', 'created_by')
        }),
        ('Status & Approval', {
            'fields': ('status', 'submitted_for_approval_at', 'approved_by', 'approved_at', 'rejection_reason')
        }),
        ('Integration', {
            'fields': ('integration_status', 'outlook_calendar_id', 'outlook_calendar_url', 
                      'notion_page_id', 'notion_page_url', 'integration_notes'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at', 'version'),
            'classes': ('collapse',)
        }),
    )

    ordering = ['-start_datetime']
    date_hierarchy = 'start_datetime'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_university_poc():
            return qs.filter(university__poc=request.user)
        if request.user.is_provider_poc():
            return qs.filter(batch__contract__oem__poc=request.user)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new event
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    actions = ['approve_events', 'reject_events', 'update_status']

    @admin.action(description='Approve selected events')
    def approve_events(self, request, queryset):
        approved_count = 0
        for event in queryset.filter(status='pending_approval'):
            try:
                event.approve(request.user)
                approved_count += 1
            except Exception as e:
                self.message_user(request, f"Failed to approve event {event.title}: {str(e)}", level='ERROR')
        
        if approved_count > 0:
            self.message_user(request, f"Successfully approved {approved_count} events.")

    @admin.action(description='Reject selected events')
    def reject_events(self, request, queryset):
        rejected_count = 0
        for event in queryset.filter(status='pending_approval'):
            try:
                event.reject(request.user, "Rejected via admin action")
                rejected_count += 1
            except Exception as e:
                self.message_user(request, f"Failed to reject event {event.title}: {str(e)}", level='ERROR')
        
        if rejected_count > 0:
            self.message_user(request, f"Successfully rejected {rejected_count} events.")

    @admin.action(description='Update status based on current time')
    def update_status(self, request, queryset):
        updated_count = 0
        for event in queryset.filter(status='approved'):
            try:
                event.update_status()
                updated_count += 1
            except Exception as e:
                self.message_user(request, f"Failed to update status for event {event.title}: {str(e)}", level='ERROR')
        
        if updated_count > 0:
            self.message_user(request, f"Successfully updated status for {updated_count} events.")


