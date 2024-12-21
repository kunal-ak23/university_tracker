# core/signals.py
import logging

from django.db import transaction, models
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from core.logger_service import get_logger
from core.models import ContractFile, Billing, Payment, Invoice, Contract
from core.services import PaymentScheduleService

logger = get_logger()

@receiver(post_save, sender=ContractFile)
@receiver(post_delete, sender=ContractFile)
def validate_contract_files(sender, instance, **kwargs):
    contract = instance.contract
    if not contract.contract_files.exists():
        raise ValidationError("Contract must have at least one contract file.")


updating_instance = False
@receiver(post_save, sender=Billing)
def calculate_total_amount(sender, instance, **kwargs):
    def update_amounts():
        global updating_instance
        if updating_instance:
            return
        updating_instance = True
        try:
            total_amount = 0
            # Clear previous batch_snapshots
            instance.batch_snapshots.clear()
            
            for batch in instance.batches.all():
                # Get effective cost per student and tax rate for this batch
                cost_per_student = batch.get_cost_per_student()
                tax_rate = batch.get_tax_rate().rate / 100  # Convert percentage to decimal
                
                # Calculate amount for this batch
                batch_amount = batch.number_of_students * cost_per_student * (1 + tax_rate)
                total_amount += batch_amount
                
                # Create snapshot
                instance.batch_snapshots.add(instance.add_batch_snapshot(batch))

            if instance.batches.exists():
                instance.total_amount = total_amount
                instance.balance_due = instance.total_amount - instance.total_payments
                instance.save()
        finally:
            updating_instance = False

    # Ensure the update happens after the transaction completes
    transaction.on_commit(update_amounts)

@receiver(post_save, sender=Invoice)
def handle_invoice_save(sender, instance, created, **kwargs):
    is_new_invoice = created
    previous_actual_invoice = None

    # Check for previous actual invoice if this is an update
    if not is_new_invoice:
        previous_actual_invoice = Invoice.objects.get(pk=instance.pk).actual_invoice

    # If the actual invoice is uploaded and the invoice is paid, create a payment record
    if instance.actual_invoice and (is_new_invoice or not previous_actual_invoice) and instance.status == 'paid':
        with transaction.atomic():
            Payment.objects.create(
                billing=instance.billing,
                amount=instance.amount,
                payment_date=instance.issue_date,
                invoice=instance,
                payment_method='Invoice Payment',
                status='paid',
                notes='Payment created from actual invoice'
            )
            # Update the billing totals
            instance.billing.total_payments = instance.billing.payments.aggregate(total=models.Sum('amount'))['total'] or 0.00
            instance.billing.balance_due = instance.billing.total_amount - instance.billing.total_payments
            instance.billing.save()

@receiver(pre_save, sender=Contract)
def validate_courses_oem(sender, instance, **kwargs):
    if instance.pk:  # Ensure the instance is already saved
        logger.info(f"Validating programs for Contract ID: {instance.pk}")
        # filter duplicates and remove all programs that are not from the OEM
        logger.info(instance.oem)
        
        filtered_programs = instance.programs.filter(provider=instance.oem).distinct()
        if filtered_programs.count() != instance.programs.count():
            logger.warning(f"Some programs do not belong to OEM {instance.oem.name} and will be removed.")
            instance.programs.set(filtered_programs)

@receiver(post_save, sender=Payment)
def handle_payment_status_change(sender, instance, created, **kwargs):
    """Handle payment status changes and update related models"""
    if instance.status == 'completed':
        with transaction.atomic():
            # Update invoice status
            invoice = instance.invoice
            invoice.refresh_from_db()  # Ensure we have the latest data
            invoice.update_status()
            invoice.save()

            # Update billing totals
            billing = instance.billing
            billing.refresh_from_db()
            completed_payments = billing.payments.filter(status='completed')
            billing.total_payments = completed_payments.aggregate(
                total=models.Sum('amount'))['total'] or 0.00
            billing.balance_due = billing.total_amount - billing.total_payments
            billing.save()

@receiver(post_save, sender=Invoice)
def create_payment_schedule(sender, instance, created, **kwargs):
    """Create payment schedule when invoice is created"""
    if created:
        # Get recipients from the contract's POC and OEM contact
        contract = instance.billing.batches.first().contract
        recipients = [
            contract.oem.contact_email,
            contract.oem.poc.email if contract.oem.poc else None
        ]
        # Filter out None values and create comma-separated string
        reminder_recipients = ','.join(filter(None, recipients))
        
        PaymentScheduleService.create_payment_schedule(
            invoice=instance,
            amount=instance.amount,
            due_date=instance.due_date,
            reminder_recipients=reminder_recipients
        )

