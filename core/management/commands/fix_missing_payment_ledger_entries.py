from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Payment, PaymentLedger, University
from decimal import Decimal


class Command(BaseCommand):
    help = 'Fix missing ledger entries for completed payments that were created/updated before the bug fix'

    def add_arguments(self, parser):
        parser.add_argument(
            '--university-id',
            type=int,
            help='Fix entries for a specific university only',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes',
        )

    def handle(self, *args, **options):
        university_id = options.get('university_id')
        dry_run = options.get('dry_run', False)
        
        if university_id:
            try:
                university = University.objects.get(id=university_id)
                self.stdout.write(f'Fixing missing ledger entries for university: {university.name}')
            except University.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'University with ID {university_id} not found')
                )
                return
        else:
            self.stdout.write('Fixing missing ledger entries for all universities...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get all completed payments
        payments = Payment.objects.filter(status='completed')
        if university_id:
            # Filter payments by university
            payments = payments.filter(
                invoice__billing__batches__university_id=university_id
            ).distinct()
        
        self.stdout.write(f'Found {payments.count()} completed payments to check')
        
        missing_count = 0
        created_count = 0
        error_count = 0
        updated_count = 0
        removed_duplicates_count = 0
        
        for payment in payments:
            try:
                # Get university and billing from the payment's invoice
                university = None
                billing = None
                if payment.invoice and payment.invoice.billing:
                    billing = payment.invoice.billing
                    # Get university from the first batch in the billing
                    if billing.batches.exists():
                        first_batch = billing.batches.first()
                        university = first_batch.university if first_batch else None
                
                if not university:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping payment {payment.id}: No university found (invoice: {payment.invoice.id})'
                        )
                    )
                    continue
                
                # Check for ledger entries matching this payment (same date, university, billing, reference)
                # We need to find entries that might be for this payment, even if amount doesn't match
                matching_entries = PaymentLedger.objects.filter(
                    transaction_type='income',
                    transaction_date=payment.payment_date,
                    university=university,
                    billing=billing,
                    reference_number=payment.transaction_reference or ''
                )
                
                # Find exact match (correct amount)
                exact_match = matching_entries.filter(amount=payment.amount).first()
                
                # Find entries with wrong amounts (payment was updated)
                wrong_amount_entries = matching_entries.exclude(amount=payment.amount)
                
                if exact_match:
                    # Perfect match exists, no action needed
                    continue
                elif wrong_amount_entries.exists():
                    # Ledger entry exists but with wrong amount - update it
                    wrong_entry = wrong_amount_entries.first()
                    old_amount = wrong_entry.amount
                    
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(
                                f'[DRY RUN] Would update ledger entry {wrong_entry.id}: '
                                f'amount {old_amount} -> {payment.amount} for payment {payment.id}'
                            )
                        )
                        updated_count += 1
                        
                        # Count duplicates that would be removed
                        if wrong_amount_entries.count() > 1:
                            removed_duplicates_count += wrong_amount_entries.exclude(id=wrong_entry.id).count()
                    else:
                        with transaction.atomic():
                            wrong_entry.amount = payment.amount
                            wrong_entry.description = f"Payment received from {university.name} - {payment.name}"
                            wrong_entry.notes = f"Payment method: {payment.payment_method}"
                            wrong_entry.save()
                            updated_count += 1
                            
                            # Remove any other duplicate entries for this payment
                            if wrong_amount_entries.count() > 1:
                                duplicates_to_remove = wrong_amount_entries.exclude(id=wrong_entry.id)
                                removed_duplicates_count += duplicates_to_remove.count()
                                duplicates_to_remove.delete()
                else:
                    # No matching entry found - create new one
                    missing_count += 1
                    
                    description = f"Payment received from {university.name} - {payment.name}"
                    
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(
                                f'[DRY RUN] Would create ledger entry for payment {payment.id}: '
                                f'{payment.amount} on {payment.payment_date} for {university.name}'
                            )
                        )
                    else:
                        # Create the ledger entry directly (without triggering full recalculation each time)
                        # We'll do a single recalculation at the end
                        with transaction.atomic():
                            PaymentLedger.objects.create(
                                transaction_type='income',
                                amount=payment.amount,
                                transaction_date=payment.payment_date,
                                description=description,
                                university=university,
                                billing=billing,
                                reference_number=payment.transaction_reference,
                                notes=f"Payment method: {payment.payment_method}",
                                running_balance=Decimal('0.00')  # Will be fixed by final recalculation
                            )
                            created_count += 1
                            
                            if created_count % 10 == 0:
                                self.stdout.write(f'Created {created_count} ledger entries...')
                                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing payment {payment.id}: {str(e)}'
                    )
                )
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(f'  Total payments checked: {payments.count()}')
        self.stdout.write(f'  Missing ledger entries found: {missing_count}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('  DRY RUN - No entries were created/updated'))
            if updated_count > 0:
                self.stdout.write(f'  Would update {updated_count} ledger entries with wrong amounts')
            if removed_duplicates_count > 0:
                self.stdout.write(f'  Would remove {removed_duplicates_count} duplicate entries')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'  Ledger entries created: {created_count}')
            )
            if updated_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'  Ledger entries updated (wrong amounts): {updated_count}')
                )
            if removed_duplicates_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'  Duplicate entries removed: {removed_duplicates_count}')
                )
            
            if error_count > 0:
                self.stdout.write(
                    self.style.ERROR(f'  Errors encountered: {error_count}')
                )
            
            # Recalculate running balances if any changes were made
            if created_count > 0 or updated_count > 0 or removed_duplicates_count > 0:
                self.stdout.write('\nRecalculating running balances...')
                if university_id:
                    balance_updated_count = PaymentLedger.recalculate_running_balances(
                        university_id=university_id
                    )
                else:
                    balance_updated_count = PaymentLedger.recalculate_running_balances()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully recalculated {balance_updated_count} ledger entry balances'
                    )
                )
        
        self.stdout.write(self.style.SUCCESS('Fix completed!'))
