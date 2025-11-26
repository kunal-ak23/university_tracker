# core/signals.py
import logging

from django.db import transaction, models
from django.db.models.signals import post_save, post_delete, pre_save, m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from core.logger_service import get_logger
from core.models import ContractFile, Billing, Payment, Invoice, Contract, Expense, OEMPayment, InvoiceOEMPayment, InvoiceTDS
from core.services import PaymentScheduleService, LedgerService

logger = get_logger()


@receiver(pre_save, sender=Expense)
def track_expense_snapshot(sender, instance, **kwargs):
    """Store previous expense for ledger diffing."""
    if instance.pk:
        try:
            instance._ledger_previous_version = Expense.objects.get(pk=instance.pk)
        except Expense.DoesNotExist:
            instance._ledger_previous_version = None
    else:
        instance._ledger_previous_version = None

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

@receiver(pre_save, sender=Payment)
def track_payment_status_change(sender, instance, **kwargs):
    """Track payment status before save to detect changes"""
    if instance.pk:
        try:
            old_payment = Payment.objects.get(pk=instance.pk)
            instance._previous_status = old_payment.status
            instance._ledger_previous_version = old_payment
        except Payment.DoesNotExist:
            instance._previous_status = None
            instance._ledger_previous_version = None
    else:
        instance._previous_status = None
        instance._ledger_previous_version = None

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

    try:
        LedgerService.sync_payment(None, previous_version=instance)
    except Exception as e:
        logger.error(f"Failed to append reversing ledger lines for deleted payment {instance.id}: {str(e)}", exc_info=True)

@receiver(post_save, sender=Invoice)
def create_payment_schedule(sender, instance, created, **kwargs):
    """Create payment schedule when invoice is created"""
    if created:
        try:
            # Ensure invoice has a primary key before accessing relationships
            if not instance.pk:
                logger.warning(f"Invoice {instance.id if hasattr(instance, 'id') else 'unknown'} does not have a primary key yet, skipping payment schedule creation")
                return
            
            # Get recipients from the contract's POC and OEM contact
            # Add proper null checks to avoid AttributeError
            if not instance.billing:
                logger.warning(f"Invoice {instance.pk} has no billing, skipping payment schedule creation")
                return
            
            first_batch = instance.billing.batches.first()
            if not first_batch:
                logger.warning(f"Invoice {instance.pk} billing has no batches, skipping payment schedule creation")
                return
            
            contract = first_batch.get_contract()
            if not contract or not contract.oem:
                logger.warning(f"Invoice {instance.pk} has no contract or OEM, skipping payment schedule creation")
                return
            
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
                reminder_recipients=reminder_recipients if reminder_recipients else None
            )
        except Exception as e:
            logger.error(f"Failed to create payment schedule for invoice {instance.pk if hasattr(instance, 'pk') and instance.pk else 'unknown'}: {str(e)}", exc_info=True)

@receiver(post_save, sender=Payment)
def sync_payment_ledger_entry(sender, instance, **kwargs):
    """Append ledger lines for payment changes."""
    try:
        LedgerService.sync_payment(instance, getattr(instance, '_ledger_previous_version', None))
    except Exception as e:
        logger.error(f"Failed to sync ledger for payment {instance.id}: {str(e)}", exc_info=True)

@receiver(post_save, sender=Expense)
def sync_expense_ledger_entry(sender, instance, **kwargs):
    """Append ledger lines for any expense change."""
    try:
        LedgerService.sync_expense(instance, getattr(instance, '_ledger_previous_version', None))
    except Exception as e:
        logger.error(f"Failed to sync ledger for expense {instance.id}: {str(e)}", exc_info=True)


@receiver(post_delete, sender=Expense)
def reverse_expense_ledger_entry(sender, instance, **kwargs):
    """Append reversing entries when an expense is deleted."""
    try:
        LedgerService.sync_expense(None, previous_version=instance)
    except Exception as e:
        logger.error(f"Failed to append reversing ledger lines for expense {instance.id}: {str(e)}", exc_info=True)

@receiver(pre_save, sender=OEMPayment)
def track_oem_payment_status_change(sender, instance, **kwargs):
    """Track OEMPayment status before save to detect changes"""
    if instance.pk:
        try:
            old_payment = OEMPayment.objects.get(pk=instance.pk)
            instance._previous_status = old_payment.status
            instance._previous_amount = old_payment.amount
            instance._ledger_previous_version = old_payment
        except OEMPayment.DoesNotExist:
            instance._previous_status = None
            instance._previous_amount = None
            instance._ledger_previous_version = None
    else:
        instance._previous_status = None
        instance._previous_amount = None
        instance._ledger_previous_version = None


@receiver(post_save, sender=OEMPayment)
def sync_oem_payment_ledger_entry(sender, instance, **kwargs):
    """
    Append ledger lines when an OEM payment is completed or reversed.
    """
    try:
        LedgerService.sync_oem_payment(instance, getattr(instance, '_ledger_previous_version', None))
    except Exception as e:
        logger.error(f"Failed to sync ledger for OEM payment {instance.id}: {str(e)}", exc_info=True)


@receiver(post_delete, sender=OEMPayment)
def reverse_oem_payment_ledger_entry(sender, instance, **kwargs):
    """Append reversing entries when an OEM payment is deleted."""
    try:
        LedgerService.sync_oem_payment(None, previous_version=instance)
    except Exception as e:
        logger.error(f"Failed to append reversing ledger lines for OEM payment {instance.id}: {str(e)}", exc_info=True)
@receiver(pre_save, sender=InvoiceOEMPayment)
def track_invoice_oem_payment_status_change(sender, instance, **kwargs):
    """Track InvoiceOEMPayment status before save to detect changes"""
    if instance.pk:
        try:
            old_payment = InvoiceOEMPayment.objects.get(pk=instance.pk)
            instance._previous_status = old_payment.status
            instance._previous_oem_payment_id = old_payment.oem_payment_id if old_payment.oem_payment else None
        except InvoiceOEMPayment.DoesNotExist:
            instance._previous_status = None
            instance._previous_oem_payment_id = None
    else:
        instance._previous_status = None
        instance._previous_oem_payment_id = None


@receiver(post_save, sender=InvoiceOEMPayment)
def create_invoice_oem_payment_entry(sender, instance, created, **kwargs):
    """
    Create or update OEMPayment rows when InvoiceOEMPayment status changes.
    """
    old_status = getattr(instance, '_previous_status', None)

    if instance.status == 'completed':
        try:
            invoice = instance.invoice
            oem = invoice.get_oem() if hasattr(invoice, 'get_oem') else None

            if not oem and invoice.billing:
                for batch in invoice.billing.batches.all():
                    contract = batch.get_contract() if batch else None
                    if contract and contract.oem:
                        oem = contract.oem
                        logger.info(f"Found OEM {oem.id} for invoice {invoice.id} via batch {batch.id}")
                        break

            if not oem:
                logger.warning(f"Cannot create OEMPayment: No OEM found for invoice {invoice.id}.")
                return

            if instance.oem_payment:
                from decimal import Decimal

                oem_payment = instance.oem_payment
                oem_payment.amount = instance.amount
                oem_payment.net_amount = Decimal(str(instance.amount)) - Decimal(
                    str(oem_payment.tax_amount or 0)
                )
                oem_payment.payment_date = instance.payment_date
                oem_payment.payment_method = instance.payment_method
                oem_payment.reference_number = instance.reference_number
                oem_payment.description = (
                    instance.description or f"OEM Payment for Invoice {invoice.name}"
                )
                oem_payment.notes = instance.notes
                oem_payment.status = 'completed'
                oem_payment.invoice = invoice
                oem_payment.billing = invoice.billing
                oem_payment.clean()
                oem_payment.save()
            else:
                from decimal import Decimal

                with transaction.atomic():
                    net_amount = Decimal(str(instance.amount)) - Decimal('0.00')

                    oem_payment = OEMPayment(
                        oem=oem,
                        amount=instance.amount,
                        net_amount=net_amount,
                        tax_amount=Decimal('0.00'),
                        payment_type='oem_transfer',
                        payment_method=instance.payment_method,
                        status='completed',
                        payment_date=instance.payment_date,
                        processed_date=instance.processed_date or timezone.now(),
                        reference_number=instance.reference_number,
                        description=instance.description or f"OEM Payment for Invoice {invoice.name}",
                        notes=instance.notes,
                        billing=invoice.billing,
                        invoice=invoice,
                        created_by=instance.created_by,
                    )
                    oem_payment.clean()
                    oem_payment.save()

                    instance.oem_payment = oem_payment
                    instance.save(update_fields=['oem_payment'])

        except Exception as e:
            logger.error(
                f"Failed to create OEMPayment entry for InvoiceOEMPayment {instance.id}: {str(e)}",
                exc_info=True,
            )
    elif old_status == 'completed' and instance.status != 'completed' and instance.oem_payment:
        try:
            oem_payment = instance.oem_payment
            oem_payment.status = instance.status
            note = f"Status updated to {instance.status} via Invoice OEM payment {instance.id}"
            oem_payment.notes = f"{oem_payment.notes or ''}\n{note}".strip()
            oem_payment.save(update_fields=['status', 'notes'])
        except Exception as e:
            logger.error(
                f"Failed to sync OEMPayment {instance.oem_payment_id} after InvoiceOEMPayment update: {str(e)}",
                exc_info=True,
            )


@receiver(post_save, sender=InvoiceTDS)
def update_invoice_status_on_tds(sender, instance, created, **kwargs):
    """
    Update invoice status when TDS is added/updated.
    TDS is NOT tracked in the ledger - it's only for record-keeping at invoice level.
    TDS is money registered against our account in income tax department,
    paid by university directly to government on our behalf - never hits our bank account.
    """
    try:
        invoice = instance.invoice
        # Update invoice status to account for TDS (for invoice payment status calculation)
        if invoice:
            invoice.update_status()
            invoice.save()
    except Exception as e:
        logger.error(f"Failed to update invoice status after TDS change: {str(e)}")


@receiver(post_delete, sender=InvoiceTDS)
def update_invoice_status_on_tds_delete(sender, instance, **kwargs):
    """Update invoice status when TDS is deleted"""
    try:
        invoice = instance.invoice
        # Update invoice status after TDS deletion
        if invoice:
            invoice.update_status()
            invoice.save()
    except Exception as e:
        logger.error(f"Failed to update invoice status after TDS deletion: {str(e)}")

