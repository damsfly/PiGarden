import smtplib
from email.message import EmailMessage
from smtplib import SMTPException, SMTPConnectError, SMTPHeloError, SMTPAuthenticationError


def send_email(email_config, subject, body):
    """ Fonction pour envoyer un courriel """
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = email_config["email_address"]
        msg["To"] = email_config["recipient_address"]

        with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
            server.starttls()
            server.login(email_config["email_address"], email_config["email_password"])
            server.send_message(msg)

        print("E-mail envoyé avec succès.")
    except (SMTPException, SMTPConnectError, SMTPHeloError, SMTPAuthenticationError) as error:
        print(f"Erreur lors de l'envoi de l'e-mail : {error}")
