# core/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Billing, Payment, OEM, Course, University, Stream, TaxRate, Contract, ContractCourse, Batch, Invoice, ContractFile, CustomUser

def duplicate_billing(modeladmin, request, queryset):
    for billing in queryset:
        billing.pk = None  # Reset the primary key to create a new instance
        billing.save()

duplicate_billing.short_description = "Duplicate selected Billing"

class PaymentInline(admin.TabularInline):
    model = Payment
    readonly_fields = ['amount', 'notes', 'payment_date', 'payment_method', 'status', 'transaction_reference', 'created_at', 'updated_at']

@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    inlines = [PaymentInline]
    readonly_fields = ['total_amount', 'created_at', 'updated_at', 'total_payments', 'balance_due']
    list_display = ['id', 'name', 'total_amount', 'total_payments', 'balance_due', 'created_at', 'updated_at']
    search_fields = ['id', 'name', 'notes']
    list_filter = ['created_at', 'updated_at']
    actions = [duplicate_billing]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    readonly_fields = ['amount', 'payment_date', 'payment_method', 'status', 'transaction_reference', 'created_at', 'updated_at']
    list_display = ['id', 'billing', 'amount', 'payment_date', 'payment_method', 'status', 'created_at', 'updated_at']
    search_fields = ['id', 'billing__id', 'transaction_reference']
    list_filter = ['payment_date', 'status', 'created_at', 'updated_at']

@admin.register(OEM)
class OEMAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at']
    list_display = ['id', 'name', 'website', 'contact_email', 'contact_phone', 'created_at', 'updated_at']
    search_fields = ['id', 'name', 'website', 'contact_email', 'contact_phone']
    list_filter = ['created_at', 'updated_at']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at']
    list_display = ['id', 'name', 'course_code', 'provider', 'duration', 'duration_unit', 'created_at', 'updated_at']
    search_fields = ['id', 'name', 'course_code', 'provider__name']
    list_filter = ['duration_unit', 'created_at', 'updated_at']

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at']
    list_display = ['id', 'name', 'website', 'established_year', 'accreditation', 'contact_email', 'contact_phone', 'created_at', 'updated_at']
    search_fields = ['id', 'name', 'website', 'contact_email', 'contact_phone']
    list_filter = ['established_year', 'created_at', 'updated_at']

@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at']
    list_display = ['id', 'name', 'duration', 'duration_unit', 'university', 'created_at', 'updated_at']
    search_fields = ['id', 'name', 'university__name']
    list_filter = ['duration_unit', 'created_at', 'updated_at']

@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'rate', 'description']
    search_fields = ['id', 'name', 'rate']
    list_filter = ['rate']

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at']
    list_display = ['id', 'name', 'stream', 'cost_per_student', 'tax_rate', 'oem_transfer_price', 'start_date', 'end_date', 'status', 'created_at', 'updated_at']
    search_fields = ['id', 'name', 'stream__name', 'tax_rate__name']
    list_filter = ['status', 'created_at', 'updated_at']

@admin.register(ContractCourse)
class ContractCourseAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at']
    list_display = ['id', 'contract', 'course', 'created_at', 'updated_at']
    search_fields = ['id', 'contract__name', 'course__name']
    list_filter = ['created_at', 'updated_at']

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at']
    list_display = ['id', 'contract', 'name', 'start_year', 'end_year', 'number_of_students', 'start_date', 'end_date', 'status', 'created_at', 'updated_at']
    search_fields = ['id', 'contract__name', 'name', 'status']
    list_filter = ['status', 'start_year', 'end_year', 'created_at', 'updated_at']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at']
    list_display = ['id', 'billing', 'issue_date', 'due_date', 'amount', 'status', 'created_at', 'updated_at']
    search_fields = ['id', 'billing__id', 'status']
    list_filter = ['issue_date', 'due_date', 'status', 'created_at', 'updated_at']

@admin.register(ContractFile)
class ContractFileAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at']
    list_display = ['id', 'contract', 'file_type', 'uploaded_by', 'created_at', 'updated_at']
    search_fields = ['id', 'contract__name', 'file_type', 'uploaded_by']
    list_filter = ['created_at', 'updated_at']

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'phone_number', 'profile_picture', 'provider', 'address', 'date_of_birth')}),
    )
    list_display = ['username', 'email', 'role', 'provider', 'is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'role', 'provider']
    list_filter = ['role', 'provider', 'is_active', 'is_staff', 'is_superuser']