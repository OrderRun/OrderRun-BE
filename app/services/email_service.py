"""
Email service for sending emails via SMTP.

This module provides a centralized service for:
- Sending single and bulk emails
- Rendering HTML email templates with Jinja2
- Managing email delivery status and logging
- Async email sending via aiosmtplib
"""
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

try:
    import aiosmtplib
    AIOSMTPLIB_AVAILABLE = True
except ImportError:
    AIOSMTPLIB_AVAILABLE = False
    logging.warning("aiosmtplib package not installed. Email functionality will be disabled.")

try:
    from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logging.warning("jinja2 package not installed. Email template functionality will be disabled.")

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.email import EmailLog, EmailStatus
from app.schemas.email import (
    EmailSendRequest,
    EmailBulkSendRequest,
    EmailTemplateRequest,
    EmailSendResult,
    EmailBulkSendResult,
    EmailRecipient
)


logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending emails via SMTP.

    This service handles:
    - SMTP connection management
    - Email composition and sending
    - Template rendering with Jinja2
    - Delivery status tracking and logging
    - Error handling and retry logic
    """

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_use_tls: Optional[bool] = None,
        smtp_use_ssl: Optional[bool] = None,
        default_from_email: Optional[str] = None,
        default_from_name: Optional[str] = None,
        template_dir: Optional[str] = None
    ):
        """
        Initialize Email service.

        Args:
            smtp_host: SMTP server hostname (default from settings)
            smtp_port: SMTP server port (default from settings)
            smtp_username: SMTP username (default from settings)
            smtp_password: SMTP password (default from settings)
            smtp_use_tls: Use TLS (default from settings)
            smtp_use_ssl: Use SSL (default from settings)
            default_from_email: Default sender email (default from settings)
            default_from_name: Default sender name (default from settings)
            template_dir: Directory containing email templates (default: app/templates/email)
        """
        self.smtp_host = smtp_host or settings.smtp_host
        self.smtp_port = smtp_port or settings.smtp_port
        self.smtp_username = smtp_username or settings.smtp_username
        self.smtp_password = smtp_password or settings.smtp_password
        self.smtp_use_tls = smtp_use_tls if smtp_use_tls is not None else settings.smtp_use_tls
        self.smtp_use_ssl = smtp_use_ssl if smtp_use_ssl is not None else settings.smtp_use_ssl
        self.default_from_email = default_from_email or settings.email_from or self.smtp_username
        self.default_from_name = default_from_name or settings.email_from_name

        # Setup template environment
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            # Default to app/templates/email
            app_dir = Path(__file__).parent.parent
            self.template_dir = app_dir / "templates" / "email"

        self.jinja_env = None
        if JINJA2_AVAILABLE and self.template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=True
            )
            logger.info(f"Email template directory loaded: {self.template_dir}")
        elif JINJA2_AVAILABLE:
            logger.warning(f"Email template directory not found: {self.template_dir}")

        if not AIOSMTPLIB_AVAILABLE:
            logger.error("aiosmtplib is not installed. Email sending will fail.")

        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP credentials not configured. Email sending may fail.")

    def _create_message(
        self,
        to_email: str,
        to_name: Optional[str],
        subject: str,
        body_text: Optional[str],
        body_html: Optional[str],
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> MIMEMultipart:
        """
        Create an email message.

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body
            from_email: Sender email (optional override)
            from_name: Sender name (optional override)

        Returns:
            MIMEMultipart message object
        """
        message = MIMEMultipart("alternative")

        # Set sender
        sender_email = from_email or self.default_from_email
        sender_name = from_name or self.default_from_name
        if sender_name:
            message["From"] = f"{sender_name} <{sender_email}>"
        else:
            message["From"] = sender_email

        # Set recipient
        if to_name:
            message["To"] = f"{to_name} <{to_email}>"
        else:
            message["To"] = to_email

        message["Subject"] = subject

        # Add plain text part
        if body_text:
            part_text = MIMEText(body_text, "plain", "utf-8")
            message.attach(part_text)

        # Add HTML part
        if body_html:
            part_html = MIMEText(body_html, "html", "utf-8")
            message.attach(part_html)

        return message

    async def _send_smtp(self, message: MIMEMultipart) -> None:
        """
        Send email via SMTP.

        Args:
            message: Email message to send

        Raises:
            Exception: If SMTP send fails
        """
        if not AIOSMTPLIB_AVAILABLE:
            raise RuntimeError("aiosmtplib is not installed")

        try:
            if self.smtp_use_ssl:
                # Use SSL connection
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_username,
                    password=self.smtp_password,
                    use_tls=False,
                    start_tls=False
                )
            elif self.smtp_use_tls:
                # Use TLS connection (STARTTLS)
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_username,
                    password=self.smtp_password,
                    use_tls=False,
                    start_tls=True
                )
            else:
                # No encryption
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_username,
                    password=self.smtp_password,
                    use_tls=False,
                    start_tls=False
                )

            logger.info(f"Email sent successfully to {message['To']}")

        except Exception as e:
            logger.error(f"Failed to send email to {message['To']}: {str(e)}")
            raise

    def _create_email_log(
        self,
        db: Session,
        to_email: str,
        to_name: Optional[str],
        from_email: str,
        from_name: Optional[str],
        subject: str,
        body_text: Optional[str],
        body_html: Optional[str],
        template_name: Optional[str] = None,
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: EmailStatus = EmailStatus.PENDING
    ) -> EmailLog:
        """
        Create an email log entry in the database.

        Args:
            db: Database session
            to_email: Recipient email
            to_name: Recipient name
            from_email: Sender email
            from_name: Sender name
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body
            template_name: Template name if using template
            user_id: Associated user ID
            metadata: Additional metadata
            status: Initial email status

        Returns:
            Created EmailLog object
        """
        email_log = EmailLog(
            to_email=to_email,
            to_name=to_name,
            from_email=from_email,
            from_name=from_name,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            template_name=template_name,
            user_id=user_id,
            status=status,
            metadata=json.dumps(metadata) if metadata else None
        )

        db.add(email_log)
        db.commit()
        db.refresh(email_log)

        return email_log

    def _update_email_log_status(
        self,
        db: Session,
        email_log: EmailLog,
        status: EmailStatus,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update email log status.

        Args:
            db: Database session
            email_log: EmailLog object to update
            status: New status
            error_message: Error message if failed
        """
        email_log.status = status

        if status == EmailStatus.SENT:
            email_log.sent_at = datetime.utcnow()
        elif status == EmailStatus.FAILED:
            email_log.error_message = error_message
            email_log.retry_count += 1

        db.commit()
        db.refresh(email_log)

    async def send_email(
        self,
        db: Session,
        request: EmailSendRequest
    ) -> EmailSendResult:
        """
        Send a single email.

        Args:
            db: Database session
            request: Email send request

        Returns:
            EmailSendResult with send status
        """
        from_email = request.from_email or self.default_from_email
        from_name = request.from_name or self.default_from_name

        # Create email log
        email_log = self._create_email_log(
            db=db,
            to_email=request.to.email,
            to_name=request.to.name,
            from_email=from_email,
            from_name=from_name,
            subject=request.subject,
            body_text=request.body_text,
            body_html=request.body_html,
            user_id=request.user_id,
            metadata=request.metadata
        )

        try:
            # Create message
            message = self._create_message(
                to_email=request.to.email,
                to_name=request.to.name,
                subject=request.subject,
                body_text=request.body_text,
                body_html=request.body_html,
                from_email=from_email,
                from_name=from_name
            )

            # Send via SMTP
            await self._send_smtp(message)

            # Update log status
            self._update_email_log_status(db, email_log, EmailStatus.SENT)

            return EmailSendResult(
                success=True,
                email_log_id=email_log.id,
                to_email=request.to.email
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send email to {request.to.email}: {error_msg}")

            # Update log status
            self._update_email_log_status(db, email_log, EmailStatus.FAILED, error_msg)

            return EmailSendResult(
                success=False,
                email_log_id=email_log.id,
                to_email=request.to.email,
                error_message=error_msg
            )

    async def send_bulk_email(
        self,
        db: Session,
        request: EmailBulkSendRequest
    ) -> EmailBulkSendResult:
        """
        Send emails to multiple recipients.

        Args:
            db: Database session
            request: Bulk email send request

        Returns:
            EmailBulkSendResult with aggregated results
        """
        results = []
        successful = 0
        failed = 0

        for recipient in request.recipients:
            # Create individual send request
            send_request = EmailSendRequest(
                to=recipient,
                subject=request.subject,
                body_text=request.body_text,
                body_html=request.body_html,
                from_email=request.from_email,
                from_name=request.from_name,
                metadata=request.metadata
            )

            # Send email
            result = await self.send_email(db, send_request)
            results.append(result)

            if result.success:
                successful += 1
            else:
                failed += 1

        return EmailBulkSendResult(
            total=len(request.recipients),
            successful=successful,
            failed=failed,
            results=results
        )

    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Render an email template with context variables.

        Args:
            template_name: Template filename (with or without .html extension)
            context: Template context variables

        Returns:
            Rendered HTML string

        Raises:
            TemplateNotFound: If template does not exist
            RuntimeError: If Jinja2 is not available
        """
        if not JINJA2_AVAILABLE:
            raise RuntimeError("Jinja2 is not installed")

        if not self.jinja_env:
            raise RuntimeError("Template environment not initialized")

        # Add .html extension if not present
        if not template_name.endswith(".html"):
            template_name = f"{template_name}.html"

        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            logger.error(f"Email template not found: {template_name}")
            raise

    async def send_template_email(
        self,
        db: Session,
        request: EmailTemplateRequest
    ) -> EmailSendResult:
        """
        Send an email using a template.

        Args:
            db: Database session
            request: Template email request

        Returns:
            EmailSendResult with send status
        """
        try:
            # Render template
            body_html = self.render_template(request.template_name, request.context)

            from_email = request.from_email or self.default_from_email
            from_name = request.from_name or self.default_from_name

            # Create email log
            email_log = self._create_email_log(
                db=db,
                to_email=request.to.email,
                to_name=request.to.name,
                from_email=from_email,
                from_name=from_name,
                subject=request.subject,
                body_text=None,
                body_html=body_html,
                template_name=request.template_name,
                user_id=request.user_id,
                metadata=request.metadata
            )

            # Create message
            message = self._create_message(
                to_email=request.to.email,
                to_name=request.to.name,
                subject=request.subject,
                body_text=None,
                body_html=body_html,
                from_email=from_email,
                from_name=from_name
            )

            # Send via SMTP
            await self._send_smtp(message)

            # Update log status
            self._update_email_log_status(db, email_log, EmailStatus.SENT)

            return EmailSendResult(
                success=True,
                email_log_id=email_log.id,
                to_email=request.to.email
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send template email to {request.to.email}: {error_msg}")

            # Try to create failed log if we haven't already
            try:
                email_log = self._create_email_log(
                    db=db,
                    to_email=request.to.email,
                    to_name=request.to.name,
                    from_email=request.from_email or self.default_from_email,
                    from_name=request.from_name or self.default_from_name,
                    subject=request.subject,
                    body_text=None,
                    body_html=None,
                    template_name=request.template_name,
                    user_id=request.user_id,
                    metadata=request.metadata,
                    status=EmailStatus.FAILED
                )
                email_log.error_message = error_msg
                db.commit()
            except Exception:
                pass

            return EmailSendResult(
                success=False,
                email_log_id=None,
                to_email=request.to.email,
                error_message=error_msg
            )

    def get_email_logs(
        self,
        db: Session,
        user_id: Optional[int] = None,
        status: Optional[EmailStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[EmailLog]:
        """
        Get email logs with optional filtering.

        Args:
            db: Database session
            user_id: Filter by user ID
            status: Filter by status
            limit: Maximum number of logs to return
            offset: Number of logs to skip

        Returns:
            List of EmailLog objects
        """
        query = db.query(EmailLog)

        if user_id is not None:
            query = query.filter(EmailLog.user_id == user_id)

        if status is not None:
            query = query.filter(EmailLog.status == status)

        query = query.order_by(EmailLog.created_at.desc())
        query = query.limit(limit).offset(offset)

        return query.all()


# Global email service instance
email_service = EmailService()
