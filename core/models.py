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

    name = models.CharField(max_length=100, unique=True)
    streams = models.ManyToManyField(Stream, related_name='contracts')
    cost_per_student = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.ForeignKey(TaxRate, on_delete=models.SET_DEFAULT, default=0, related_name='contracts')
    oem = models.ForeignKey(OEM, on_delete=models.CASCADE, related_name='contracts')
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='contracts')
    oem_transfer_price = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=CONTRACT_STATUS_CHOICES, default='active')
    programs = models.ManyToManyField(Program, through='ContractProgram', related_name='contracts')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Contract {self.name} ({self.university.name} - {self.oem.name})'

    def clean(self):
        super().clean()
        if self.pk and not self.contract_files.exists():
            raise ValidationError("Contract must have at least one file.")


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
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='batches')
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='batches')
    name = models.CharField(max_length=255)
    start_year = models.PositiveIntegerField(help_text='Start Year')
    end_year = models.PositiveIntegerField(help_text='End Year')
    number_of_students = models.PositiveIntegerField()
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    cost_per_student_override = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Override contract's cost per student for this batch"
    )
    oem_transfer_price_override = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Override contract's OEM transfer price for this batch"
    )
    tax_rate_override = models.ForeignKey(
        TaxRate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='batch_overrides',
        help_text="Override contract's tax rate for this batch"
    )
    status = models.CharField(max_length=20, choices=[
        ('planned', 'Planned'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ], default='planned')
    notes = models.TextField(blank=True, null=True)

    def clean(self):
        # Validate that the stream is part of the contract's streams
        if not self.contract.streams.filter(id=self.stream.id).exists():
            raise ValidationError(f"The stream '{self.stream}' is not part of the contract '{self.contract}'.")

    def get_cost_per_student(self):
        """Returns the effective cost per student (override or contract's value)"""
        return self.cost_per_student_override if self.cost_per_student_override is not None else self.contract.cost_per_student

    def get_tax_rate(self):
        """Returns the effective tax rate (override or contract's value)"""
        return self.tax_rate_override if self.tax_rate_override is not None else self.contract.tax_rate

    def get_oem_transfer_price(self):
        """Returns the effective OEM transfer price (override or contract's value)"""
        return self.oem_transfer_price_override if self.oem_transfer_price_override is not None else self.contract.oem_transfer_price

    def __str__(self):
        return f'Batch {self.name} ({self.start_year}-{self.end_year}) for {self.contract}'


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
        # Calculate total amount from batch snapshots (including tax)
        total = sum(
            snapshot.number_of_students * snapshot.cost_per_student * (1 + snapshot.tax_rate/100)
            for snapshot in self.batch_snapshots.all()
        )
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
        self.total_oem_transfer_amount = sum(
            snapshot.number_of_students * snapshot.oem_transfer_price * (1 + snapshot.tax_rate/100)
            for snapshot in self.batch_snapshots.all()
        )

        # Save without triggering update_totals again
        self.save(skip_update=True)

    def add_batch_snapshot(self, batch):
        """Create a snapshot of the batch's current state"""
        snapshot = BatchSnapshot.objects.create(
            batch=batch,
            billing=self,
            number_of_students=batch.number_of_students,
            cost_per_student=batch.get_cost_per_student(),
            tax_rate=batch.get_tax_rate().rate,
            oem_transfer_price=batch.get_oem_transfer_price(),
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
        """Update invoice status based on payments"""
        if self.amount_paid >= self.amount:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partially_paid'
        else:
            self.status = 'unpaid'

    def save(self, *args, **kwargs):
        self.update_status()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



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
            remaining_amount = self.invoice.amount - self.invoice.amount_paid
            if self.amount > remaining_amount:
                raise ValidationError(f"Payment amount ({self.amount}) exceeds remaining invoice amount ({remaining_amount})")

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
                    program = self.batch.contract.programs.first()
                else:
                    program = self.program_batch.program
                
                partner_program = ChannelPartnerProgram.objects.get(
                    channel_partner=self.channel_partner,
                    program=program
                )
                self.transfer_price = partner_program.transfer_price
                self.commission_amount = self.transfer_price * (partner_program.get_effective_commission_rate() / 100)
            except ChannelPartnerProgram.DoesNotExist:
                raise ValidationError("No pricing found for this program and channel partner combination")
            
            # Update student's enrollment source
            self.student.enrollment_source = 'channel_partner'
            self.student.save()
            
        super().save(*args, **kwargs)
