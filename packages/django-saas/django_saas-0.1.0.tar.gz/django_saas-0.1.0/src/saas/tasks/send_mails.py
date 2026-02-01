import typing as t

from django.tasks import task

from saas.utils.mails import send_email as _send_email


@task
def send_email(
    subject: str,
    recipients: t.List[str],
    text_message: str,
    html_message: t.Optional[str] = None,
    from_email: t.Optional[str] = None,
    headers: t.Optional[t.Dict[str, str]] = None,
    reply_to: t.Optional[str] = None,
):
    return _send_email(
        subject,
        recipients,
        text_message,
        html_message,
        from_email,
        headers,
        reply_to,
    )
