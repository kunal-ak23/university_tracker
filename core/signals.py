# core/signals.py
import logging

from django.db import transaction, models
from django.db.models.signals import post_save, post_delete, pre_save, m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from decimal import Decimal

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
    if action not in ("post_add", "post_remove", "post_clear"):
        return

    try:
        billing = instance
        if not billing.can_modify_batches():
            raise ValidationError("Cannot modify batches on an active or archived billing")

        if action == "post_add" and pk_set:
            # Clear existing snapshots for these batches
            billing.batch_snapshots.filter(batch_id__in=pk_set).delete()
            
            # Create new snapshots
            for batch_id in pk_set:
                batch = model.objects.get(id=batch_id)
                billing.add_batch_snapshot(batch)
        
        elif action in ("post_remove", "post_clear"):
            # Remove snapshots for removed batches
            if pk_set:
                billing.batch_snapshots.filter(batch_id__in=pk_set).delete()
            else:  # post_clear
                billing.batch_snapshots.all().delete()
            
            billing.update_totals()

    except Exception as e:
        raise ValidationError(f"Error updating billing: {str(e)}")

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
def handle_payment_save(sender, instance, created, **kwargs):
    """Update invoice and billing totals when a payment is saved"""
    with transaction.atomic():
        # Get the old instance if it exists
        if not created:
            try:
                old_instance = Payment.objects.get(pk=instance.pk)
                old_status = old_instance.status
            except Payment.DoesNotExist:
                old_status = None
        else:
            old_status = None

        # Only update totals if status is 'completed' or changed from 'completed'
        if instance.status == 'completed' or old_status == 'completed':
            # Recalculate invoice amount_paid
            invoice = instance.invoice
            invoice.refresh_from_db()  # Ensure we have the latest data
            
            total_payments = Decimal('0.00')
            for payment in invoice.payments.filter(status='completed'):
                total_payments += payment.amount
            
            # Update invoice
            invoice.amount_paid = total_payments
            invoice.save()  # This will trigger update_status()
            
            # Update billing totals
            billing = invoice.billing
            billing.refresh_from_db()
            billing.update_totals()

            # Check if billing should be marked as paid
            # Only check if billing is active and balance_due is zero
            if billing.status == 'active' and billing.balance_due == Decimal('0.00'):
                billing.status = 'paid'
                billing.save(skip_update=True)

@receiver(post_delete, sender=Payment)
def handle_payment_delete(sender, instance, **kwargs):
    """Update invoice and billing totals when a payment is deleted"""
    with transaction.atomic():
        # Only update if the deleted payment was completed
        if instance.status == 'completed':
            # Recalculate invoice amount_paid
            invoice = instance.invoice
            invoice.refresh_from_db()
            
            total_payments = Decimal('0.00')
            for payment in invoice.payments.filter(status='completed'):
                total_payments += payment.amount
            
            # Update invoice
            invoice.amount_paid = total_payments
            invoice.save()  # This will trigger update_status()
            
            # Update billing totals
            billing = invoice.billing
            billing.refresh_from_db()
            billing.update_totals()

            # Check if billing status needs to be updated
            if billing.status == 'paid' and billing.balance_due > Decimal('0.00'):
                billing.status = 'active'
                billing.save(skip_update=True)

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

