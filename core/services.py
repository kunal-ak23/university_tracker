# core/services.py
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from datetime import date, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import PaymentSchedule, PaymentReminder, PaymentScheduleRecipient
import logging
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