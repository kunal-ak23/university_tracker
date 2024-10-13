import logging

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
            # Use F() to avoid concurrency issues
            self.version = models.F('version') + 1
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

class Course(BaseModel):
    DURATION_UNIT_CHOICES = [
        ('Days', 'Days'),
        ('Months', 'Months'),
        ('Years', 'Years'),
    ]

    name = models.CharField(max_length=255)
    course_code = models.CharField(max_length=50, unique=True)
    provider = models.ForeignKey(OEM, on_delete=models.CASCADE, related_name='courses', help_text="Name of the OEM")
    duration = models.PositiveIntegerField(help_text='Duration')
    duration_unit = models.CharField(max_length=50, choices=DURATION_UNIT_CHOICES)
    description = models.TextField(blank=True, null=True)
    prerequisites = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('name', 'provider')

    def __str__(self):
        return f'{self.name} (Code: {self.course_code}, OEM: {self.provider.name})'


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
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=100, unique=True)
    streams = models.ManyToManyField(Stream, related_name='contracts')  # Updated to ManyToManyField
    cost_per_student = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.ForeignKey(TaxRate, on_delete=models.SET_DEFAULT, default=0, related_name='contracts')
    oem = models.ForeignKey(OEM, on_delete=models.CASCADE, related_name='contracts')  # Added OEM field
    oem_transfer_price = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=CONTRACT_STATUS_CHOICES, default='active')
    courses = models.ManyToManyField(Course, through='ContractCourse', related_name='contracts')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Contract {self.name}'


class ContractFile(BaseModel):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='contract_files')
    file_type = models.CharField(max_length=50)
    uploaded_by = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    file = models.FileField(upload_to='contracts/files/', null=False)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'File {self.file_type} for {self.contract.name}'

class ContractCourse(BaseModel):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='contract_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='contract_courses')

    def __str__(self):
        return f'{self.course.name} for {self.contract.name}'


class Batch(BaseModel):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='batches')
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='batches')  # Added stream field
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
        # Validate that the stream is part of the contract's streams
        if not self.contract.streams.filter(id=self.stream.id).exists():
            raise ValidationError(f"The stream '{self.stream}' is not part of the contract '{self.contract}'.")

    def __str__(self):
        return f'Batch {self.name} ({self.start_year}-{self.end_year}) for {self.contract}'


class BatchSnapshot(BaseModel):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='oeiginal_batch')
    number_of_students = models.PositiveIntegerField()
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    status = models.CharField(max_length=20, choices=[
        ('planned', 'Planned'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ], default='planned')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.batch.name} | students: {self.number_of_students}'


class Billing(BaseModel):
    name = models.CharField(max_length=255)
    batches = models.ManyToManyField(Batch, related_name='billings')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_payments = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)
    batch_snapshots = models.ManyToManyField(BatchSnapshot, related_name='snapshots', blank=True)

    def __str__(self):
        if self.batches.exists():
            return f'Billing for {self.name}'
        return 'Billing (no batches assigned yet)'

    def add_batch_snapshot(self, batch):
        return BatchSnapshot.objects.create(
            batch=batch,
            number_of_students=batch.number_of_students,
            start_date=batch.start_date,
            end_date=batch.end_date,
            status=batch.status,
            notes=batch.notes
        )


class Invoice(BaseModel):
    billing = models.ForeignKey(Billing, on_delete=models.CASCADE, related_name='invoices')
    issue_date = models.DateField()
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    proforma_invoice = models.FileField(upload_to='invoices/proforma/', blank=True, null=True)
    actual_invoice = models.FileField(upload_to='invoices/actual/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('unpaid', 'Unpaid'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
    ], default='unpaid')
    notes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        is_new_invoice = self.pk is None
        previous_actual_invoice = None

        # Check for previous actual invoice if this is an update
        if not is_new_invoice:
            previous_actual_invoice = Invoice.objects.get(pk=self.pk).actual_invoice

        super().save(*args, **kwargs)

        # If the actual invoice is uploaded and the invoice is paid, create a payment record
        if self.actual_invoice and (is_new_invoice or not previous_actual_invoice) and self.status == 'paid':
            with transaction.atomic():
                Payment.objects.create(
                    billing=self.billing,
                    amount=self.amount,
                    payment_date=self.issue_date,
                    invoice=self,
                    payment_method='Invoice Payment',
                    status='paid',
                    notes='Payment created from actual invoice'
                )
                # Update the billing totals
                self.billing.total_payments = self.billing.payments.aggregate(total=models.Sum('amount'))['total'] or 0.00
                self.billing.balance_due = self.billing.total_amount - self.billing.total_payments
                self.billing.save()

    def __str__(self):
        return f'Invoice {self.id} for {self.billing}'



class Payment(BaseModel):
    billing = models.ForeignKey(Billing, on_delete=models.CASCADE, related_name='payments')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('unpaid', 'Unpaid'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
    ], default='unpaid')
    transaction_reference = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='payments/', blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Recalculate total payments and balance due on the related billing
        self.billing.total_payments = self.billing.payments.aggregate(total=models.Sum('amount'))['total'] or 0.00
        self.billing.balance_due = self.billing.total_amount - self.billing.total_payments
        self.billing.save()

    def __str__(self):
        return f'Payment {self.id} for {self.billing}'

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('provider_poc', 'Provider POC'),
        ('university_poc', 'University POC'),
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