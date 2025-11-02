import logging
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from rest_framework.exceptions import ValidationError

logger = logging.getLogger('django')

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Pop skip_update if present (used by child classes like Invoice)
        kwargs.pop('skip_update', None)
        
        if self.pk:
            # Get current version and increment it
            current = self.__class__.objects.get(pk=self.pk)
            self.version = current.version + 1
        super().save(*args, **kwargs)


@receiver(pre_save)
def log_model_changes(sender, instance, **kwargs):
    if not issubclass(sender, BaseModel):
        return

    if instance.pk:
        old_instance = sender.objects.get(pk=instance.pk)
        changes = []
        for field in instance._meta.fields:
            field_name = field.name
            old_value = getattr(old_instance, field_name)
            new_value = getattr(instance, field_name)
            if old_value != new_value:
                changes.append(f'{field_name} changed from {old_value} to {new_value}')
        if changes:
            logger.info(f'{sender.__name__} {instance.pk} changes: {"; ".join(changes)}')


@receiver(post_save, sender='core.UniversityEvent')
def handle_event_approval(sender, instance, created, **kwargs):
    """Handle post-save actions for UniversityEvent"""
    # Only trigger integrations when status changes to 'approved' and it's not a new creation
    if not created and instance.status == 'approved':
        # Check if this is an integration update to avoid infinite recursion
        if hasattr(instance, '_integration_update') and instance._integration_update:
            return
            
        # Trigger integration tasks when event is approved
        # Note: For automatic triggers, we don't have a request object, so we'll skip Outlook integration
        # Users can manually trigger it after authentication
        from .services import trigger_event_integrations
        try:
            trigger_event_integrations(instance)
        except Exception as e:
            logger.error(f"Failed to trigger integrations for event {instance.id}: {str(e)}")
            instance.mark_integration_failed(f"Integration trigger failed: {str(e)}")


class OEM(BaseModel):
    name = models.CharField(max_length=255)
    website = models.URLField()
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    poc = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, related_name='oem_pocs')

    def __str__(self):
        return self.name

    def clean(self):
        if self.poc and not (self.poc.is_provider_poc() or self.poc.is_superuser):
            raise ValidationError("The POC must be either a 'university_poc' or a 'superuser'.")

    def delete(self, *args, **kwargs):
        if self.contracts.exists():
            raise ValidationError("Cannot delete OEM as it has associated contracts. Please delete the contracts first.")
        return super().delete(*args, **kwargs)

class Program(BaseModel):
    DURATION_UNIT_CHOICES = [
        ('Days', 'Days'),
        ('Months', 'Months'),
        ('Years', 'Years'),
    ]

    name = models.CharField(max_length=255)
    program_code = models.CharField(max_length=50, unique=True)
    provider = models.ForeignKey(OEM, on_delete=models.CASCADE, related_name='programs', help_text="Name of the OEM")
    duration = models.PositiveIntegerField(help_text='Duration')
    duration_unit = models.CharField(max_length=50, choices=DURATION_UNIT_CHOICES)
    description = models.TextField(blank=True, null=True)
    prerequisites = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('name', 'provider')

    def __str__(self):
        return f'{self.name} (Code: {self.program_code}, OEM: {self.provider.name})'


class University(BaseModel):
    name = models.CharField(max_length=255)
    website = models.URLField()
    established_year = models.PositiveIntegerField()
    accreditation = models.CharField(max_length=255, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    poc = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, related_name='university_pocs')

    def __str__(self):
        return self.name

    def clean(self):
        if self.poc and not (self.poc.is_university_poc() or self.poc.is_superuser):
            raise ValidationError("The POC must be either a 'university_poc' or a 'superuser'.")


class UniversityEvent(BaseModel):
    EVENT_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=500)
    batch = models.ForeignKey('Batch', on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    status = models.CharField(max_length=20, choices=EVENT_STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='created_events')
    notes = models.TextField(blank=True, null=True)
    
    # Invitees field - comma separated email IDs
    invitees = models.TextField(blank=True, null=True, help_text="Comma separated email addresses")
    
    # Approval fields
    submitted_for_approval_at = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_events')
    approved_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Integration tracking fields
    notion_page_id = models.CharField(max_length=255, blank=True, null=True, help_text="Notion Page ID")
    notion_page_url = models.URLField(blank=True, null=True, help_text="Notion Page URL")
    integration_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('notion_created', 'Notion Created'),
        ('failed', 'Failed'),
    ], default='pending')
    integration_notes = models.TextField(blank=True, null=True, help_text="Notes about integration status")

    class Meta:
        ordering = ['start_datetime']
        verbose_name = 'University Event'
        verbose_name_plural = 'University Events'

    def __str__(self):
        return f'{self.title} - {self.university.name} ({self.start_datetime.strftime("%Y-%m-%d %H:%M")})'

    def clean(self):
        if self.start_datetime and self.end_datetime:
            if self.start_datetime >= self.end_datetime:
                raise ValidationError("End datetime must be after start datetime.")
        
        if self.batch:
            contract = self.batch.get_contract()
            if contract and contract.university != self.university:
                raise ValidationError("The selected batch must belong to this university.")

    def get_invitees(self):
        """Returns list of people to whom invites should be extended"""
        invitees = []
        
        # Add university POC
        if self.university and self.university.poc:
            invitees.append({
                'name': self.university.poc.get_full_name() or self.university.poc.username,
                'email': self.university.poc.email,
                'role': 'University POC'
            })
        
        # Add OEM POC if batch is associated and has a contract
        if self.batch:
            contract = self.batch.get_contract()
            if contract and contract.oem and contract.oem.poc:
                invitees.append({
                    'name': contract.oem.poc.get_full_name() or contract.oem.poc.username,
                    'email': contract.oem.poc.email,
                    'role': 'OEM POC'
                })
        
        # Add batch-specific invitees if batch is associated
        if self.batch:
            # Add channel partner POCs for this batch
            for cps in self.batch.channel_partner_students.select_related('channel_partner__poc').distinct('channel_partner'):
                if cps.channel_partner.poc:
                    invitees.append({
                        'name': cps.channel_partner.poc.get_full_name() or cps.channel_partner.poc.username,
                        'email': cps.channel_partner.poc.email,
                        'role': f'Channel Partner POC ({cps.channel_partner.name})'
                    })
        
        # Add custom invitees from comma-separated field
        if self.invitees:
            custom_emails = [email.strip() for email in self.invitees.split(',') if email.strip()]
            for email in custom_emails:
                invitees.append({
                    'name': email,  # Use email as name if no additional info
                    'email': email,
                    'role': 'Custom Invitee'
                })
        
        return invitees

    def get_invitee_emails(self):
        """Returns list of email addresses for the event"""
        emails = []
        
        # Add automatic invitees
        for invitee in self.get_invitees():
            emails.append(invitee['email'])
        
        return emails

    def add_invitee(self, email):
        """Add an email to the invitees list"""
        if not self.invitees:
            self.invitees = email
        else:
            # Check if email already exists
            existing_emails = [e.strip() for e in self.invitees.split(',')]
            if email not in existing_emails:
                self.invitees = f"{self.invitees}, {email}"
        self.save(update_fields=['invitees'])

    def remove_invitee(self, email):
        """Remove an email from the invitees list"""
        if self.invitees:
            emails = [e.strip() for e in self.invitees.split(',')]
            if email in emails:
                emails.remove(email)
                self.invitees = ', '.join(emails) if emails else None
                self.save(update_fields=['invitees'])

    def is_upcoming(self):
        """Check if event is upcoming (not started yet)"""
        from django.utils import timezone
        return self.start_datetime > timezone.now()

    def is_ongoing(self):
        """Check if event is currently ongoing"""
        from django.utils import timezone
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime

    def is_completed(self):
        """Check if event has completed"""
        from django.utils import timezone
        return self.end_datetime < timezone.now()

    def submit_for_approval(self):
        """Submit event for approval"""
        from django.utils import timezone
        
        if self.status != 'draft':
            raise ValidationError("Only draft events can be submitted for approval.")
        
        self.status = 'pending_approval'
        self.submitted_for_approval_at = timezone.now()
        self.save(update_fields=['status', 'submitted_for_approval_at'])

    def approve(self, approved_by_user):
        """Approve the event"""
        from django.utils import timezone
        
        if self.status != 'pending_approval':
            raise ValidationError("Only pending approval events can be approved.")
        
        if not approved_by_user.is_superuser:
            raise ValidationError("Only superusers can approve events.")
        
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save(update_fields=['status', 'approved_by', 'approved_at'])

    def reject(self, rejected_by_user, reason):
        """Reject the event"""
        from django.utils import timezone
        
        if self.status != 'pending_approval':
            raise ValidationError("Only pending approval events can be rejected.")
        
        if not rejected_by_user.is_superuser:
            raise ValidationError("Only superusers can reject events.")
        
        self.status = 'rejected'
        self.rejection_reason = reason
        self.save(update_fields=['status', 'rejection_reason'])

    def update_status(self):
        """Update event status based on current time (only for approved events)"""
        from django.utils import timezone
        now = timezone.now()
        
        # Only update status for approved events
        if self.status == 'approved':
            if self.is_completed():
                self.status = 'completed'
            elif self.is_ongoing():
                self.status = 'ongoing'
            elif self.is_upcoming():
                self.status = 'upcoming'
            
            self.save(update_fields=['status'])




    def mark_notion_created(self, page_id, page_url):
        """Mark Notion page as created"""
        self.notion_page_id = page_id
        self.notion_page_url = page_url
        
        if self.integration_status == 'pending':
            self.integration_status = 'notion_created'
        
        # Set flag to prevent infinite recursion
        self._integration_update = True
        self.save(update_fields=['notion_page_id', 'notion_page_url', 'integration_status'])

    def mark_integration_failed(self, error_message):
        """Mark integration as failed"""
        self.integration_status = 'failed'
        self.integration_notes = error_message
        # Set flag to prevent infinite recursion
        self._integration_update = True
        self.save(update_fields=['integration_status', 'integration_notes'])

    def can_be_approved(self):
        """Check if event can be approved"""
        return self.status == 'pending_approval'

    def can_be_rejected(self):
        """Check if event can be rejected"""
        return self.status == 'pending_approval'

    def can_be_submitted(self):
        """Check if event can be submitted for approval"""
        return self.status == 'draft'

    def is_approved(self):
        """Check if event is approved"""
        return self.status == 'approved'

    def is_pending_approval(self):
        """Check if event is pending approval"""
        return self.status == 'pending_approval'
    





class Expense(BaseModel):
    CATEGORY_CHOICES = [
        ('marketing', 'Marketing'),
        ('travel', 'Travel'),
        ('operations', 'Operations'),
        ('logistics', 'Logistics'),
        ('venue', 'Venue'),
        ('speaker', 'Speaker'),
        ('other', 'Other'),
    ]

    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='expenses')
    batch = models.ForeignKey('Batch', on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    event = models.ForeignKey('UniversityEvent', on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    incurred_date = models.DateField()
    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-incurred_date', '-created_at']
        indexes = [
            models.Index(fields=['university', 'incurred_date']),
            models.Index(fields=['batch', 'incurred_date']),
            models.Index(fields=['event']),
        ]

    def __str__(self):
        target = self.event.title if self.event else (self.batch.name if self.batch else self.university.name)
        return f'Expense {self.category} - ₹{self.amount} - {target} - {self.incurred_date}'

    def clean(self):
        super().clean()
        # Ensure relationships are consistent
        if self.batch and self.batch.contract.university_id != self.university_id:
            raise ValidationError("The selected batch must belong to this university.")
        if self.event and self.event.university_id != self.university_id:
            raise ValidationError("The selected event must belong to this university.")
        # If both batch and event are set, ensure event references same batch if event has one
        if self.batch and self.event and self.event.batch and self.event.batch_id != self.batch_id:
            raise ValidationError("Event's batch does not match the selected batch.")

class Stream(BaseModel):
    DURATION_UNIT_CHOICES = [
        ('Days', 'Days'),
        ('Months', 'Months'),
        ('Years', 'Years'),
    ]
    name = models.CharField(max_length=255)
    duration = models.PositiveIntegerField(help_text='Duration')
    duration_unit = models.CharField(max_length=50, choices=DURATION_UNIT_CHOICES)
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='streams')
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.name} ({self.university.name})'


class TaxRate(BaseModel):
    name = models.CharField(max_length=255)
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.name} ({self.rate}%)'


class Contract(BaseModel):
    CONTRACT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('planned', 'Planned'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]

    name = models.CharField(max_length=100)
    oem = models.ForeignKey(OEM, on_delete=models.CASCADE, related_name='contracts')
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='contracts')
    start_year = models.PositiveIntegerField(help_text='Contract start year', default=2024)
    end_year = models.PositiveIntegerField(help_text='Contract end year', default=2025)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=CONTRACT_STATUS_CHOICES, default='active')
    programs = models.ManyToManyField(Program, through='ContractProgram', related_name='contracts')
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = [['name', 'oem', 'university']]

    def __str__(self):
        return f'Contract {self.name} ({self.university.name} - {self.oem.name}) {self.start_year}-{self.end_year}'

    def clean(self):
        super().clean()
        if self.start_year and self.end_year and self.start_year >= self.end_year:
            raise ValidationError("Start year must be before end year.")
        if self.pk and not self.contract_files.exists():
            raise ValidationError("Contract must have at least one file.")

    def get_stream_pricing(self, stream, year, program=None):
        """Get pricing for a specific stream and year, optionally filtered by program"""
        try:
            if program:
                return self.stream_pricing.get(program=program, stream=stream, year=year)
            else:
                # If no program specified, get the first available pricing for this stream/year
                return self.stream_pricing.filter(stream=stream, year=year).first()
        except ContractStreamPricing.DoesNotExist:
            return None

    def get_available_streams(self):
        """Get all streams that have pricing defined"""
        return Stream.objects.filter(
            stream_pricing__contract=self
        ).distinct()

    def get_available_years(self):
        """Get all years that have pricing defined"""
        return self.stream_pricing.values_list('year', flat=True).distinct().order_by('year')


class ContractStreamPricing(BaseModel):
    """Pricing for specific program, stream and year within a contract"""
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='stream_pricing')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='stream_pricing', default=1)
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='stream_pricing')
    year = models.PositiveIntegerField(help_text='Year for this pricing')
    cost_per_student = models.DecimalField(max_digits=12, decimal_places=2, help_text='Cost per student for this program/stream/year')
    oem_transfer_price = models.DecimalField(max_digits=12, decimal_places=2, help_text='OEM transfer price for this program/stream/year')
    tax_rate = models.ForeignKey(TaxRate, on_delete=models.SET_DEFAULT, default=0, related_name='stream_pricing')

    class Meta:
        unique_together = ('contract', 'program', 'stream', 'year')
        ordering = ['program__name', 'stream__name', 'year']

    def __str__(self):
        return f'{self.contract.name} - {self.program.name}/{self.stream.name} ({self.year}): ₹{self.cost_per_student}'

    def clean(self):
        super().clean()
        # Validate year is within contract range
        if self.contract and self.year:
            if self.year < self.contract.start_year or self.year > self.contract.end_year:
                raise ValidationError(f"Year {self.year} must be within contract range {self.contract.start_year}-{self.contract.end_year}")
        
        # Validate stream belongs to the same university as contract
        if self.contract and self.stream:
            if self.stream.university != self.contract.university:
                raise ValidationError(f"Stream {self.stream.name} must belong to the same university as the contract")
        
        # Validate program is associated with the contract
        if self.contract and self.program:
            if not self.contract.programs.filter(id=self.program.id).exists():
                raise ValidationError(f"Program {self.program.name} must be associated with the contract")


class ContractFile(BaseModel):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='contract_files')
    file_type = models.CharField(max_length=50)
    uploaded_by = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    file = models.FileField(upload_to='contracts/files/', null=False)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'File {self.file_type} for {self.contract.name}'

class ContractProgram(BaseModel):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='contract_programs')
    program = models.ForeignKey(Program, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('contract', 'program')

    def __str__(self):
        return f'{self.contract.name} - {self.program.name}'


class Batch(BaseModel):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='batches', null=True, blank=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='batches', null=True, blank=True)
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='batches')
    name = models.CharField(max_length=255)
    start_year = models.PositiveIntegerField(help_text='Start Year')
    end_year = models.PositiveIntegerField(help_text='End Year')
    number_of_students = models.PositiveIntegerField()
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    status = models.CharField(max_length=20, choices=[
        ('planned', 'Planned'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ], default='planned')
    notes = models.TextField(blank=True, null=True)

    def clean(self):
        # Validate that the stream belongs to the same university
        if self.stream and self.stream.university != self.university:
            raise ValidationError(f"The stream '{self.stream}' must belong to the same university as the batch.")
        
        # Validate that a contract exists for this university/program/stream/year combination
        if self.university and self.program and self.stream and self.start_year:
            contract_exists = Contract.objects.filter(
                university=self.university,
                stream_pricing__program=self.program,
                stream_pricing__stream=self.stream,
                stream_pricing__year=self.start_year,
                start_year__lte=self.start_year,
                end_year__gte=self.start_year
            ).exists()
            
            if not contract_exists:
                raise ValidationError(
                    f"No contract found for university '{self.university.name}', program '{self.program.name}', and stream '{self.stream.name}' for year {self.start_year}. "
                    "Please create a contract first before creating a batch."
                )
        
        # Validate that a batch with the same university, stream, and start_year doesn't already exist
        if self.university and self.stream and self.start_year:
            existing_batch = Batch.objects.filter(
                university=self.university,
                stream=self.stream,
                start_year=self.start_year
            )
            # Exclude current instance if updating
            if self.pk:
                existing_batch = existing_batch.exclude(pk=self.pk)
            
            if existing_batch.exists():
                raise ValidationError(
                    f"A batch already exists for university '{self.university.name}', "
                    f"stream '{self.stream.name}', and year {self.start_year}. "
                    "Please use a different year or stream."
                )

    def get_contract(self):
        """Get the contract for this batch's university, program, stream, and year"""
        try:
            # If program is not set, return None (legacy batches)
            if not self.program or not self.university or not self.stream or not self.start_year:
                return None
                
            contracts = Contract.objects.filter(
                university=self.university,
                stream_pricing__program=self.program,
                stream_pricing__stream=self.stream,
                stream_pricing__year=self.start_year,
                start_year__lte=self.start_year,
                end_year__gte=self.start_year
            ).distinct()
            
            if contracts.exists():
                # If multiple contracts exist, return the most recent one
                return contracts.order_by('-created_at').first()
            return None
        except Exception:
            return None

    def get_cost_per_student(self):
        """Returns the cost per student from contract's stream pricing"""
        contract = self.get_contract()
        if contract:
            pricing = contract.get_stream_pricing(self.stream, self.start_year, self.program)
            if pricing:
                return pricing.cost_per_student
        return 0

    def get_tax_rate(self):
        """Returns the tax rate from contract's stream pricing"""
        contract = self.get_contract()
        if contract:
            pricing = contract.get_stream_pricing(self.stream, self.start_year, self.program)
            if pricing:
                return pricing.tax_rate
        return None

    def get_oem_transfer_price(self):
        """Returns the OEM transfer price from contract's stream pricing"""
        contract = self.get_contract()
        if contract:
            pricing = contract.get_stream_pricing(self.stream, self.start_year, self.program)
            if pricing:
                return pricing.oem_transfer_price
        return 0

    def __str__(self):
        return f'Batch {self.name} ({self.start_year}-{self.end_year}) for {self.university.name} - {self.stream.name}'


class BatchSnapshot(BaseModel):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='snapshots')
    billing = models.ForeignKey('Billing', on_delete=models.CASCADE, related_name='batch_snapshots', null=True, blank=True)
    number_of_students = models.PositiveIntegerField()
    cost_per_student = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    oem_transfer_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0.00,
        help_text="OEM transfer price at the time of snapshot"
    )
    status = models.CharField(max_length=20, choices=[
        ('planned', 'Planned'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ], default='planned')

    def __str__(self):
        return (
            f'Batch: {self.batch.name}\n'
            f'Students: {self.number_of_students}\n'
            f'Cost/Student: ₹{self.cost_per_student:,.2f}\n'
            f'Tax Rate: {self.tax_rate}%\n'
            f'OEM Price: ₹{self.oem_transfer_price:,.2f}'
            f'\n\n'
        )


class Billing(BaseModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paid', 'Paid'),
        ('archived', 'Archived'),
    ]

    name = models.CharField(max_length=255)
    batches = models.ManyToManyField(Batch, related_name='billings')
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_payments = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_oem_transfer_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        skip_update = kwargs.pop('skip_update', False)
        super().save(*args, **kwargs)
        # Update totals after save
        if not skip_update:
            self.update_totals()

    def archive(self):
        """Archive the billing"""
        if self.status == 'draft':
            raise ValidationError("Cannot archive a draft billing. Publish it first.")
        if self.status == 'archived':
            raise ValidationError("Billing is already archived.")
        
        # Check if all invoices are paid
        unpaid_invoices = self.invoices.exclude(status='paid')
        if unpaid_invoices.exists():
            raise ValidationError("Cannot archive billing with unpaid invoices.")
        
        with transaction.atomic():
            self.status = 'archived'
            self.save(skip_update=True)

    def publish(self):
        """Publish the billing by setting it to active and creating snapshots"""
        if self.status != 'draft':
            raise ValidationError("Only draft billings can be published")

        if not self.batches.exists():
            raise ValidationError("Cannot publish billing without any batches")

        with transaction.atomic():
            # Clear any existing snapshots
            self.batch_snapshots.all().delete()
            
            # Create new snapshots for each batch
            for batch in self.batches.all():
                self.add_batch_snapshot(batch)
            
            # Set status to active
            self.status = 'active'
            self.save(skip_update=True)
            
            # Update totals
            self.update_totals()

    def can_modify_batches(self):
        """Check if batches can be modified based on status"""
        return self.status == 'draft'

    def update_totals(self):
        """Update all total fields based on current data"""
        from decimal import Decimal
        
        # Calculate total amount from batch snapshots (including tax)
        total = Decimal('0')
        for snapshot in self.batch_snapshots.all():
            tax_rate = snapshot.tax_rate if snapshot.tax_rate is not None else Decimal('0')
            total += snapshot.number_of_students * snapshot.cost_per_student * (Decimal('1') + tax_rate/Decimal('100'))
        self.total_amount = total

        # Calculate total payments from invoices and payments
        total_paid = sum(
            payment.amount 
            for invoice in self.invoices.all()
            for payment in invoice.payments.filter(status='completed')
        )
        self.total_payments = total_paid

        # Calculate balance due
        self.balance_due = self.total_amount - self.total_payments

        # Calculate OEM transfer amount (including tax)
        oem_total = Decimal('0')
        for snapshot in self.batch_snapshots.all():
            tax_rate = snapshot.tax_rate if snapshot.tax_rate is not None else Decimal('0')
            oem_total += snapshot.number_of_students * snapshot.oem_transfer_price * (Decimal('1') + tax_rate/Decimal('100'))
        self.total_oem_transfer_amount = oem_total

        # Save without triggering update_totals again
        self.save(skip_update=True)

    def add_batch_snapshot(self, batch):
        """Create a snapshot of the batch's current state"""
        # Get pricing information safely
        tax_rate_obj = batch.get_tax_rate()
        tax_rate = tax_rate_obj.rate if tax_rate_obj else 0.00
        
        cost_per_student = batch.get_cost_per_student()
        if cost_per_student is None:
            cost_per_student = 0.00
            
        oem_transfer_price = batch.get_oem_transfer_price()
        if oem_transfer_price is None:
            oem_transfer_price = 0.00
        
        snapshot = BatchSnapshot.objects.create(
            batch=batch,
            billing=self,
            number_of_students=batch.number_of_students,
            cost_per_student=cost_per_student,
            tax_rate=tax_rate,
            oem_transfer_price=oem_transfer_price,
            status=batch.status
        )
        self.update_totals()
        return snapshot


class Invoice(BaseModel):
    name = models.CharField(max_length=255, default="Invoice")
    billing = models.ForeignKey(Billing, on_delete=models.CASCADE, related_name='invoices')
    issue_date = models.DateField()
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    proforma_invoice = models.FileField(upload_to='invoices/proforma/', blank=True, null=True)
    actual_invoice = models.FileField(upload_to='invoices/actual/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('unpaid', 'Unpaid'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
    ], default='unpaid')
    notes = models.TextField(blank=True, null=True)

    def update_status(self):
        """Update invoice status based on payments and TDS"""
        from decimal import Decimal
        
        # Only access relationships if invoice has a primary key (is saved)
        total_tds = self.get_total_tds() if self.pk else Decimal('0.00')
        
        # Invoice is considered paid if: amount_paid + TDS >= invoice amount
        # Because TDS is deducted at source, the university pays the full amount,
        # but we only receive the net amount (amount - TDS)
        total_paid_plus_tds = Decimal(str(self.amount_paid)) + total_tds
        
        if total_paid_plus_tds >= Decimal(str(self.amount)):
            self.status = 'paid'
        elif self.amount_paid > 0 or total_tds > 0:
            # Partially paid if there's any payment or TDS
            self.status = 'partially_paid'
        else:
            self.status = 'unpaid'

    def save(self, *args, **kwargs):
        # Skip status update flag (used internally to prevent recursion)
        skip_update = kwargs.pop('skip_update', False)
        
        # Save first to ensure we have a primary key
        super().save(*args, **kwargs)
        
        # Update status after save (now we have pk and can access relationships)
        if not skip_update:
            old_status = self.status
            self.update_status()
            # Only save again if status changed
            if old_status != self.status and 'update_fields' not in kwargs:
                # Use update_fields to save only status, and skip update to prevent recursion
                # Note: skip_update is popped from kwargs, so we don't pass it to parent
                super().save(update_fields=['status'], skip_update=True)

    def get_oem(self):
        """Get OEM from the invoice's billing contract"""
        try:
            if self.billing and self.billing.batches.exists():
                # Try to get OEM from any batch's contract
                for batch in self.billing.batches.all():
                    contract = batch.get_contract() if batch else None
                    if contract and contract.oem:
                        return contract.oem
        except Exception:
            pass
        return None
    
    def get_oem_transfer_amount(self):
        """Calculate the OEM transfer amount for this invoice (proportional to invoice amount)"""
        from decimal import Decimal
        if not self.billing or self.billing.total_amount == 0:
            return Decimal('0.00')
        
        # Calculate proportion: invoice_amount / billing_total_amount
        proportion = Decimal(str(self.amount)) / Decimal(str(self.billing.total_amount))
        # Multiply by total OEM transfer amount
        oem_transfer = proportion * Decimal(str(self.billing.total_oem_transfer_amount))
        return oem_transfer.quantize(Decimal('0.01'))
    
    def get_oem_transfer_paid(self):
        """Get total OEM payments made for this invoice"""
        from decimal import Decimal
        # Only access relationship if invoice has a primary key (is saved)
        if not self.pk:
            return Decimal('0.00')
        return sum(
            Decimal(str(payment.amount)) 
            for payment in self.oem_payments.filter(status='completed')
        )
    
    def get_oem_transfer_remaining(self):
        """Get remaining OEM transfer amount for this invoice"""
        return self.get_oem_transfer_amount() - self.get_oem_transfer_paid()
    
    def get_total_tds(self):
        """Get total TDS amount for this invoice"""
        from decimal import Decimal
        # Only access relationship if invoice has a primary key (is saved)
        if not self.pk:
            return Decimal('0.00')
        return sum(Decimal(str(tds.amount)) for tds in self.tds_entries.all())
    
    def get_net_invoice_amount(self):
        """
        Get net invoice amount that will actually hit our account.
        TDS is deducted at source by the university and paid directly to government,
        so it never reaches our account.
        Net Amount = Invoice Amount - Total TDS
        """
        from decimal import Decimal
        return Decimal(str(self.amount)) - self.get_total_tds()
    
    def get_net_amount_received(self):
        """
        Get net amount actually received in our account.
        
        When TDS is deducted at source by the university:
        - University pays the full invoice amount
        - TDS is deducted at source and paid directly to government
        - We only receive: (Invoice Amount - TDS) in our account
        
        Since amount_paid represents what actually hit our account (after TDS deduction),
        net_amount_received = amount_paid
        
        Note: amount_paid tracks the actual money received in our bank account,
        which is already net of TDS if TDS was deducted at source.
        """
        from decimal import Decimal
        # amount_paid already represents what we received (after TDS deduction)
        # So net_amount_received is simply the amount_paid
        return Decimal(str(self.amount_paid))
    
    def get_net_remaining_amount(self):
        """
        Get remaining net amount to be received.
        This is what's still outstanding after accounting for TDS deduction.
        Net Remaining = Net Invoice Amount - Net Amount Received
        """
        return self.get_net_invoice_amount() - self.get_net_amount_received()
    
    def __str__(self):
        return self.name


class InvoiceOEMPayment(BaseModel):
    """Track OEM payments at invoice level - allows clearing individual invoices"""
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('cheque', 'Cheque'),
        ('cash', 'Cash'),
        ('other', 'Other'),
    ]
    
    # Core fields
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='oem_payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Dates
    payment_date = models.DateField()
    processed_date = models.DateTimeField(null=True, blank=True)
    
    # Reference information
    reference_number = models.CharField(max_length=255, blank=True, null=True, help_text="Transaction reference number")
    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Link to main OEMPayment for ledger tracking
    oem_payment = models.ForeignKey(
        'OEMPayment', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='invoice_oem_payments',
        help_text="Linked OEMPayment entry for ledger tracking"
    )
    
    # Audit fields
    created_by = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='created_invoice_oem_payments')
    
    class Meta:
        ordering = ['-payment_date', '-created_at']
        indexes = [
            models.Index(fields=['invoice', 'payment_date']),
            models.Index(fields=['status', 'payment_date']),
        ]
    
    def clean(self):
        from decimal import Decimal
        
        # Validate invoice is paid before allowing OEM payment
        if self.invoice.status != 'paid':
            raise ValidationError(
                f"OEM payment can only be made after invoice is paid. "
                f"Current invoice status: {self.invoice.status}"
            )
        
        # Validate amount doesn't exceed remaining OEM transfer amount
        remaining = self.invoice.get_oem_transfer_remaining()
        if Decimal(str(self.amount)) > remaining:
            raise ValidationError(
                f"OEM payment amount ({self.amount}) exceeds remaining OEM transfer amount ({remaining}). "
                f"Total OEM transfer for invoice: {self.invoice.get_oem_transfer_amount()}, "
                f"Already paid: {self.invoice.get_oem_transfer_paid()}"
            )
        
        # Validate amount is positive
        if Decimal(str(self.amount)) <= 0:
            raise ValidationError("OEM payment amount must be greater than zero")
    
    def __str__(self):
        return f'Invoice OEM Payment - {self.invoice.name} - ₹{self.amount} - {self.payment_date}'


class InvoiceTDS(BaseModel):
    """
    Track TDS (Tax Deducted at Source) entries at invoice level.
    
    IMPORTANT: TDS amount NEVER hits our account. The university deducts TDS
    at source and pays it directly to the government on our behalf. We can
    only claim TDS back if:
    - Our organization has no tax to be paid, OR
    - There is a tax rebate
    
    The TDS is deducted BEFORE payment reaches us, so the net amount received
    in our account is: Invoice Amount - TDS Amount
    """
    
    TDS_CERTIFICATE_TYPE_CHOICES = [
        ('form_16a', 'Form 16A'),
        ('form_16b', 'Form 16B'),
        ('certificate', 'TDS Certificate'),
        ('other', 'Other'),
    ]
    
    # Core fields
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='tds_entries')
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        help_text="TDS amount deducted at source. IMPORTANT: This amount NEVER hits our account. "
                  "University deducts TDS and pays it directly to government on our behalf. "
                  "We can claim it back only if we have no tax liability or tax rebate."
    )
    tds_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        help_text="TDS rate percentage (e.g., 10.00 for 10%)"
    )
    deduction_date = models.DateField(help_text="Date when TDS was deducted at source")
    
    # Reference information
    reference_number = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="TDS certificate or form number"
    )
    certificate_type = models.CharField(
        max_length=20, 
        choices=TDS_CERTIFICATE_TYPE_CHOICES, 
        blank=True, 
        null=True,
        help_text="Type of TDS certificate"
    )
    certificate_document = models.FileField(
        upload_to='invoices/tds/', 
        blank=True, 
        null=True,
        help_text="TDS certificate document"
    )
    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-deduction_date', '-created_at']
        indexes = [
            models.Index(fields=['invoice', 'deduction_date']),
        ]
        verbose_name = 'Invoice TDS'
        verbose_name_plural = 'Invoice TDS Entries'
    
    def clean(self):
        from decimal import Decimal
        
        # Validate TDS amount is positive
        if Decimal(str(self.amount)) <= 0:
            raise ValidationError("TDS amount must be greater than zero")
        
        # Validate TDS rate is positive
        if Decimal(str(self.tds_rate)) <= 0:
            raise ValidationError("TDS rate must be greater than zero")
        
        # Validate TDS amount doesn't exceed invoice amount
        if Decimal(str(self.amount)) > Decimal(str(self.invoice.amount)):
            raise ValidationError(
                f"TDS amount ({self.amount}) cannot exceed invoice amount ({self.invoice.amount})"
            )
    
    def __str__(self):
        return f'TDS - {self.invoice.name} - ₹{self.amount} - {self.deduction_date}'


class Payment(BaseModel):
    name = models.CharField(max_length=255, default="Payment")
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    transaction_reference = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def clean(self):
        # Validate that payment amount doesn't exceed remaining invoice amount
        if self.invoice:
            from decimal import Decimal
            
            # Refresh invoice from database to get latest amount_paid
            if self.invoice.pk:
                self.invoice.refresh_from_db()
            
            # Get current remaining amount
            remaining_amount = Decimal(str(self.invoice.amount)) - Decimal(str(self.invoice.amount_paid))
            
            # If this is an update, we need to account for the old payment amount
            if self.pk:
                try:
                    # Get the old payment from database (not from self, which has new values)
                    old_payment = Payment.objects.get(pk=self.pk)
                    # If the old payment was completed, it's already included in amount_paid
                    # So we need to add it back to the remaining amount for validation
                    if old_payment.status == 'completed':
                        remaining_amount += Decimal(str(old_payment.amount))
                except Payment.DoesNotExist:
                    # Payment doesn't exist yet, treat as new
                    pass
            
            # Only validate if the payment is or will be completed
            # If status is not completed, we don't need to check the amount limit
            if self.status == 'completed':
                if Decimal(str(self.amount)) > remaining_amount:
                    raise ValidationError(
                        f"Payment amount ({self.amount}) exceeds remaining invoice amount ({remaining_amount}). "
                        f"Invoice amount: {self.invoice.amount}, Amount paid: {self.invoice.amount_paid}"
                    )

    def __str__(self):
        return self.name

class PaymentDocument(BaseModel):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='payments/')
    description = models.CharField(max_length=255, blank=True, null=True)
    uploaded_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'Document for Payment {self.payment.id}'

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('provider_poc', 'Provider POC'),
        ('university_poc', 'University POC'),
        ('agent', 'Agent'),
        ('staff', 'Staff'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.username

    # Add any custom methods for role-based actions or permissions here
    def is_provider_poc(self):
        return self.role == 'provider_poc'

    def is_university_poc(self):
        return self.role == 'university_poc'

    def is_agent(self):
        return self.role == 'agent'

    def is_staff_user(self):
        return self.role == 'staff'

    def get_assigned_universities(self):
        """Get universities assigned to this staff user"""
        if self.is_staff_user():
            return University.objects.filter(staff_assignments__staff=self)
        return University.objects.none()


class StaffUniversityAssignment(BaseModel):
    """Model to assign staff users to multiple universities"""
    staff = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='staff_assignments')
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='staff_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='staff_assignments_created')

    class Meta:
        unique_together = ('staff', 'university')
        verbose_name = 'Staff University Assignment'
        verbose_name_plural = 'Staff University Assignments'

    def __str__(self):
        return f'{self.staff.username} - {self.university.name}'

    def clean(self):
        if self.staff and not self.staff.is_staff_user():
            raise ValidationError("Only staff users can be assigned to universities.")


class PaymentSchedule(BaseModel):
    FREQUENCY_CHOICES = [
        ('one_time', 'One Time'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payment_schedules')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    reminder_days = models.PositiveIntegerField(
        default=7,
        help_text="Days before due date to send reminder"
    )
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ], default='pending')

    def get_reminder_recipients(self):
        """Returns list of reminder recipients"""
        # Fallback to OEM contact if no custom recipients
        return [self.invoice.billing.batches.first().contract.oem.contact_email]

    def __str__(self):
        return f'Payment Schedule for Invoice {self.invoice.id} - Due: {self.due_date}'

    def save(self, *args, **kwargs):
        if self.due_date < date.today():
            self.status = 'overdue'
        super().save(*args, **kwargs)

class PaymentScheduleRecipient(BaseModel):
    payment_schedule = models.ForeignKey(PaymentSchedule, on_delete=models.CASCADE, related_name='recipients')
    email = models.EmailField()

    def __str__(self):
        return f'Recipient {self.email} for Schedule {self.payment_schedule.id}'


class PaymentReminder(BaseModel):
    REMINDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    payment_schedule = models.ForeignKey(PaymentSchedule, on_delete=models.CASCADE, related_name='reminders')
    scheduled_date = models.DateField()
    status = models.CharField(max_length=20, choices=REMINDER_STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Reminder for {self.payment_schedule} on {self.scheduled_date}'

class ChannelPartner(BaseModel):
    name = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    poc = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='channel_partner_pocs')
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Default commission rate in percentage")
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], default='active')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    def clean(self):
        if self.poc and not (self.poc.is_provider_poc() or self.poc.is_superuser):
            raise ValidationError("The POC must be either a 'provider_poc' or a 'superuser'.")

class ChannelPartnerProgram(BaseModel):
    channel_partner = models.ForeignKey(ChannelPartner, on_delete=models.CASCADE, related_name='programs')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='channel_partners')
    transfer_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Partner's transfer price for this program")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Commission rate override for this program")
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('channel_partner', 'program')

    def __str__(self):
        return f'{self.channel_partner.name} - {self.program.name}'

    def get_effective_commission_rate(self):
        """Returns the effective commission rate (override or partner's default)"""
        return self.commission_rate if self.commission_rate is not None else self.channel_partner.commission_rate

class Student(BaseModel):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    enrollment_source = models.CharField(max_length=20, choices=[
        ('direct', 'Direct'),
        ('channel_partner', 'Channel Partner'),
        ('university', 'University'),
    ], default='direct')
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ], default='active')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.name} ({self.email})'

    class Meta:
        ordering = ['name']

class ProgramBatch(BaseModel):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='program_batches')
    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    number_of_students = models.PositiveIntegerField()
    cost_per_student = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('planned', 'Planned'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ], default='planned')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.name} ({self.program.name})'

    class Meta:
        ordering = ['-start_date']

class ChannelPartnerStudent(BaseModel):
    channel_partner = models.ForeignKey(ChannelPartner, on_delete=models.CASCADE, related_name='students')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='channel_partner_students', null=True, blank=True)
    program_batch = models.ForeignKey(ProgramBatch, on_delete=models.CASCADE, related_name='channel_partner_students', null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='channel_partner_enrollments')
    enrollment_date = models.DateField()
    transfer_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Actual transfer price for this student")
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Commission amount for this student")
    status = models.CharField(max_length=20, choices=[
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ], default='enrolled')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.student.name} ({self.channel_partner.name})'

    def clean(self):
        if not (self.batch or self.program_batch):
            raise ValidationError("Either batch or program_batch must be specified")
        if self.batch and self.program_batch:
            raise ValidationError("Cannot specify both batch and program_batch")

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            # Get the channel partner program for this batch's program
            try:
                if self.batch:
                    # Use batch's program directly if available
                    if self.batch.program:
                        program = self.batch.program
                    else:
                        # Fallback to contract's programs for legacy batches
                        contract = self.batch.get_contract()
                        if contract:
                            program = contract.programs.first()
                        else:
                            raise ValidationError("Cannot determine program for this batch")
                else:
                    program = self.program_batch.program
                
                if not program:
                    raise ValidationError("No program available for pricing calculation")
                
                partner_program = ChannelPartnerProgram.objects.get(
                    channel_partner=self.channel_partner,
                    program=program
                )
                self.transfer_price = partner_program.transfer_price
                self.commission_amount = self.transfer_price * (partner_program.get_effective_commission_rate() / 100)
            except (ChannelPartnerProgram.DoesNotExist, AttributeError, ValidationError) as e:
                raise ValidationError(f"No pricing found for this program and channel partner combination: {str(e)}")
            
            # Update student's enrollment source
            self.student.enrollment_source = 'channel_partner'
            self.student.save()
            
        super().save(*args, **kwargs)


class OEMPayment(BaseModel):
    """Model to track payments made to OEMs - creating a comprehensive ledger"""
    
    PAYMENT_TYPE_CHOICES = [
        ('oem_transfer', 'OEM Transfer Payment'),
        ('commission', 'Commission Payment'),
        ('refund', 'Refund'),
        ('adjustment', 'Adjustment'),
        ('other', 'Other'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('cheque', 'Cheque'),
        ('cash', 'Cash'),
        ('other', 'Other'),
    ]
    
    # Core payment details
    oem = models.ForeignKey(OEM, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Payment dates
    payment_date = models.DateField()
    processed_date = models.DateTimeField(null=True, blank=True)
    
    # Reference information
    reference_number = models.CharField(max_length=255, blank=True, null=True, help_text="Transaction reference number")
    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Related entities (optional - for tracking what triggered this payment)
    billing = models.ForeignKey(Billing, on_delete=models.SET_NULL, null=True, blank=True, related_name='oem_payments')
    invoice = models.ForeignKey('Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_oem_payments', help_text="Invoice this OEM payment is for")
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name='oem_payments')
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True, related_name='oem_payments')
    
    # Financial tracking
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Tax amount included in payment")
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Net amount after tax")
    
    # Audit fields
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_oem_payments')
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_oem_payments')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-payment_date', '-created_at']
        indexes = [
            models.Index(fields=['oem', 'payment_date']),
            models.Index(fields=['status', 'payment_date']),
            models.Index(fields=['payment_type', 'payment_date']),
        ]
    
    def __str__(self):
        return f'OEM Payment - {self.oem.name} - ₹{self.amount} - {self.payment_date}'
    
    def clean(self):
        super().clean()
        from decimal import Decimal
        # Calculate net amount if not provided
        if not self.net_amount:
            self.net_amount = Decimal(str(self.amount)) - Decimal(str(self.tax_amount))
        
        # Validate payment amount
        if Decimal(str(self.amount)) <= 0:
            raise ValidationError("Payment amount must be greater than zero")
        
        # Validate tax amount doesn't exceed payment amount
        if Decimal(str(self.tax_amount)) > Decimal(str(self.amount)):
            raise ValidationError("Tax amount cannot exceed payment amount")
    
    def save(self, *args, **kwargs):
        # Auto-calculate net amount if not set
        if not self.net_amount:
            from decimal import Decimal
            self.net_amount = Decimal(str(self.amount)) - Decimal(str(self.tax_amount))
        super().save(*args, **kwargs)
    
    def approve(self, approved_by_user):
        """Approve the payment"""
        from django.utils import timezone
        
        if self.status != 'pending':
            raise ValidationError("Only pending payments can be approved")
        
        if not approved_by_user.is_superuser:
            raise ValidationError("Only superusers can approve payments")
        
        self.status = 'processing'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save(update_fields=['status', 'approved_by', 'approved_at'])
    
    def mark_completed(self):
        """Mark payment as completed"""
        if self.status not in ['pending', 'processing']:
            raise ValidationError("Only pending or processing payments can be marked as completed")
        
        from django.utils import timezone
        self.status = 'completed'
        self.processed_date = timezone.now()
        self.save(update_fields=['status', 'processed_date'])
    
    def mark_failed(self, reason=None):
        """Mark payment as failed"""
        if self.status not in ['pending', 'processing']:
            raise ValidationError("Only pending or processing payments can be marked as failed")
        
        self.status = 'failed'
        if reason:
            self.notes = f"{self.notes or ''}\nFailed: {reason}".strip()
        self.save(update_fields=['status', 'notes'])


class PaymentDocument(BaseModel):
    """Documents related to OEM payments"""
    payment = models.ForeignKey(OEMPayment, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='oem_payments/documents/')
    document_type = models.CharField(max_length=50, choices=[
        ('receipt', 'Receipt'),
        ('invoice', 'Invoice'),
        ('bank_statement', 'Bank Statement'),
        ('approval', 'Approval Document'),
        ('other', 'Other'),
    ], default='other')
    description = models.CharField(max_length=255, blank=True, null=True)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f'Document for Payment {self.payment.id} - {self.document_type}'


class PaymentLedger(BaseModel):
    """Comprehensive ledger view of all financial transactions"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('oem_payment', 'OEM Payment'),
        ('commission_payment', 'Commission Payment'),
        ('refund', 'Refund'),
        ('adjustment', 'Adjustment'),
    ]
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateField()
    description = models.TextField()
    
    # Related entities
    oem = models.ForeignKey(OEM, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries')
    university = models.ForeignKey(University, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries')
    billing = models.ForeignKey(Billing, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries')
    payment = models.ForeignKey(OEMPayment, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries')
    invoice = models.ForeignKey('Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries', help_text="Invoice this ledger entry is related to")
    
    # Balance tracking
    running_balance = models.DecimalField(max_digits=12, decimal_places=2, help_text="Running balance after this transaction")
    
    # Reference
    reference_number = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['transaction_type', 'transaction_date']),
            models.Index(fields=['oem', 'transaction_date']),
            models.Index(fields=['university', 'transaction_date']),
        ]
    
    def __str__(self):
        return f'{self.transaction_type.title()} - ₹{self.amount} - {self.transaction_date}'
    
    @classmethod
    def recalculate_running_balances(cls, university_id=None):
        """Recalculate all running balances in chronological order"""
        from decimal import Decimal
        
        # Get all entries ordered by transaction date and creation time
        queryset = cls.objects.all()
        if university_id:
            queryset = queryset.filter(university_id=university_id)
        
        entries = queryset.order_by('transaction_date', 'created_at')
        
        running_balance = Decimal('0.00')
        updated_count = 0
        
        for entry in entries:
            # Calculate new balance based on transaction type
            if entry.transaction_type in ['income', 'refund']:
                running_balance += entry.amount
            else:  # expense, oem_payment, commission_payment, adjustment
                running_balance -= entry.amount
            
            # Update the entry with correct running balance
            if entry.running_balance != running_balance:
                entry.running_balance = running_balance
                entry.save(update_fields=['running_balance'])
                updated_count += 1
        
        return updated_count

    @classmethod
    def create_ledger_entry(cls, transaction_type, amount, transaction_date, description, 
                          oem=None, university=None, billing=None, payment=None, 
                          invoice=None,
                          reference_number=None, notes=None):
        """Create a new ledger entry and update running balance"""
        from django.db import transaction
        
        with transaction.atomic():
            # Create the entry first with temporary balance
            entry = cls.objects.create(
                transaction_type=transaction_type,
                amount=amount,
                transaction_date=transaction_date,
                description=description,
                oem=oem,
                university=university,
                billing=billing,
                payment=payment,
                invoice=invoice,
                reference_number=reference_number,
                notes=notes,
                running_balance=Decimal('0.00')  # Temporary value
            )
            
            # Ensure the entry is saved and committed
            entry.refresh_from_db()
            
            # Recalculate all running balances to ensure accuracy
            # Note: This recalculates all entries for correctness, but may need optimization
            # for production with large datasets. Consider:
            # 1. Calculating only the current entry's balance based on the last entry
            # 2. Adding a periodic background job to recalculate all entries
            # 3. Only doing full recalculation when needed (backdated entries)
            cls.recalculate_running_balances(university_id=None)
            
            # Refresh the entry to get the correct balance
            entry.refresh_from_db()
            
            return entry



