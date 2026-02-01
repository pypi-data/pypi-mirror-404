from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv
from .mail_templating import EmailTemplates
from fastapi_pundra.common.helpers import base_path
import os
from typing import List

# Load environment variables from .env file
load_dotenv()

def str_to_bool(value):
    return value.lower() in ("true", "1", "yes")

# Configure email connection
def mail_config():
    conf = ConnectionConfig(
        MAIL_USERNAME=os.getenv('MAIL_USERNAME', 'default_username'),
        MAIL_PASSWORD=os.getenv('MAIL_PASSWORD', 'default_password'),
        MAIL_FROM=os.getenv('MAIL_FROM_ADDRESS', 'noreply@example.com'),  # Default sender address
        MAIL_PORT=int(os.getenv('MAIL_PORT', '465')),  # Changed to 465 for SSL
        MAIL_SERVER=os.getenv('MAIL_HOST', 'smtp.gmail.com'),  # Default to Gmail SMTP server
        MAIL_STARTTLS=str_to_bool(os.getenv('MAIL_STARTTLS', 'False')),  # Changed to False since we're using SSL/TLS
        MAIL_SSL_TLS=str_to_bool(os.getenv('MAIL_SSL_TLS', 'True')),    # Changed to True for Gmail's secure connection
        USE_CREDENTIALS=str_to_bool(os.getenv('MAIL_USE_CREDENTIALS', 'True'))
    )
    return conf

def render_mail_template(template_name: str, context: dict = {}):
    # Initialize EmailTemplates with the correct directory
    project_base_path = os.getenv('PROJECT_BASE_PATH', 'app')

    template_dir = os.path.join(base_path(), project_base_path, 'templates', 'mails')
    templates = EmailTemplates(directory=template_dir)
    # Render the specified template with the given context
    return templates.render_template(template_name, context)

async def send_mail_util(subject: str, to: List[str], template_name: str, context: dict = None, cc: List[str] | str = None, bcc: List[str] | str = None, reply_to: List[str] | str = None):
    try:
        if not isinstance(to, list):
            to = [to]
        
        # Convert cc, bcc, reply_to to lists if they are strings
        if cc and not isinstance(cc, list):
            cc = [cc]
        if bcc and not isinstance(bcc, list):
            bcc = [bcc]
        if reply_to and not isinstance(reply_to, list):
            reply_to = [reply_to]
            
        # Create message kwargs with required fields
        message_kwargs = {
            "subject": subject,
            "recipients": to,
            "body": render_mail_template(template_name=template_name, context=context),
            "subtype": "html"
        }
        
        # Only add optional fields if they have values
        if cc:
            message_kwargs["cc"] = cc
        if bcc:
            message_kwargs["bcc"] = bcc
        if reply_to:
            message_kwargs["reply_to"] = reply_to
            
        message = MessageSchema(**message_kwargs)
        the_mail_config = mail_config()
        
        fm = FastMail(the_mail_config)
        await fm.send_message(message)
        return "Email has been sent"
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return f'An error occurred while sending the email: {str(e)}'

async def send_mail_background(background_tasks: BackgroundTasks, subject: str, to: List[str], template_name: str, context: dict = None, cc: List[str] | str = None, bcc: List[str] | str = None, reply_to: List[str] | str = None):
    background_tasks.add_task(send_mail_util, subject, to, template_name, context, cc, bcc, reply_to)
    return "Email scheduled for sending"

async def send_mail(subject: str, to: List[str], template_name: str, context: dict = None, cc: List[str] | str = None, bcc: List[str] | str = None, reply_to: List[str] | str = None):
    return await send_mail_util(subject, to, template_name, context, cc, bcc, reply_to)

