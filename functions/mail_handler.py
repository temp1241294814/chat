import functions_framework
import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import base64
import json

# Create a SendGrid client
sg = SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
FROM = os.environ.get("FROM_EMAIL")


@functions_framework.http
def handle_email(request):
    request_json = request.get_json()
    data = json.loads(base64.b64decode(request_json["message"]["data"]).decode("utf-8"))
    to_emails = data["to_emails"]
    subject = data["subject"]
    message = data["message"]

    # Create the email message
    email = Mail(
        from_email=FROM,
        to_emails=to_emails,
        subject=subject,
        plain_text_content=message,
    )

    try:
        # Send the email
        sg.send(email)
        return "ok", 200
    except Exception:
        return "error", 500
