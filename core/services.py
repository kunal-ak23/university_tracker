# core/services.py

from django.core.exceptions import ValidationError
from datetime import date, timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import PaymentSchedule, PaymentReminder, PaymentScheduleRecipient

class ContractService:
    @staticmethod
    def validate_contract(contract):
        if not contract.streams.exists():
            raise ValidationError("Contract must have at least one stream.")
        if not contract.courses.exists():
            raise ValidationError("Contract must have at least one course.")
        if not contract.contract_files.exists():
            raise ValidationError("Contract must have at least one contract file.")

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