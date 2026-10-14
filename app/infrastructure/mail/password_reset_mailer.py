import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode


class SmtpPasswordResetMailer:

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        sender_email: str,
        frontend_reset_url: str,
        smtp_username: str | None = None,
        smtp_password: str | None = None,
        use_starttls: bool = True,
    ) -> None:

        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.frontend_reset_url = frontend_reset_url

        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.use_starttls = use_starttls

    def send_password_reset(
        self,
        email: str,
        raw_token: str,
    ) -> None:

        # 1. Construct the recovery link
        query = urlencode({"token": raw_token})
        reset_link = f"{self.frontend_reset_url}?{query}"

        # 2. Construct the email
        message = EmailMessage()

        message["From"] = self.sender_email
        message["To"] = email
        message["Subject"] = "Reset your password"

        message.set_content(f"""
    We received a request to reset your password.

    Use the following link to reset it:

    {reset_link}

    This link expires in 30 minutes.

    If you didn't request this, you can ignore this email.
    """)

        # 3. Connect to the SMTP server
        with smtplib.SMTP(
            self.smtp_host,
            self.smtp_port,
            timeout=10,
        ) as server:

            # 4. Upgrade the connection to TLS
            if self.use_starttls:
                server.starttls(context=ssl.create_default_context())

            # 5. Authenticate if credentials are configured
            if self.smtp_username and self.smtp_password:
                server.login(
                    self.smtp_username,
                    self.smtp_password,
                )

            # 6. Send the email
            server.send_message(message)
