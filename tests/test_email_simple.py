"""Simple tests for email infrastructure."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.infra.email import EmailClient, get_email_client, close_email_client, render_email_template


class TestEmailClient:
    """Test EmailClient basic functionality."""

    def test_email_client_initialization(self):
        """Test EmailClient can be initialized."""
        client = EmailClient()
        assert client._connection is None
        assert client._last_used is None
        assert client._connection_timeout == 300

    @patch('app.infra.email.settings')
    @pytest.mark.asyncio
    async def test_send_email_disabled(self, mock_settings):
        """Test sending email when email verification is disabled."""
        mock_settings.email.enable_email_verification = False

        client = EmailClient()
        result = await client.send_email("test@example.com", "Test", "<h1>Test</h1>")

        assert result is True

    @patch('app.infra.email.settings')
    @pytest.mark.asyncio
    async def test_send_email_no_smtp_host(self, mock_settings):
        """Test sending email when SMTP not configured."""
        mock_settings.email.enable_email_verification = True
        mock_settings.email.smtp_host = None

        client = EmailClient()
        result = await client.send_email("test@example.com", "Test", "<h1>Test</h1>")

        assert result is False


class TestEmailClientSingleton:
    """Test email client singleton functions."""

    def test_get_email_client(self):
        """Test getting email client instance."""
        # Reset global state
        import app.infra.email
        app.infra.email._email_client = None

        client1 = get_email_client()
        client2 = get_email_client()

        assert client1 is client2
        assert isinstance(client1, EmailClient)

    @pytest.mark.asyncio
    async def test_close_email_client(self):
        """Test closing email client."""
        # Setup
        import app.infra.email
        app.infra.email._email_client = Mock()

        with patch.object(app.infra.email._email_client, 'close', new_callable=AsyncMock):
            await close_email_client()
            assert app.infra.email._email_client is None


class TestEmailTemplateRendering:
    """Test email template rendering."""

    def test_render_verification_template(self):
        """Test rendering verification email template."""
        context = {
            'verification_url': 'https://qeem.com/verify?token=abc123'
        }

        html_content, text_content = render_email_template(
            'verification', context)

        assert 'Welcome to Qeem!' in html_content
        assert 'Verify Your Email Address' in html_content
        assert 'https://qeem.com/verify?token=abc123' in html_content
        assert 'Welcome to Qeem!' in text_content
        assert 'https://qeem.com/verify?token=abc123' in text_content

    def test_render_default_template(self):
        """Test rendering default template."""
        context = {'message': 'Test message'}

        html_content, text_content = render_email_template(
            'unknown_template', context)

        assert 'unknown_template' in html_content
        assert 'Test message' in html_content
        assert 'unknown_template' in text_content
        assert 'Test message' in text_content
