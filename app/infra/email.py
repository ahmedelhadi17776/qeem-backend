"""Email infrastructure with SMTP client and template rendering."""

import asyncio
import logging
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, Any
import smtplib
from smtplib import SMTP, SMTPAuthenticationError, SMTPException

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailClient:
    """SMTP email client with connection pooling and retry logic."""
    
    def __init__(self):
        self._connection: Optional[SMTP] = None
        self._last_used = None
        self._connection_timeout = 300  # 5 minutes
    
    async def _get_connection(self) -> SMTP:
        """Get or create SMTP connection with pooling."""
        now = datetime.now()
        
        # Reuse existing connection if it's still valid
        if (self._connection and 
            self._last_used and 
            (now - self._last_used).seconds < self._connection_timeout):
            try:
                # Test connection
                self._connection.noop()
                return self._connection
            except (SMTPException, OSError):
                # Connection is dead, close it
                try:
                    self._connection.quit()
                except:
                    pass
                self._connection = None
        
        # Create new connection
        if not settings.email.smtp_host:
            raise ValueError("SMTP host not configured")
        
        try:
            # Run SMTP connection in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self._connection = await loop.run_in_executor(
                None, self._create_smtp_connection
            )
            self._last_used = now
            return self._connection
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            raise
    
    def _create_smtp_connection(self) -> SMTP:
        """Create SMTP connection (runs in thread pool)."""
        smtp = SMTP(settings.email.smtp_host, settings.email.smtp_port)
        
        if settings.email.smtp_use_tls:
            smtp.starttls()
        
        if settings.email.smtp_username and settings.email.smtp_password:
            smtp.login(settings.email.smtp_username, settings.email.smtp_password)
        
        return smtp
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """Send email with retry logic.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text content (optional)
            from_email: Sender email (uses default if not provided)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not settings.email.enable_email_verification:
            logger.info("Email verification disabled, skipping email send")
            return True
        
        if not settings.email.smtp_host:
            logger.warning("SMTP not configured, skipping email send")
            return False
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                connection = await self._get_connection()
                
                # Create message
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = from_email or settings.email.smtp_from_email
                msg['To'] = to_email
                
                # Add text content
                if text_content:
                    text_part = MIMEText(text_content, 'plain', 'utf-8')
                    msg.attach(text_part)
                
                # Add HTML content
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
                
                # Send email
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, connection.send_message, msg
                )
                
                logger.info(f"Email sent successfully to {to_email}")
                return True
                
            except SMTPAuthenticationError as e:
                logger.error(f"SMTP authentication failed: {e}")
                return False
            except SMTPException as e:
                logger.warning(f"SMTP error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    # Reset connection for retry
                    if self._connection:
                        try:
                            self._connection.quit()
                        except:
                            pass
                        self._connection = None
                else:
                    logger.error(f"Failed to send email after {max_retries} attempts")
                    return False
            except Exception as e:
                logger.error(f"Unexpected error sending email: {e}")
                return False
        
        return False
    
    async def close(self):
        """Close SMTP connection."""
        if self._connection:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._connection.quit)
            except:
                pass
            finally:
                self._connection = None


# Global email client instance
_email_client: Optional[EmailClient] = None


def get_email_client() -> EmailClient:
    """Get global email client instance."""
    global _email_client
    if _email_client is None:
        _email_client = EmailClient()
    return _email_client


async def close_email_client():
    """Close global email client."""
    global _email_client
    if _email_client:
        await _email_client.close()
        _email_client = None


def render_email_template(template_name: str, context: Dict[str, Any]) -> tuple[str, str]:
    """Render email template with context.
    
    Args:
        template_name: Name of the template (without extension)
        context: Template context variables
        
    Returns:
        Tuple of (html_content, text_content)
    """
    # Simple template rendering for MVP
    # In production, you'd use Jinja2 or similar
    
    if template_name == "verification":
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Email - Qeem</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #2563eb;">Welcome to Qeem!</h1>
            </div>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="color: #1e293b; margin-top: 0;">Verify Your Email Address</h2>
                <p style="color: #64748b; line-height: 1.6;">
                    Thank you for registering with Qeem! To complete your registration and start using our 
                    AI-powered freelance rate calculator, please verify your email address.
                </p>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{context['verification_url']}" 
                   style="background-color: #2563eb; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px; font-weight: bold; 
                          display: inline-block;">
                    Verify Email Address
                </a>
            </div>
            
            <div style="background-color: #fef2f2; padding: 15px; border-radius: 6px; margin-top: 20px;">
                <p style="color: #dc2626; margin: 0; font-size: 14px;">
                    <strong>Important:</strong> This verification link will expire in 24 hours. 
                    If you didn't create an account with Qeem, please ignore this email.
                </p>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                <p style="color: #64748b; font-size: 14px; text-align: center;">
                    If the button doesn't work, copy and paste this link into your browser:<br>
                    <a href="{context['verification_url']}" style="color: #2563eb; word-break: break-all;">
                        {context['verification_url']}
                    </a>
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Qeem!
        
        Thank you for registering with Qeem! To complete your registration and start using our 
        AI-powered freelance rate calculator, please verify your email address.
        
        Click the link below to verify your email:
        {context['verification_url']}
        
        Important: This verification link will expire in 24 hours. 
        If you didn't create an account with Qeem, please ignore this email.
        
        Best regards,
        The Qeem Team
        """
        
        return html_content, text_content
    
    # Default template
    html_content = f"<html><body><h1>{template_name}</h1><p>{context}</p></body></html>"
    text_content = f"{template_name}\n\n{context}"
    return html_content, text_content
