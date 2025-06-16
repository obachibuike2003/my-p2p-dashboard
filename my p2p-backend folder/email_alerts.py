import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_alert_email(sender_email: str, sender_password: str, recipient_email: str, subject: str, body: str) -> bool:
    """
    Sends an email alert using Gmail SMTP.
    Requires app password for Gmail account if 2FA is enabled.
    """
    if not all([sender_email, sender_password, recipient_email, subject, body]):
        logging.error("Missing email parameters. Cannot send alert email.")
        return False

    # For Gmail, the SMTP server is smtp.gmail.com and the port is 587 (TLS)
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        logging.info(f"Email alert sent successfully to {recipient_email} with subject: '{subject}'")
        return True
    except smtplib.SMTPAuthenticationError:
        logging.error("❌ SMTP Authentication Error: Could not log in. Check email username/password (for Gmail, use App Password).")
        return False
    except smtplib.SMTPConnectError as e:
        logging.error(f"❌ SMTP Connection Error: Could not connect to SMTP server: {e}. Check internet connection or server address/port.")
        return False
    except Exception as e:
        logging.error(f"❌ An unexpected error occurred while sending email alert: {e}", exc_info=True)
        return False

