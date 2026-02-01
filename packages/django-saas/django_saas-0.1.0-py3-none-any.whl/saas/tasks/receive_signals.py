from django.dispatch import receiver

from saas.signals import mail_queued
from saas.utils.mails import render_mail_messages

from .send_mails import send_email


@receiver(mail_queued)
def send_queued_mail(sender, template_id, subject, recipients, context, **kwargs):
    text_message, html_message = render_mail_messages(template_id, context)
    send_email.enqueue(
        subject=str(subject),
        recipients=recipients,
        text_message=text_message,
        html_message=html_message,
    )
