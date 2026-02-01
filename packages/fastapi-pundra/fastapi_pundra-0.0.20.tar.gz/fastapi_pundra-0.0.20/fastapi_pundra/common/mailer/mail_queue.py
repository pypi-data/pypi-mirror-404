from .task import send_email_queue_task
from typing import List

async def send_mail_queue(
    subject: str, 
    to: List[str], 
    template_name: str, 
    context: dict, 
    cc: List[str] | str = None, 
    bcc: List[str] | str = None, 
    reply_to: List[str] | str = None, 
    delay: int = 30
):
    send_email_queue_task.apply_async(
        args=[subject, to, template_name, context, cc, bcc, reply_to],
        countdown=delay
    ) 