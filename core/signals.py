# core/signals.py
import logging

from django.db import transaction, models
from django.db.models.signals import post_save, post_delete, pre_save, m2m_changed
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


@receiver(m2m_changed, sender=Billing.batches.through)
def handle_billing_batches_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    """Handle changes to billing.batches M2M relationship"""
    if action == "pre_add" or action == "pre_remove" or action == "pre_clear":
        # Check if batches can be modified
        if not instance.can_modify_batches():
            raise ValidationError("Cannot modify batches on an active or archived billing")

    if action == "post_add" or action == "post_remove" or action == "post_clear":
        # Clear previous batch_snapshots if in draft state
        if instance.status == 'draft':
            instance.batch_snapshots.all().delete()
            
            # Create new snapshots for each batch
            for batch in instance.batches.all():
                instance.add_batch_snapshot(batch)

@receiver(post_save, sender=Invoice)
def handle_invoice_save(sender, instance, created, **kwargs):
    is_new_invoice = created
    previous_actual_invoice = None

    # Check for previous actual invoice if this is an update
    if not is_new_invoice:
        try:
            previous_invoice = Invoice.objects.get(pk=instance.pk)
            previous_actual_invoice = previous_invoice.actual_invoice
        except Invoice.DoesNotExist:
            pass

    # If the actual invoice is uploaded and the invoice is paid, create a payment record
    if instance.actual_invoice and (is_new_invoice or not previous_actual_invoice) and instance.status == 'paid':
        with transaction.atomic():
            Payment.objects.create(
                invoice=instance,
                amount=instance.amount,
                payment_date=instance.issue_date,
                payment_method='Invoice Payment',
                status='completed',
                notes='Payment created from actual invoice'
            )

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
            invoice.amount_paid = models.F('amount_paid') + instance.amount
            invoice.save()
            invoice.refresh_from_db()
            invoice.update_status()
            invoice.save()

            # Update billing totals
            billing = invoice.billing
            billing.refresh_from_db()
            billing.update_totals()

@receiver(post_save, sender=Invoice)
def create_payment_schedule(sender, instance, created, **kwargs):
    """Create payment schedule when invoice is created"""
    if created:
        try:
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
        except Exception as e:
            logger.error(f"Failed to create payment schedule: {str(e)}")

