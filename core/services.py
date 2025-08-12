# core/services.py

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
        if not contract.streams.exists():
            raise ValidationError("Contract must have at least one stream.")
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
    """Service for handling event integrations with Microsoft Graph (email) and Notion"""
    
    @staticmethod
    def trigger_event_integrations(event):
        """Trigger integrations for an approved event"""
        if not event.is_approved():
            logger.warning(f"Event {event.id} is not approved, skipping integrations")
            return
        
        try:
            # Send email notification using Microsoft Graph
            EventIntegrationService.send_event_email(event)
            
            # Create Notion page
            EventIntegrationService.create_notion_page(event)
            
        except Exception as e:
            logger.error(f"Failed to trigger integrations for event {event.id}: {str(e)}")
            event.mark_integration_failed(str(e))
    
    @staticmethod
    def send_event_email(event):
        """Send email notification for the university event using Microsoft Graph API"""
        try:
            # Check if Microsoft Graph is configured
            if not all([settings.GRAPH_CLIENT_ID, settings.GRAPH_CLIENT_SECRET, settings.GRAPH_TENANT, settings.GRAPH_SENDER_ID]):
                logger.warning("Microsoft Graph not configured (missing GRAPH_* envs), skipping email integration")
                return False
            
            # Get access token using client credentials
            access_token = EventIntegrationService._get_graph_access_token()
            
            if not access_token:
                logger.warning("No access token available for Microsoft Graph")
                return False

            # Get invitee emails
            invitee_emails = event.get_invitee_emails()
            
            # Prepare email content
            email_subject = f"Automated Event Invitation: {event.title}"
            email_body = EventIntegrationService._create_email_body(event)
            
            # Send email to teched@datagami.in with invitees in body
            try:
                success = EventIntegrationService._send_single_email(
                    access_token, settings.GRAPH_SENDER_ID, email_subject, email_body
                )
                if success:
                    event.mark_email_sent(len(invitee_emails))
                    logger.info(f"Email sent to teched@datagami.in for event {event.id} with {len(invitee_emails)} invitees")
                    return True
                else:
                    logger.error(f"Failed to send email to teched@datagami.in for event {event.id}")
                    return False
            except Exception as e:
                logger.error(f"Failed to send email to teched@datagami.in: {str(e)}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to send event email for event {event.id}: {str(e)}")
            return False
    
    @staticmethod
    def _get_graph_access_token():
        """Get access token for Microsoft Graph API using client credentials"""
        try:
            token_url = f"https://login.microsoftonline.com/{settings.GRAPH_TENANT}/oauth2/v2.0/token"
            
            data = {
                'client_id': settings.GRAPH_CLIENT_ID,
                'client_secret': settings.GRAPH_CLIENT_SECRET,
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'client_credentials'
            }
            
            response = requests.post(token_url, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token')
            else:
                logger.error(f"Failed to acquire token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error acquiring access token: {str(e)}")
            return None
    
    @staticmethod
    def _create_email_body(event):
        """Create HTML email body for the event with invitees for Power Automate processing"""
        invitees = event.get_invitees()
        
        # Create structured invitee list for Power Automate
        invitee_emails = [invitee['email'] for invitee in invitees]
        invitee_list = "\n".join([f"• {invitee['name']} ({invitee['email']}) - {invitee['role']}" for invitee in invitees])
        
        html_body = f"""
        <html>
        <body>
            <h2>Event Invitation</h2>
            <p><strong>Event:</strong> {event.title}</p>
            <p><strong>Date:</strong> {event.start_datetime.strftime('%A, %B %d, %Y')}</p>
            <p><strong>Time:</strong> {event.start_datetime.strftime('%I:%M %p')} - {event.end_datetime.strftime('%I:%M %p')}</p>
            <p><strong>Location:</strong> {event.location}</p>
            <p><strong>University:</strong> {event.university.name}</p>
            <p><strong>Description:</strong></p>
            <p>{event.description}</p>
            
            <h3>Invitees for Calendar Invite:</h3>
            <p><strong>Email List (comma-separated):</strong></p>
            <p>{', '.join(invitee_emails)}</p>
            
            <h3>Detailed Invitee List:</h3>
            <p>{invitee_list}</p>
            
            <hr>
            <p><em>Power Automate will process this email and create calendar invites for all listed invitees.</em></p>
            
            <p>Best regards,<br>
            {event.university.name}</p>
        </body>
        </html>
        """
        
        return html_body
    
    @staticmethod
    def _send_single_email(access_token, recipient_email, subject, html_body):
        """Send a single email using Microsoft Graph API"""
        try:
            # Prepare the email payload
            payload = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML",
                        "content": html_body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": recipient_email
                            }
                        }
                    ]
                },
                "saveToSentItems": "true"
            }
            
            # Make the API call to Microsoft Graph
            response = requests.post(
                f"https://graph.microsoft.com/v1.0/users/{settings.GRAPH_SENDER_ID}/sendMail",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=20
            )
            
            if response.status_code == 202:  # 202 Accepted is the correct response for sendMail
                return True
            else:
                logger.error(f"Failed to send email to {recipient_email}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Exception sending email to {recipient_email}: {str(e)}")
            return False
    
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