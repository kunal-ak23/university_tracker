# core/signals.py
import logging

from django.db import transaction, models
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from core.logger_service import get_logger
from core.models import ContractFile, Billing, Payment, Invoice, Contract

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
            total_students = 0
            # Clear previous batch_snapshots
            instance.batch_snapshots.clear()
            for batch in instance.batches.all():
                total_students += batch.number_of_students
                instance.batch_snapshots.add(instance.add_batch_snapshot(batch))

            if instance.batches.exists():
                contract = instance.batches.first().contract
                cost_per_student = contract.cost_per_student
                tax_rate = contract.tax_rate.rate / 100  # Convert percentage to decimal

                # Calculate total amount based on the number of students and tax rate
                instance.total_amount = total_students * cost_per_student * (1 + tax_rate)

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
        logger.info(f"Validating courses for Contract ID: {instance.pk}")
        # filter duplicates and remove all courses that are not from the OEM
        logger.info(instance.oem)
        for course in instance.courses.all():
            logger.info(course.provider)

        filtered_courses = instance.courses.filter(provider=instance.oem).distinct()
        if filtered_courses.count() != instance.courses.count():
            logger.warning(f"Some courses do not belong to OEM {instance.oem.name} and will be removed.")
        instance.courses.clear()
        instance.courses.set(filtered_courses)
        logger.info(f"Validation complete for Contract ID: {instance.pk}")

