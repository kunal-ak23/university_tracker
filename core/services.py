# core/services.py
from zoneinfo import ZoneInfo

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Sequence

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import LedgerLine, PaymentSchedule, PaymentReminder, PaymentScheduleRecipient
import requests

logger = logging.getLogger('django')

class ContractService:
    @staticmethod
    def validate_contract(contract):
        # Check if contract has streams through stream_pricing
        if not contract.stream_pricing.exists():
            raise ValidationError("Contract must have at least one stream pricing entry.")
        if not contract.programs.exists():
            raise ValidationError("Contract must have at least one program.")

class PaymentScheduleService:
    @staticmethod
    def create_payment_schedule(invoice, amount, due_date, reminder_recipients=None, frequency='one_time', reminder_days=7):
        """Create a payment schedule for an invoice"""
        schedule = PaymentSchedule.objects.create(
            invoice=invoice,
            amount=amount,
            due_date=due_date,
            frequency=frequency,
            reminder_days=reminder_days
        )
        
        # Create recipients if provided
        if reminder_recipients:
            for email in reminder_recipients.split(','):
                email = email.strip()
                if email:  # Only create for non-empty emails
                    PaymentScheduleRecipient.objects.create(
                        payment_schedule=schedule,
                        email=email
                    )
        
        # Create reminder
        reminder_date = due_date - timedelta(days=reminder_days)
        PaymentReminder.objects.create(
            payment_schedule=schedule,
            scheduled_date=reminder_date
        )
        
        return schedule

    @staticmethod
    def process_reminders():
        """Process pending reminders"""
        today = date.today()
        pending_reminders = PaymentReminder.objects.filter(
            status='pending',
            scheduled_date=today
        ).select_related('payment_schedule__invoice__billing')

        for reminder in pending_reminders:
            try:
                schedule = reminder.payment_schedule
                invoice = schedule.invoice
                billing = invoice.billing
                
                # Send email reminder
                subject = f'Payment Reminder: Invoice #{invoice.id}'
                message = f"""
                Dear Customer,

                This is a reminder that a payment of {schedule.amount} is due on {schedule.due_date}
                for Invoice #{invoice.id}.

                Payment Details:
                - Amount Due: {schedule.amount}
                - Due Date: {schedule.due_date}
                - Invoice Number: {invoice.id}
                - Billing Reference: {billing.name}

                Please ensure timely payment to avoid any service interruptions.

                Best regards,
                Your Organization
                """
                
                # Get recipients from payment schedule
                recipients = schedule.get_reminder_recipients()
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipients,
                    fail_silently=False,
                )
                
                reminder.status = 'sent'
                reminder.sent_at = timezone.now()
                reminder.save()
                
            except Exception as e:
                reminder.status = 'failed'
                reminder.error_message = str(e)
                reminder.save()

class EventIntegrationService:
    """Service for handling event integrations with Notion"""
    
    @staticmethod
    def trigger_event_integrations(event):
        """Trigger integrations for an approved event"""
        if not event.is_approved():
            logger.warning(f"Event {event.id} is not approved, skipping integrations")
            return
        
        try:
            # Create Notion page
            EventIntegrationService.create_notion_page(event)
            
        except Exception as e:
            logger.error(f"Failed to trigger integrations for event {event.id}: {str(e)}")
            event.mark_integration_failed(str(e))
    
    
    @staticmethod
    def create_notion_page(event):
        """Create Notion page for the university event"""
        try:
            # This is a placeholder for actual Notion API integration
            # You would implement the actual Notion API calls here
            
            # Example implementation structure:
            # import requests
            # 
            # headers = {
            #     "Authorization": f"Bearer {settings.NOTION_API_KEY}",
            #     "Content-Type": "application/json",
            #     "Notion-Version": "2022-06-28"
            # }
            # 
            # page_data = {
            #     "parent": {"database_id": settings.NOTION_EVENTS_DATABASE_ID},
            #     "properties": {
            #         "Title": {"title": [{"text": {"content": event.title}}]},
            #         "University": {"rich_text": [{"text": {"content": event.university.name}}]},
            #         "Start Date": {"date": {"start": event.start_datetime.isoformat()}},
            #         "End Date": {"date": {"start": event.end_datetime.isoformat()}},
            #         "Location": {"rich_text": [{"text": {"content": event.location}}]},
            #         "Status": {"select": {"name": event.status}},
            #         "Batch": {"rich_text": [{"text": {"content": event.batch.name if event.batch else "N/A"}}]}
            #     },
            #     "children": [
            #         {
            #             "object": "block",
            #             "type": "paragraph",
            #             "paragraph": {
            #                 "rich_text": [{"text": {"content": event.description}}]
            #             }
            #         }
            #     ]
            # }
            # 
            # response = requests.post(
            #     "https://api.notion.com/v1/pages",
            #     headers=headers,
            #     json=page_data
            # )
            # 
            # page_id = response.json()["id"]
            # page_url = response.json()["url"]
            
            # For now, we'll simulate the integration
            page_id = f"notion_page_{event.id}_{int(timezone.now().timestamp())}"
            page_url = f"https://notion.so/{page_id}"
            
            event.mark_notion_created(page_id, page_url)
            logger.info(f"Notion page created for event {event.id}")
            
        except Exception as e:
            logger.error(f"Failed to create Notion page for event {event.id}: {str(e)}")
            raise


def trigger_event_integrations(event):
    """Global function to trigger event integrations"""
    EventIntegrationService.trigger_event_integrations(event)


@dataclass(frozen=True)
class LedgerEntrySpec:
    entry_date: date
    account: str
    entry_type: str
    amount: Decimal
    memo: Optional[str] = None


@dataclass(frozen=True)
class LedgerEffect:
    entries: Sequence[LedgerEntrySpec]
    context: Dict[str, Any]

    def has_entries(self) -> bool:
        return bool(self.entries)


class LedgerService:
    """Central helper for producing and persisting append-only ledger lines."""

    @classmethod
    def sync_payment(cls, payment, previous_version=None):
        cls._sync_effects(
            cls.build_payment_effect(previous_version),
            cls.build_payment_effect(payment),
        )

    @classmethod
    def sync_oem_payment(cls, oem_payment, previous_version=None):
        cls._sync_effects(
            cls.build_oem_payment_effect(previous_version),
            cls.build_oem_payment_effect(oem_payment),
        )

    @classmethod
    def sync_expense(cls, expense, previous_version=None):
        cls._sync_effects(
            cls.build_expense_effect(previous_version),
            cls.build_expense_effect(expense),
        )

    @classmethod
    def build_payment_effect(cls, payment) -> Optional[LedgerEffect]:
        if not payment or payment.status != 'completed':
            return None

        amount = cls._to_amount(payment.amount)
        if amount == Decimal('0.00'):
            return None

        memo = f"Payment {payment.name} ({payment.payment_method})"
        entry_date = payment.payment_date or date.today()
        context = cls._build_context(
            payment=payment,
            invoice=payment.invoice,
            billing=getattr(payment.invoice, 'billing', None) if payment.invoice else None,
            external_reference=payment.transaction_reference,
        )

        entries = [
            LedgerEntrySpec(
                entry_date=entry_date,
                account=LedgerLine.Account.CASH,
                entry_type=LedgerLine.EntryType.DEBIT,
                amount=amount,
                memo=memo,
            ),
            LedgerEntrySpec(
                entry_date=entry_date,
                account=LedgerLine.Account.ACCOUNTS_RECEIVABLE,
                entry_type=LedgerLine.EntryType.CREDIT,
                amount=amount,
                memo=memo,
            ),
        ]

        return LedgerEffect(entries=entries, context=context)

    @classmethod
    def build_oem_payment_effect(cls, oem_payment) -> Optional[LedgerEffect]:
        if not oem_payment or oem_payment.status != 'completed':
            return None

        amount = cls._to_amount(oem_payment.amount)
        if amount == Decimal('0.00'):
            return None

        memo = f"OEM Payment ({oem_payment.payment_method})"
        entry_date = oem_payment.payment_date or date.today()
        context = cls._build_context(
            oem_payment=oem_payment,
            invoice=oem_payment.invoice,
            billing=oem_payment.billing,
            oem=oem_payment.oem,
            external_reference=oem_payment.reference_number,
        )

        entries = [
            LedgerEntrySpec(
                entry_date=entry_date,
                account=LedgerLine.Account.OEM_PAYABLE,
                entry_type=LedgerLine.EntryType.DEBIT,
                amount=amount,
                memo=memo,
            ),
            LedgerEntrySpec(
                entry_date=entry_date,
                account=LedgerLine.Account.CASH,
                entry_type=LedgerLine.EntryType.CREDIT,
                amount=amount,
                memo=memo,
            ),
        ]

        return LedgerEffect(entries=entries, context=context)

    @classmethod
    def build_expense_effect(cls, expense) -> Optional[LedgerEffect]:
        if not expense or not expense.amount or not expense.university:
            return None

        amount = cls._to_amount(expense.amount)
        if amount == Decimal('0.00'):
            return None

        memo = f"Expense {expense.category}: {expense.description or ''}".strip()
        entry_date = getattr(expense, 'incurred_date', None)
        if not entry_date:
            created_at = getattr(expense, 'created_at', None)
            entry_date = created_at.date() if created_at else date.today()
        context = cls._build_context(
            expense=expense,
            university=expense.university,
            external_reference=f"EXP-{expense.id}" if expense.id else None,
        )

        entries = [
            LedgerEntrySpec(
                entry_date=entry_date,
                account=LedgerLine.Account.EXPENSE,
                entry_type=LedgerLine.EntryType.DEBIT,
                amount=amount,
                memo=memo,
            ),
            LedgerEntrySpec(
                entry_date=entry_date,
                account=LedgerLine.Account.CASH,
                entry_type=LedgerLine.EntryType.CREDIT,
                amount=amount,
                memo=memo,
            ),
        ]

        return LedgerEffect(entries=entries, context=context)

    @classmethod
    def record_effect(cls, effect: Optional[LedgerEffect]):
        """Append entries for a freshly created effect (used by rebuild command)."""
        if not effect or not effect.has_entries():
            return []
        return cls._persist(effect, reversing=False)

    @classmethod
    def _sync_effects(cls, before: Optional[LedgerEffect], after: Optional[LedgerEffect]):
        if cls._effects_equal(before, after):
            return

        if before and before.has_entries():
            cls._persist(before, reversing=True)

        if after and after.has_entries():
            cls._persist(after, reversing=False)

    @classmethod
    def _persist(cls, effect: LedgerEffect, reversing: bool):
        created = []
        if not effect or not effect.entries:
            return created

        context = effect.context or {}

        with transaction.atomic():
            for entry in effect.entries:
                entry_type = entry.entry_type
                memo = entry.memo
                if reversing:
                    entry_type = (
                        LedgerLine.EntryType.DEBIT
                        if entry.entry_type == LedgerLine.EntryType.CREDIT
                        else LedgerLine.EntryType.CREDIT
                    )
                    memo = (f"{memo} (reversal)" if memo else "Reversal").strip()

                created.append(
                    LedgerLine.objects.create(
                        account=entry.account,
                        entry_date=entry.entry_date,
                        entry_type=entry_type,
                        amount=entry.amount,
                        memo=memo,
                        payment=context.get('payment'),
                        invoice=context.get('invoice'),
                        billing=context.get('billing'),
                        expense=context.get('expense'),
                        oem_payment=context.get('oem_payment'),
                        university=context.get('university'),
                        oem=context.get('oem'),
                        external_reference=context.get('external_reference'),
                        reversing=reversing,
                    )
                )

        return created

    @classmethod
    def _build_context(
        cls,
        payment=None,
        invoice=None,
        billing=None,
        expense=None,
        oem_payment=None,
        oem=None,
        university=None,
        external_reference=None,
    ):
        billing = billing or getattr(invoice, 'billing', None) if invoice else billing
        university = university or cls._resolve_university(billing)
        oem = oem or cls._resolve_oem(invoice, billing)

        return {
            'payment': payment,
            'invoice': invoice,
            'billing': billing,
            'expense': expense,
            'oem_payment': oem_payment,
            'university': university,
            'oem': oem,
            'external_reference': external_reference,
        }

    @staticmethod
    def _resolve_university(billing):
        if not billing:
            return None
        first_batch = billing.batches.first()
        return first_batch.university if first_batch else None

    @staticmethod
    def _resolve_oem(invoice, billing):
        if invoice and hasattr(invoice, 'get_oem'):
            oem = invoice.get_oem()
            if oem:
                return oem

        billing = billing or getattr(invoice, 'billing', None)
        if not billing:
            return None

        first_batch = billing.batches.first()
        if not first_batch:
            return None
        contract = first_batch.get_contract() if hasattr(first_batch, 'get_contract') else None
        return contract.oem if contract and contract.oem else None

    @staticmethod
    def _effects_equal(before: Optional[LedgerEffect], after: Optional[LedgerEffect]) -> bool:
        return LedgerService._effect_signature(before) == LedgerService._effect_signature(after)

    @staticmethod
    def _effect_signature(effect: Optional[LedgerEffect]):
        if not effect or not effect.entries:
            return None

        entries_sig = tuple(
            (
                entry.account,
                entry.entry_type,
                str(entry.amount),
                entry.memo,
                entry.entry_date.isoformat() if hasattr(entry.entry_date, 'isoformat') else entry.entry_date,
            )
            for entry in effect.entries
        )
        context = effect.context or {}
        ctx_sig = (
            LedgerService._pk(context.get('payment')),
            LedgerService._pk(context.get('invoice')),
            LedgerService._pk(context.get('billing')),
            LedgerService._pk(context.get('expense')),
            LedgerService._pk(context.get('oem_payment')),
            LedgerService._pk(context.get('university')),
            LedgerService._pk(context.get('oem')),
            context.get('external_reference'),
        )
        return entries_sig, ctx_sig

    @staticmethod
    def _pk(obj):
        return obj.pk if obj is not None and hasattr(obj, 'pk') else obj

    @staticmethod
    def _to_amount(value) -> Decimal:
        if value is None:
            return Decimal('0.00')
        return Decimal(str(value))