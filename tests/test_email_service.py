"""
Test cases for email service functionality.

NOTE: These tests are examples and require proper SMTP configuration to run.
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.email_service import EmailService, email_service
from app.schemas.email import (
    EmailRecipient,
    EmailSendRequest,
    EmailBulkSendRequest,
    EmailTemplateRequest
)
from app.models.email import EmailStatus


# Example test showing how to use the email service
@pytest.mark.asyncio
async def test_send_simple_email_example():
    """
    Example test showing how to send a simple email.

    NOTE: This test is skipped by default as it requires SMTP configuration.
    To run this test:
    1. Set up SMTP credentials in .env file
    2. Remove the @pytest.mark.skip decorator
    3. Update the recipient email address
    """
    pytest.skip("Requires SMTP configuration")

    # Mock database session (you'll need proper DB session in real tests)
    from app.core.database import get_db
    db = next(get_db())

    # Create email request
    request = EmailSendRequest(
        to=EmailRecipient(
            email="test@example.com",
            name="Test User"
        ),
        subject="Test Email from OrderRun",
        body_text="This is a plain text email.",
        body_html="<h1>This is an HTML email</h1><p>Testing email service.</p>"
    )

    # Send email
    result = await email_service.send_email(db, request)

    # Assert result
    assert result.success is True
    assert result.email_log_id is not None
    assert result.to_email == "test@example.com"
    assert result.error_message is None


@pytest.mark.asyncio
async def test_send_bulk_email_example():
    """
    Example test showing how to send bulk emails.

    NOTE: This test is skipped by default as it requires SMTP configuration.
    """
    pytest.skip("Requires SMTP configuration")

    from app.core.database import get_db
    db = next(get_db())

    # Create bulk email request
    request = EmailBulkSendRequest(
        recipients=[
            EmailRecipient(email="user1@example.com", name="User 1"),
            EmailRecipient(email="user2@example.com", name="User 2"),
            EmailRecipient(email="user3@example.com", name="User 3")
        ],
        subject="Bulk Email Test",
        body_html="<p>This is a bulk email sent to multiple recipients.</p>"
    )

    # Send bulk emails
    result = await email_service.send_bulk_email(db, request)

    # Assert results
    assert result.total == 3
    assert result.successful + result.failed == 3
    assert len(result.results) == 3


@pytest.mark.asyncio
async def test_send_template_email_example():
    """
    Example test showing how to send an email using a template.

    NOTE: This test is skipped by default as it requires SMTP configuration.
    """
    pytest.skip("Requires SMTP configuration")

    from app.core.database import get_db
    db = next(get_db())

    # Create template email request
    request = EmailTemplateRequest(
        to=EmailRecipient(
            email="newuser@example.com",
            name="New User"
        ),
        template_name="welcome",  # Uses welcome.html template
        subject="Welcome to OrderRun!",
        context={
            "user_name": "New User",
            "verification_link": "https://orderrun.com/verify?token=abc123",
            "current_year": datetime.now().year
        }
    )

    # Send template email
    result = await email_service.send_template_email(db, request)

    # Assert result
    assert result.success is True
    assert result.email_log_id is not None


def test_render_template():
    """Test template rendering without sending email."""
    # Test welcome template
    html = email_service.render_template(
        "welcome",
        {
            "user_name": "Test User",
            "verification_link": "https://example.com/verify",
            "current_year": 2025
        }
    )

    assert "Test User" in html
    assert "https://example.com/verify" in html
    assert "환영합니다" in html


def test_render_notification_template():
    """Test notification template rendering."""
    html = email_service.render_template(
        "notification",
        {
            "user_name": "Test User",
            "notification_title": "New Proposal",
            "notification_message": "You have received a new proposal for your request.",
            "notification_details": {
                "Proposal ID": "12345",
                "Runner": "John Doe",
                "Amount": "10,000원"
            },
            "action_url": "https://orderrun.com/proposals/12345",
            "action_text": "View Proposal"
        }
    )

    assert "Test User" in html
    assert "New Proposal" in html
    assert "12345" in html
    assert "John Doe" in html


def test_render_password_reset_template():
    """Test password reset template rendering."""
    html = email_service.render_template(
        "password_reset",
        {
            "user_name": "Test User",
            "reset_link": "https://orderrun.com/reset-password?token=xyz789",
            "expiry_hours": "24"
        }
    )

    assert "Test User" in html
    assert "비밀번호 재설정" in html
    assert "https://orderrun.com/reset-password?token=xyz789" in html
    assert "24" in html


# Example of how to use email service in your application code
"""
# In your API endpoint or service:

from app.services.email_service import email_service
from app.schemas.email import EmailRecipient, EmailSendRequest

async def send_welcome_email(db: Session, user_email: str, user_name: str):
    '''Send welcome email to new user.'''

    request = EmailTemplateRequest(
        to=EmailRecipient(email=user_email, name=user_name),
        template_name="welcome",
        subject="Welcome to OrderRun!",
        context={
            "user_name": user_name,
            "current_year": datetime.now().year
        }
    )

    result = await email_service.send_template_email(db, request)
    return result


async def send_proposal_notification(db: Session, user_email: str, proposal_id: int):
    '''Send notification when user receives a new proposal.'''

    request = EmailTemplateRequest(
        to=EmailRecipient(email=user_email),
        template_name="notification",
        subject="New Proposal Received",
        context={
            "notification_title": "New Proposal",
            "notification_message": "You have received a new proposal for your request.",
            "action_url": f"https://orderrun.com/proposals/{proposal_id}",
            "action_text": "View Proposal"
        }
    )

    result = await email_service.send_template_email(db, request)
    return result
"""
