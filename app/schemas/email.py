"""
Pydantic schemas for email-related request/response models.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr, ConfigDict

from app.models.email import EmailStatus


# ========== Email Send Request Schemas ==========

class EmailRecipient(BaseModel):
    """Schema for email recipient information."""
    email: EmailStr = Field(..., description="Recipient email address")
    name: Optional[str] = Field(None, max_length=255, description="Recipient name")

    model_config = ConfigDict(from_attributes=True)


class EmailSendRequest(BaseModel):
    """
    Schema for sending an email.

    Can send either plain text, HTML, or both.
    """
    to: EmailRecipient = Field(..., description="Email recipient")
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject")
    body_text: Optional[str] = Field(None, description="Plain text email body")
    body_html: Optional[str] = Field(None, description="HTML email body")

    # Optional overrides
    from_email: Optional[EmailStr] = Field(None, description="Custom sender email (overrides default)")
    from_name: Optional[str] = Field(None, max_length=255, description="Custom sender name (overrides default)")

    # Optional associations
    user_id: Optional[int] = Field(None, description="Associated user ID for logging")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for logging")

    model_config = ConfigDict(from_attributes=True)


class EmailBulkSendRequest(BaseModel):
    """Schema for sending emails to multiple recipients."""
    recipients: List[EmailRecipient] = Field(..., min_length=1, description="List of recipients")
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject")
    body_text: Optional[str] = Field(None, description="Plain text email body")
    body_html: Optional[str] = Field(None, description="HTML email body")

    # Optional overrides
    from_email: Optional[EmailStr] = Field(None, description="Custom sender email")
    from_name: Optional[str] = Field(None, max_length=255, description="Custom sender name")

    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    model_config = ConfigDict(from_attributes=True)


class EmailTemplateRequest(BaseModel):
    """
    Schema for sending email using a template.

    Template will be rendered with provided context variables.
    """
    to: EmailRecipient = Field(..., description="Email recipient")
    template_name: str = Field(..., min_length=1, max_length=100, description="Template name (without .html extension)")
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject")
    context: Dict[str, Any] = Field(default_factory=dict, description="Template context variables")

    # Optional overrides
    from_email: Optional[EmailStr] = Field(None, description="Custom sender email")
    from_name: Optional[str] = Field(None, max_length=255, description="Custom sender name")

    # Optional associations
    user_id: Optional[int] = Field(None, description="Associated user ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    model_config = ConfigDict(from_attributes=True)


# ========== Email Response Schemas ==========

class EmailSendResult(BaseModel):
    """Result of a single email send operation."""
    success: bool = Field(..., description="Whether the email was sent successfully")
    email_log_id: Optional[int] = Field(None, description="Database ID of the email log")
    to_email: str = Field(..., description="Recipient email address")
    error_message: Optional[str] = Field(None, description="Error message if send failed")

    model_config = ConfigDict(from_attributes=True)


class EmailBulkSendResult(BaseModel):
    """Result of bulk email send operation."""
    total: int = Field(..., description="Total number of emails attempted")
    successful: int = Field(..., description="Number of successful sends")
    failed: int = Field(..., description="Number of failed sends")
    results: List[EmailSendResult] = Field(..., description="Individual results for each email")

    model_config = ConfigDict(from_attributes=True)


class EmailLogResponse(BaseModel):
    """Schema for email log response."""
    id: int
    to_email: str
    to_name: Optional[str]
    from_email: str
    from_name: Optional[str]
    subject: str
    template_name: Optional[str]
    user_id: Optional[int]
    status: EmailStatus
    error_message: Optional[str]
    retry_count: int
    created_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class EmailStatsResponse(BaseModel):
    """Schema for email statistics."""
    total_sent: int = Field(..., description="Total emails sent")
    successful: int = Field(..., description="Successfully delivered emails")
    failed: int = Field(..., description="Failed email sends")
    pending: int = Field(..., description="Pending emails")

    model_config = ConfigDict(from_attributes=True)
