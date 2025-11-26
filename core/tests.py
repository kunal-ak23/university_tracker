from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from django.db.models import Sum

from core.models import (
    Batch,
    Billing,
    Expense,
    Invoice,
    LedgerLine,
    OEM,
    OEMPayment,
    Payment,
    Stream,
    University,
    InvoiceTDS,
)


class LedgerLineTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create(username='admin', email='admin@example.com')

        self.university = University.objects.create(
            name='Test University',
            website='https://example.edu',
            established_year=2000,
            accreditation='A',
        )

        self.stream = Stream.objects.create(
            name='Computer Science',
            duration=12,
            duration_unit='Months',
            university=self.university,
        )

        self.batch = Batch.objects.create(
            university=self.university,
            stream=self.stream,
            name='Batch 001',
            start_year=2025,
            end_year=2026,
            number_of_students=10,
        )

        self.billing = Billing.objects.create(name='Billing 001', status='active')
        self.billing.batches.add(self.batch)

        self.invoice = Invoice.objects.create(
            billing=self.billing,
            issue_date=date(2025, 1, 1),
            due_date=date(2025, 2, 1),
            amount=Decimal('100.00'),
        )

        self.oem = OEM.objects.create(
            name='Test OEM',
            website='https://oem.example.com',
            contact_email='contact@oem.example.com',
        )

    def _create_payment(self, amount=Decimal('100.00'), invoice=None, transaction_reference='TXN-123'):
        invoice = invoice or self.invoice
        return Payment.objects.create(
            invoice=invoice,
            amount=amount,
            payment_date=date(2025, 1, 15),
            payment_method='bank_transfer',
            status='completed',
            transaction_reference=transaction_reference,
            name='Test Payment',
        )

    def _create_expense(self, amount=Decimal('25.00')):
        return Expense.objects.create(
            university=self.university,
            amount=amount,
            category='operations',
            incurred_date=date(2025, 1, 10),
            description='Test expense',
        )

    def _create_oem_payment(self, amount=Decimal('50.00')):
        return OEMPayment.objects.create(
            oem=self.oem,
            amount=amount,
            net_amount=amount,
            tax_amount=Decimal('0.00'),
            payment_type='oem_transfer',
            payment_method='bank_transfer',
            status='completed',
            payment_date=date(2025, 1, 20),
            reference_number='OEM-123',
            description='OEM transfer',
            billing=self.billing,
            invoice=self.invoice,
            created_by=self.admin,
        )

    def test_payment_update_appends_reversals(self):
        payment = self._create_payment()
        self.assertEqual(LedgerLine.objects.filter(payment=payment).count(), 2)

        self.invoice.amount = Decimal('500.00')
        self.invoice.amount_paid = Decimal('100.00')
        self.invoice.save(update_fields=['amount', 'amount_paid'])

        payment.amount = Decimal('150.00')
        payment.save()

        lines = LedgerLine.objects.filter(payment=payment)
        self.assertEqual(lines.count(), 6)
        self.assertEqual(lines.filter(reversing=True).count(), 2)

    def test_payment_delete_records_reversal(self):
        payment = self._create_payment()
        Payment.objects.filter(id=payment.id).delete()

        lines = LedgerLine.objects.filter(payment_id=payment.id)
        self.assertEqual(lines.count(), 4)
        self.assertEqual(lines.filter(reversing=True).count(), 2)

    def test_rebuild_command_recreates_entries(self):
        payment = self._create_payment()
        expense = self._create_expense()
        oem_payment = self._create_oem_payment()

        initial_count = LedgerLine.objects.count()
        self.assertEqual(initial_count, 6)

        LedgerLine.objects.all().delete()
        self.assertEqual(LedgerLine.objects.count(), 0)

        call_command('rebuild_ledger')

        self.assertEqual(LedgerLine.objects.count(), initial_count)
        self.assertEqual(LedgerLine.objects.filter(payment=payment).count(), 2)
        self.assertEqual(LedgerLine.objects.filter(expense=expense).count(), 2)
        self.assertEqual(LedgerLine.objects.filter(oem_payment=oem_payment).count(), 2)

    def test_receivable_with_tds_and_oem_adjustment(self):
        invoice_two = Invoice.objects.create(
            billing=self.billing,
            issue_date=date(2025, 1, 5),
            due_date=date(2025, 2, 5),
            amount=Decimal('500.00'),
        )

        InvoiceTDS.objects.create(
            invoice=invoice_two,
            amount=Decimal('50.00'),
            tds_rate=Decimal('10.00'),
            deduction_date=date(2025, 1, 18),
            reference_number='TDS-50',
        )

        payment_one = self._create_payment(
            amount=Decimal('200.00'),
            invoice=self.invoice,
            transaction_reference='TXN-001',
        )
        payment_two = self._create_payment(
            amount=Decimal('250.00'),
            invoice=invoice_two,
            transaction_reference='TXN-002',
        )

        oem_payment = self._create_oem_payment(amount=Decimal('250.00'))
        oem_payment.amount = Decimal('300.00')
        oem_payment.net_amount = Decimal('300.00')
        oem_payment.save()

        cash_debits = LedgerLine.objects.filter(
            account=LedgerLine.Account.CASH,
            entry_type=LedgerLine.EntryType.DEBIT,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        cash_credits = LedgerLine.objects.filter(
            account=LedgerLine.Account.CASH,
            entry_type=LedgerLine.EntryType.CREDIT,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        receivable_credits = LedgerLine.objects.filter(
            account=LedgerLine.Account.ACCOUNTS_RECEIVABLE,
            entry_type=LedgerLine.EntryType.CREDIT,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        oem_payable_debits = LedgerLine.objects.filter(
            account=LedgerLine.Account.OEM_PAYABLE,
            entry_type=LedgerLine.EntryType.DEBIT,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        oem_payable_credits = LedgerLine.objects.filter(
            account=LedgerLine.Account.OEM_PAYABLE,
            entry_type=LedgerLine.EntryType.CREDIT,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        self.assertEqual(LedgerLine.objects.filter(payment__in=[payment_one, payment_two]).count(), 4)
        self.assertEqual(LedgerLine.objects.filter(oem_payment=oem_payment).count(), 6)
        self.assertEqual(LedgerLine.objects.filter(oem_payment=oem_payment, reversing=True).count(), 2)

        self.assertEqual(receivable_credits, Decimal('450.00'))
        self.assertEqual(cash_debits - cash_credits, Decimal('150.00'))
        self.assertEqual(oem_payable_debits - oem_payable_credits, Decimal('300.00'))
