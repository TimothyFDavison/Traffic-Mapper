import smtplib
from email.message import EmailMessage


def send_sms_via_email(number, carrier_gateway, message, sender_email, sender_password):
    """"
    Given a target phone number and carrier (e.g. Verizon), send an SMS via email.
    Requires connectivity to a gmail account.

    It's probably not a good practice to put email/password as input parameters like this, but
    just performing some quick experimentation for the time being.
    """
    # Message parameters
    to_number = f"{number}@{carrier_gateway}"
    msg = EmailMessage()
    msg.set_content(message)
    msg["Subject"] = ""
    msg["From"] = sender_email
    msg["To"] = to_number

    # Send using smtp, gmail credentials
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)
