from celery import shared_task
from typing import List
import asyncio
from .mail import send_mail

@shared_task(name="pundra_send_email_queue_task")
def send_email_queue_task(subject: str, to: List[str], template_name: str, context: dict, cc: List[str] | str = None, bcc: List[str] | str = None, reply_to: List[str] | str = None, logger = None):
    try:
        coro = send_mail(
            subject=subject,
            to=to,
            template_name=template_name,
            context=context,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to
        )
        
        result = asyncio.run(coro)
        return "Email sent"
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise