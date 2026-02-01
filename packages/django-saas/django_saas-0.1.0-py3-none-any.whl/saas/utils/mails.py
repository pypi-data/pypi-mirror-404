import typing as t

import css_inline
from django.core.mail import EmailMultiAlternatives
from django.template import loader

from saas.settings import saas_settings


def render_mail_messages(template_id: str, context: t.Dict[str, t.Any]) -> t.Tuple[str, str]:
    context.setdefault('site', saas_settings.SITE)
    text: str = loader.render_to_string(f'saas_emails/{template_id}.text', context)
    html: str = loader.render_to_string(f'saas_emails/{template_id}.html', context)
    return text, css_inline.inline(html)


def send_email(
    subject: str,
    recipients: t.List[str],
    text_message: str,
    html_message: t.Optional[str] = None,
    from_email: t.Optional[str] = None,
    headers: t.Optional[t.Dict[str, str]] = None,
    reply_to: t.Optional[str] = None,
):
    mail = EmailMultiAlternatives(
        subject,
        body=text_message,
        from_email=from_email,
        to=recipients,
        headers=headers,
        reply_to=reply_to,
    )
    if html_message:
        mail.attach_alternative(html_message, 'text/html')

    return mail.send()
