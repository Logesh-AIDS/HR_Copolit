# services/common/email.py
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class EmailService(ABC):
    """
    Abstract interface for email notification delivery.
    """
    @abstractmethod
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        pass

    @abstractmethod
    def send_verification_email(self, to_email: str, token: str) -> bool:
        pass

    @abstractmethod
    def send_welcome_email(self, to_email: str, name: str) -> bool:
        pass

    @abstractmethod
    def send_forgot_password_email(self, to_email: str, token: str) -> bool:
        pass

    @abstractmethod
    def send_security_alert(self, to_email: str, alert_details: str) -> bool:
        pass


class MockEmailService(EmailService):
    """
    Print/Console email service logger for local development and integration tests.
    """
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        logger.info("=== [Mock Email Sent] ===")
        logger.info(f"To:      {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body:\n{html_content}")
        logger.info("==========================")
        return True

    def send_verification_email(self, to_email: str, token: str) -> bool:
        subject = "Verify Your Account"
        verify_url = f"http://localhost:8000/api/v1/auth/verify-email?token={token}"
        html_content = f"<p>Please verify your email address by clicking <a href='{verify_url}'>here</a>.</p>"
        return self.send_email(to_email, subject, html_content)

    def send_welcome_email(self, to_email: str, name: str) -> bool:
        subject = "Welcome to AI Interview Platform"
        html_content = f"<p>Welcome, {name}! Your registration was successful.</p>"
        return self.send_email(to_email, subject, html_content)

    def send_forgot_password_email(self, to_email: str, token: str) -> bool:
        subject = "Reset Your Password"
        reset_url = f"http://localhost:8000/api/v1/auth/reset-password?token={token}"
        html_content = f"<p>You requested a password reset. Click <a href='{reset_url}'>here</a> to verify and enter your new password.</p>"
        return self.send_email(to_email, subject, html_content)

    def send_security_alert(self, to_email: str, alert_details: str) -> bool:
        subject = "Security Alert: Account Activity Warning"
        html_content = f"<p>Attention, we detected abnormal activity: <b>{alert_details}</b>. Please check your active devices list.</p>"
        return self.send_email(to_email, subject, html_content)
