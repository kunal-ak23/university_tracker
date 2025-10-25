from django.core.management.base import BaseCommand
from core.models import PaymentLedger, University
from decimal import Decimal


class Command(BaseCommand):
    help = 'Fix running balances in PaymentLedger by recalculating them in chronological order'

    def add_arguments(self, parser):
        parser.add_argument(
            '--university-id',
            type=int,
            help='Fix balances for a specific university only',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        university_id = options.get('university_id')
        dry_run = options.get('dry_run', False)
        
        if university_id:
            try:
                university = University.objects.get(id=university_id)
                self.stdout.write(f'Fixing ledger balances for university: {university.name}')
            except University.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'University with ID {university_id} not found')
                )
                return
        else:
            self.stdout.write('Fixing ledger balances for all universities...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self._show_current_balances(university_id)
            return
        
        # Get current state before fixing
        self._show_current_balances(university_id, "BEFORE")
        
        # Recalculate balances
        updated_count = PaymentLedger.recalculate_running_balances(university_id=university_id)
        
        # Show results
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} ledger entries')
        )
        
        # Show state after fixing
        self._show_current_balances(university_id, "AFTER")
        
        self.stdout.write(
            self.style.SUCCESS('Ledger balance recalculation completed!')
        )

    def _show_current_balances(self, university_id=None, stage="CURRENT"):
        """Show current running balances for debugging"""
        queryset = PaymentLedger.objects.all()
        if university_id:
            queryset = queryset.filter(university_id=university_id)
        
        entries = queryset.order_by('transaction_date', 'created_at')
        
        self.stdout.write(f'\n--- {stage} STATE ---')
        self.stdout.write(f'Total entries: {entries.count()}')
        
        if entries.exists():
            self.stdout.write('\nFirst 5 entries:')
            for entry in entries[:5]:
                self.stdout.write(
                    f'  {entry.transaction_date} | {entry.transaction_type:12} | '
                    f'₹{entry.amount:>10} | Balance: ₹{entry.running_balance:>10} | '
                    f'{entry.description[:50]}...'
                )
            
            if entries.count() > 5:
                self.stdout.write(f'  ... and {entries.count() - 5} more entries')
            
            self.stdout.write(f'\nLast entry balance: ₹{entries.last().running_balance}')
        else:
            self.stdout.write('No ledger entries found.')
