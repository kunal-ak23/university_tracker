"""
Management command to fix missing OEMPayment and ledger entries for InvoiceOEMPayment entries.
This happens when an InvoiceOEMPayment was created with status='completed' but:
1. No OEM was found at creation time, or
2. The signal failed to create the OEMPayment entry
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import InvoiceOEMPayment, OEMPayment, PaymentLedger
from core.signals import create_invoice_oem_payment_entry
from decimal import Decimal


class Command(BaseCommand):
    help = 'Fix missing OEMPayment and ledger entries for InvoiceOEMPayment entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find InvoiceOEMPayment entries with status='completed' but no linked OEMPayment
        missing_oem_payments = InvoiceOEMPayment.objects.filter(
            status='completed',
            oem_payment__isnull=True
        )
        
        if not missing_oem_payments.exists():
            self.stdout.write(
                self.style.SUCCESS('No missing OEMPayment entries found. All good!')
            )
            return
        
        self.stdout.write(
            f'Found {missing_oem_payments.count()} InvoiceOEMPayment entries missing OEMPayment links'
        )
        
        fixed_count = 0
        skipped_count = 0
        
        for invoice_oem_payment in missing_oem_payments:
            invoice = invoice_oem_payment.invoice
            oem = invoice.get_oem()
            
            if not oem:
                # Try alternative lookup
                if invoice.billing:
                    for batch in invoice.billing.batches.all():
                        contract = batch.get_contract() if batch else None
                        if contract and contract.oem:
                            oem = contract.oem
                            break
                
                if not oem:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Skipping InvoiceOEMPayment {invoice_oem_payment.id}: '
                            f'No OEM found for invoice {invoice.id}. '
                            f'Invoice billing: {invoice.billing_id}, '
                            f'Batches: {list(invoice.billing.batches.values_list("id", flat=True)) if invoice.billing else "None"}'
                        )
                    )
                    skipped_count += 1
                    continue
            
            if dry_run:
                self.stdout.write(
                    f'  Would create OEMPayment for InvoiceOEMPayment {invoice_oem_payment.id}: '
                    f'invoice={invoice.id}, oem={oem.id}, amount={invoice_oem_payment.amount}'
                )
            else:
                try:
                    with transaction.atomic():
                        # Calculate net_amount
                        net_amount = Decimal(str(invoice_oem_payment.amount)) - Decimal('0.00')
                        
                        # Create OEMPayment
                        oem_payment = OEMPayment(
                            oem=oem,
                            amount=invoice_oem_payment.amount,
                            net_amount=net_amount,
                            tax_amount=Decimal('0.00'),
                            payment_type='oem_transfer',
                            payment_method=invoice_oem_payment.payment_method,
                            status='completed',
                            payment_date=invoice_oem_payment.payment_date,
                            processed_date=invoice_oem_payment.processed_date or invoice_oem_payment.created_at,
                            reference_number=invoice_oem_payment.reference_number,
                            description=invoice_oem_payment.description or f"OEM Payment for Invoice {invoice.name}",
                            notes=invoice_oem_payment.notes,
                            billing=invoice.billing,
                            invoice=invoice,
                            created_by=invoice_oem_payment.created_by
                        )
                        oem_payment.clean()
                        oem_payment.save()
                        
                        # Link InvoiceOEMPayment to OEMPayment
                        invoice_oem_payment.oem_payment = oem_payment
                        invoice_oem_payment.save(update_fields=['oem_payment'])
                        
                        # Manually trigger ledger entry creation if not created
                        # The OEMPayment signal should have created it, but let's verify
                        ledger_entry = PaymentLedger.objects.filter(
                            transaction_type='oem_payment',
                            payment=oem_payment,
                            invoice=invoice
                        ).first()
                        
                        if not ledger_entry:
                            # Create ledger entry manually
                            PaymentLedger.create_ledger_entry(
                                transaction_type='oem_payment',
                                amount=oem_payment.amount,
                                transaction_date=oem_payment.payment_date,
                                description=f"OEM Payment - {oem_payment.payment_type}: {oem_payment.description or 'N/A'}",
                                oem=oem_payment.oem,
                                university=first_batch.university if (invoice.billing and invoice.billing.batches.exists() and (first_batch := invoice.billing.batches.first())) else None,
                                billing=oem_payment.billing,
                                payment=oem_payment,
                                invoice=invoice,
                                reference_number=oem_payment.reference_number,
                                notes=f"Payment method: {oem_payment.payment_method}"
                            )
                            self.stdout.write(
                                f'  Created OEMPayment {oem_payment.id} and ledger entry for InvoiceOEMPayment {invoice_oem_payment.id}'
                            )
                        else:
                            self.stdout.write(
                                f'  Created OEMPayment {oem_payment.id} for InvoiceOEMPayment {invoice_oem_payment.id} (ledger entry already exists)'
                            )
                        
                        fixed_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  Failed to fix InvoiceOEMPayment {invoice_oem_payment.id}: {str(e)}'
                        )
                    )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nDry run complete. Would fix {fixed_count} entries, skip {skipped_count} entries.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nFixed {fixed_count} entries, skipped {skipped_count} entries.'
                )
            )

