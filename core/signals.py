# core/signals.py
import logging

from django.db import transaction, models
from django.db.models.signals import post_save, post_delete, pre_save, m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from core.logger_service import get_logger
from core.models import ContractFile, Billing, Payment, Invoice, Contract, PaymentLedger, Expense, OEMPayment, InvoiceOEMPayment, InvoiceTDS
from core.services import PaymentScheduleService

logger = get_logger()

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
        except Payment.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None

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

@receiver(post_save, sender=Payment)
def create_payment_ledger_entry(sender, instance, created, **kwargs):
    """Create or update ledger entry when a payment is completed"""
    # Get old status to detect changes
    old_status = getattr(instance, '_previous_status', None)
    
    # If payment status changed from 'completed' to something else, remove ledger entry
    if old_status == 'completed' and instance.status != 'completed':
        try:
            # Get university and billing to find the ledger entry
            university = None
            billing = None
            if instance.invoice and instance.invoice.billing:
                billing = instance.invoice.billing
                if billing.batches.exists():
                    first_batch = billing.batches.first()
                    university = first_batch.university if first_batch else None
            
            if university:
                # Find and remove ledger entries for this payment
                matching_entries = PaymentLedger.objects.filter(
                    transaction_type='income',
                    transaction_date=instance.payment_date,
                    university=university,
                    billing=billing,
                    reference_number=instance.transaction_reference or ''
                )
                
                if matching_entries.exists():
                    # Remove the entries
                    deleted_count = matching_entries.count()
                    matching_entries.delete()
                    # Recalculate running balances
                    PaymentLedger.recalculate_running_balances(university_id=university.id if university else None)
                    logger.info(f"Removed {deleted_count} ledger entry(ies) for payment {instance.id} (status changed from completed to {instance.status})")
        except Exception as e:
            logger.error(f"Failed to remove payment ledger entry: {str(e)}")
        return  # Don't create/update anything if status is not completed
    
    # Only create/update ledger entry if payment is completed
    if instance.status == 'completed':
        should_create_entry = False
        should_update_entry = False
        
        if created:
            # New payment created with 'completed' status
            should_create_entry = True
        else:
            # Check if status changed from non-completed to completed
            # Use the _previous_status set in pre_save signal
            old_status = getattr(instance, '_previous_status', None)
            if old_status and old_status != 'completed':
                should_create_entry = True
            elif old_status == 'completed':
                # Payment was already completed - check if we need to update ledger entry
                # (e.g., amount, date, or other details changed)
                should_update_entry = True
        
        try:
            # Get university from the payment's invoice billing
            university = None
            billing = None
            if instance.invoice and instance.invoice.billing:
                billing = instance.invoice.billing
                # Get university from the first batch in the billing
                if billing.batches.exists():
                    first_batch = billing.batches.first()
                    university = first_batch.university if first_batch else None
            
            if university:
                # Check if ledger entry already exists for this payment
                # Look for entries matching date, university, billing, and reference
                matching_entries = PaymentLedger.objects.filter(
                    transaction_type='income',
                    transaction_date=instance.payment_date,
                    university=university,
                    billing=billing,
                    reference_number=instance.transaction_reference or ''
                )
                
                # Check for exact match (correct amount)
                exact_entry = matching_entries.filter(amount=instance.amount).first()
                
                # Check for entries with wrong amount (payment was updated)
                wrong_amount_entries = matching_entries.exclude(amount=instance.amount)
                
                if exact_entry:
                    # Perfect match exists - no action needed unless other details changed
                    # Update description and notes in case they changed
                    if (exact_entry.description != f"Payment received from {university.name} - {instance.name}" or
                        exact_entry.notes != f"Payment method: {instance.payment_method}"):
                        exact_entry.description = f"Payment received from {university.name} - {instance.name}"
                        exact_entry.notes = f"Payment method: {instance.payment_method}"
                        exact_entry.save()
                elif wrong_amount_entries.exists() and (should_create_entry or should_update_entry):
                    # Ledger entry exists but with wrong amount - update it
                    wrong_entry = wrong_amount_entries.first()
                    old_amount = wrong_entry.amount
                    wrong_entry.amount = instance.amount
                    wrong_entry.description = f"Payment received from {university.name} - {instance.name}"
                    wrong_entry.notes = f"Payment method: {instance.payment_method}"
                    wrong_entry.save()
                    
                    # Remove any duplicate entries
                    if wrong_amount_entries.count() > 1:
                        wrong_amount_entries.exclude(id=wrong_entry.id).delete()
                    
                    # Recalculate running balances since amount changed
                    PaymentLedger.recalculate_running_balances(university_id=university.id if university else None)
                    logger.info(f"Updated ledger entry {wrong_entry.id}: amount {old_amount} -> {instance.amount} for payment {instance.id}")
                elif should_create_entry and not exact_entry:
                    # No matching entry found - create new one
                    PaymentLedger.create_ledger_entry(
                        transaction_type='income',
                        amount=instance.amount,
                        transaction_date=instance.payment_date,
                        description=f"Payment received from {university.name} - {instance.name}",
                        university=university,
                        billing=billing,
                        reference_number=instance.transaction_reference,
                        notes=f"Payment method: {instance.payment_method}"
                    )
        except Exception as e:
            logger.error(f"Failed to create/update payment ledger entry: {str(e)}")

@receiver(post_save, sender=Expense)
def create_expense_ledger_entry(sender, instance, created, **kwargs):
    """Create ledger entry when an expense is created"""
    if created and instance.amount and instance.university:
        try:
            PaymentLedger.create_ledger_entry(
                transaction_type='expense',
                amount=instance.amount,
                transaction_date=instance.incurred_date,
                description=f"Expense - {instance.category}: {instance.description}",
                university=instance.university,
                reference_number=f"EXP-{instance.id}",
                notes=f"Category: {instance.get_category_display()}"
            )
        except Exception as e:
            logger.error(f"Failed to create expense ledger entry: {str(e)}")

@receiver(pre_save, sender=OEMPayment)
def track_oem_payment_status_change(sender, instance, **kwargs):
    """Track OEMPayment status before save to detect changes"""
    if instance.pk:
        try:
            old_payment = OEMPayment.objects.get(pk=instance.pk)
            instance._previous_status = old_payment.status
            instance._previous_amount = old_payment.amount
        except OEMPayment.DoesNotExist:
            instance._previous_status = None
            instance._previous_amount = None
    else:
        instance._previous_status = None
        instance._previous_amount = None


@receiver(post_save, sender=OEMPayment)
def create_oem_payment_ledger_entry(sender, instance, created, **kwargs):
    """
    Create or update ledger entry when an OEM payment is made.
    OEM payments are tracked as expenses in the ledger (reduce balance).
    """
    old_status = getattr(instance, '_previous_status', None)
    old_amount = getattr(instance, '_previous_amount', None)
    
    logger.info(f"OEMPayment signal fired: id={instance.id}, status={instance.status}, created={created}")
    
    # Only create/update ledger entry when status is 'completed'
    if instance.status == 'completed':
        try:
            # Get university from the payment's billing or invoice if available
            university = None
            if instance.billing:
                if instance.billing.batches.exists():
                    first_batch = instance.billing.batches.first()
                    university = first_batch.university if first_batch else None
            elif instance.invoice:
                # Get university from invoice billing
                if instance.invoice.billing and instance.invoice.billing.batches.exists():
                    first_batch = instance.invoice.billing.batches.first()
                    university = first_batch.university if first_batch else None
            
            if not university:
                logger.warning(f"No university found for OEMPayment {instance.id} - billing={instance.billing_id}, invoice={instance.invoice_id}")
            
            # Check if ledger entry already exists
            existing_entry = PaymentLedger.objects.filter(
                transaction_type='oem_payment',
                payment=instance,
                invoice=instance.invoice
            ).first()
            
            if existing_entry:
                logger.info(f"Updating existing ledger entry {existing_entry.id} for OEMPayment {instance.id}")
                # Update existing ledger entry
                if (existing_entry.amount != instance.amount or 
                    existing_entry.transaction_date != instance.payment_date or
                    old_status != 'completed'):
                    existing_entry.amount = instance.amount
                    existing_entry.transaction_date = instance.payment_date
                    existing_entry.description = f"OEM Payment - {instance.payment_type}: {instance.description or 'N/A'}"
                    existing_entry.reference_number = instance.reference_number
                    existing_entry.notes = f"Payment method: {instance.payment_method}"
                    existing_entry.save()
                    # Recalculate balances
                    PaymentLedger.recalculate_running_balances(university_id=university.id if university else None)
            else:
                logger.info(f"Creating new ledger entry for OEMPayment {instance.id} - amount={instance.amount}, university={university}")
                # Create new ledger entry
                ledger_entry = PaymentLedger.create_ledger_entry(
                    transaction_type='oem_payment',
                    amount=instance.amount,
                    transaction_date=instance.payment_date,
                    description=f"OEM Payment - {instance.payment_type}: {instance.description or 'N/A'}",
                    oem=instance.oem,
                    university=university,
                    billing=instance.billing,
                    payment=instance,
                    invoice=instance.invoice,
                    reference_number=instance.reference_number,
                    notes=f"Payment method: {instance.payment_method}"
                )
                logger.info(f"Created ledger entry {ledger_entry.id} for OEMPayment {instance.id}")
        except Exception as e:
            logger.error(f"Failed to create/update OEM payment ledger entry for OEMPayment {instance.id}: {str(e)}", exc_info=True)
    elif old_status == 'completed' and instance.status != 'completed':
        # Status changed from completed to something else - remove ledger entry
        try:
            ledger_entries = PaymentLedger.objects.filter(
                transaction_type='oem_payment',
                payment=instance,
                invoice=instance.invoice
            )
            
            if ledger_entries.exists():
                university_id = None
                if instance.invoice and instance.invoice.billing:
                    if instance.invoice.billing.batches.exists():
                        first_batch = instance.invoice.billing.batches.first()
                        university_id = first_batch.university.id if first_batch and first_batch.university else None
                elif instance.billing:
                    if instance.billing.batches.exists():
                        first_batch = instance.billing.batches.first()
                        university_id = first_batch.university.id if first_batch and first_batch.university else None
                
                ledger_entries.delete()
                
                # Recalculate balances
                if university_id:
                    PaymentLedger.recalculate_running_balances(university_id=university_id)
                else:
                    PaymentLedger.recalculate_running_balances()
        except Exception as e:
            logger.error(f"Failed to remove OEM payment ledger entry: {str(e)}")


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
    Create/update OEMPayment entry when InvoiceOEMPayment status changes.
    OEM payments are tracked as expenses in the ledger (reduce balance).
    """
    old_status = getattr(instance, '_previous_status', None)
    
    # Only create/update OEMPayment entry when status is 'completed'
    if instance.status == 'completed':
        try:
            invoice = instance.invoice
            oem = invoice.get_oem()
            
            if not oem:
                # Try alternative methods to find OEM
                # Check if billing has batches with contracts
                if invoice.billing:
                    for batch in invoice.billing.batches.all():
                        contract = batch.get_contract() if batch else None
                        if contract and contract.oem:
                            oem = contract.oem
                            logger.info(f"Found OEM {oem.id} for invoice {invoice.id} via batch {batch.id}")
                            break
                
                if not oem:
                    logger.warning(f"Cannot create OEMPayment: No OEM found for invoice {invoice.id}. Cannot create ledger entry without OEM.")
                    return
            
            # Get university for ledger entry
            university = None
            if invoice.billing and invoice.billing.batches.exists():
                first_batch = invoice.billing.batches.first()
                university = first_batch.university if first_batch else None
            
            # Check if OEMPayment already exists for this InvoiceOEMPayment
            if instance.oem_payment:
                # Update existing OEMPayment entry
                from decimal import Decimal
                oem_payment = instance.oem_payment
                old_amount = oem_payment.amount
                oem_payment.amount = instance.amount
                oem_payment.net_amount = Decimal(str(instance.amount)) - Decimal(str(oem_payment.tax_amount or 0))
                oem_payment.payment_date = instance.payment_date
                oem_payment.payment_method = instance.payment_method
                oem_payment.reference_number = instance.reference_number
                oem_payment.description = instance.description or f"OEM Payment for Invoice {invoice.name}"
                oem_payment.notes = instance.notes
                oem_payment.status = 'completed'
                oem_payment.invoice = invoice
                oem_payment.billing = invoice.billing
                oem_payment.clean()
                oem_payment.save()
                
                # Update ledger entry if amount changed or if it didn't exist before
                if old_status != 'completed' or old_amount != instance.amount:
                    # Find and update ledger entry
                    ledger_entry = PaymentLedger.objects.filter(
                        transaction_type='oem_payment',
                        payment=oem_payment,
                        invoice=invoice
                    ).first()
                    
                    if ledger_entry:
                        ledger_entry.amount = instance.amount
                        ledger_entry.transaction_date = instance.payment_date
                        ledger_entry.description = f"OEM Payment - oem_transfer: {oem_payment.description}"
                        ledger_entry.reference_number = instance.reference_number
                        ledger_entry.notes = f"Payment method: {instance.payment_method}"
                        ledger_entry.save()
                        # Recalculate balances
                        PaymentLedger.recalculate_running_balances(university_id=university.id if university else None)
            else:
                # Create new OEMPayment entry
                from decimal import Decimal
                with transaction.atomic():
                    # Calculate net_amount (amount - tax_amount, where tax_amount defaults to 0)
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
                        created_by=instance.created_by
                    )
                    # Call clean() to validate and set any missing fields
                    oem_payment.clean()
                    oem_payment.save()
                    
                    # Link InvoiceOEMPayment to OEMPayment
                    instance.oem_payment = oem_payment
                    instance.save(update_fields=['oem_payment'])
                
                # The OEMPayment signal will create the ledger entry automatically
                logger.info(f"Created OEMPayment {oem_payment.id} from InvoiceOEMPayment {instance.id} - signal should fire")
            
        except Exception as e:
            logger.error(f"Failed to create OEMPayment entry for InvoiceOEMPayment {instance.id}: {str(e)}", exc_info=True)
    elif old_status == 'completed' and instance.status != 'completed':
        # Status changed from completed to something else - remove ledger entry
        try:
            if instance.oem_payment:
                # Find and remove ledger entry
                ledger_entries = PaymentLedger.objects.filter(
                    transaction_type='oem_payment',
                    payment=instance.oem_payment,
                    invoice=instance.invoice
                )
                
                if ledger_entries.exists():
                    university_id = None
                    if instance.invoice and instance.invoice.billing:
                        if instance.invoice.billing.batches.exists():
                            first_batch = instance.invoice.billing.batches.first()
                            university_id = first_batch.university.id if first_batch and first_batch.university else None
                    
                    ledger_entries.delete()
                    
                    # Recalculate balances
                    if university_id:
                        PaymentLedger.recalculate_running_balances(university_id=university_id)
                    else:
                        PaymentLedger.recalculate_running_balances()
        except Exception as e:
            logger.error(f"Failed to remove OEM payment ledger entry: {str(e)}")


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

