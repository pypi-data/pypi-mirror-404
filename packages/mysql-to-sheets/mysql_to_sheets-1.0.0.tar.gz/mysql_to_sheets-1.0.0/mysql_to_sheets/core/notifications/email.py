"""Email notification backend using SMTP.

This module provides email notifications for sync completion alerts
using Python's smtplib with TLS/SSL support.
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from mysql_to_sheets.core.exceptions import NotificationError
from mysql_to_sheets.core.logging_utils import get_module_logger
from mysql_to_sheets.core.notifications.base import (
    NotificationBackend,
    NotificationConfig,
    NotificationPayload,
)

logger = get_module_logger(__name__)


class EmailNotificationBackend(NotificationBackend):
    """Email notification backend using SMTP.

    Sends formatted HTML emails with sync results. Supports TLS
    and SSL connections.
    """

    @property
    def name(self) -> str:
        """Get the backend name."""
        return "email"

    def is_configured(self, config: NotificationConfig) -> bool:
        """Check if email notification is configured."""
        return config.has_email_config()

    def send(
        self,
        payload: NotificationPayload,
        config: NotificationConfig,
    ) -> bool:
        """Send email notification.

        Args:
            payload: Notification data.
            config: Notification configuration.

        Returns:
            True if email was sent successfully.

        Raises:
            NotificationError: If sending fails.
        """
        if not self.is_configured(config):
            raise NotificationError(
                message="Email notification not configured",
                backend=self.name,
            )

        recipients = config.get_email_recipients()
        if not recipients:
            raise NotificationError(
                message="No email recipients configured",
                backend=self.name,
            )

        # Build email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = self._build_subject(payload)
        msg["From"] = config.smtp_from
        msg["To"] = ", ".join(recipients)

        # Create plain text and HTML versions
        text_content = self._build_text_body(payload)
        html_content = self._build_html_body(payload)

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        try:
            if config.smtp_use_tls:
                # TLS connection (STARTTLS on port 587)
                context = ssl.create_default_context()
                with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()
                    if config.smtp_user and config.smtp_password:
                        server.login(config.smtp_user, config.smtp_password)
                    server.sendmail(config.smtp_from, recipients, msg.as_string())
            else:
                # Plain SMTP (or implicit SSL on port 465)
                if config.smtp_port == 465:
                    # Implicit SSL
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL(
                        config.smtp_host, config.smtp_port, context=context, timeout=30
                    ) as server:
                        if config.smtp_user and config.smtp_password:
                            server.login(config.smtp_user, config.smtp_password)
                        server.sendmail(config.smtp_from, recipients, msg.as_string())
                else:
                    # Plain SMTP (not recommended)
                    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as server:
                        if config.smtp_user and config.smtp_password:
                            server.login(config.smtp_user, config.smtp_password)
                        server.sendmail(config.smtp_from, recipients, msg.as_string())

            logger.info(f"Email sent to {len(recipients)} recipient(s)")
            return True

        except smtplib.SMTPAuthenticationError as e:
            raise NotificationError(
                message="SMTP authentication failed",
                backend=self.name,
                original_error=e,
            ) from e
        except smtplib.SMTPConnectError as e:
            raise NotificationError(
                message=f"Failed to connect to SMTP server {config.smtp_host}:{config.smtp_port}",
                backend=self.name,
                original_error=e,
            ) from e
        except smtplib.SMTPException as e:
            raise NotificationError(
                message=f"SMTP error: {e}",
                backend=self.name,
                original_error=e,
            ) from e
        except OSError as e:
            raise NotificationError(
                message=f"Failed to send email: {e}",
                backend=self.name,
                original_error=e,
            ) from e

    def _build_subject(self, payload: NotificationPayload) -> str:
        """Build email subject line.

        Args:
            payload: Notification data.

        Returns:
            Email subject string.
        """
        status = payload.status_text
        if payload.sheet_id:
            return f"[MySQL to Sheets] {status} - {payload.sheet_id[:20]}..."
        return f"[MySQL to Sheets] {status}"

    def _build_text_body(self, payload: NotificationPayload) -> str:
        """Build plain text email body.

        Args:
            payload: Notification data.

        Returns:
            Plain text email body.
        """
        lines = [
            f"MySQL to Google Sheets Sync - {payload.status_text}",
            "",
            f"Status: {'Success' if payload.success else 'Failed'}",
            f"Rows Synced: {payload.rows_synced}",
        ]

        if payload.sheet_id:
            lines.append(f"Sheet ID: {payload.sheet_id}")
        if payload.worksheet:
            lines.append(f"Worksheet: {payload.worksheet}")
        if payload.duration_ms:
            lines.append(f"Duration: {payload.duration_ms:.2f}ms")
        if payload.source:
            lines.append(f"Source: {payload.source}")

        lines.append(f"Timestamp: {payload.timestamp.isoformat()}")

        if payload.message:
            lines.extend(["", f"Message: {payload.message}"])

        if payload.error:
            lines.extend(["", f"Error: {payload.error}"])

        return "\n".join(lines)

    def _build_html_body(self, payload: NotificationPayload) -> str:
        """Build HTML email body.

        Args:
            payload: Notification data.

        Returns:
            HTML email body.
        """
        status_color = "#28a745" if payload.success else "#dc3545"
        status_text = payload.status_text

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background: {status_color}; color: white; padding: 20px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .content {{ padding: 20px; }}
        .stat {{ display: inline-block; margin: 10px; padding: 10px 15px; background: #f8f9fa; border-radius: 4px; }}
        .stat-label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
        .stat-value {{ font-size: 18px; font-weight: bold; color: #333; }}
        .details {{ margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 4px; }}
        .details p {{ margin: 5px 0; color: #555; }}
        .error {{ margin-top: 20px; padding: 15px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; }}
        .footer {{ padding: 15px; text-align: center; font-size: 12px; color: #999; border-top: 1px solid #eee; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{payload.status_emoji} {status_text}</h1>
        </div>
        <div class="content">
            <div style="text-align: center;">
                <div class="stat">
                    <div class="stat-label">Rows Synced</div>
                    <div class="stat-value">{payload.rows_synced}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Duration</div>
                    <div class="stat-value">{payload.duration_ms:.1f}ms</div>
                </div>
            </div>
            <div class="details">
                <p><strong>Sheet ID:</strong> {payload.sheet_id or "N/A"}</p>
                <p><strong>Worksheet:</strong> {payload.worksheet or "N/A"}</p>
                <p><strong>Source:</strong> {payload.source}</p>
                <p><strong>Timestamp:</strong> {payload.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
            </div>
"""

        if payload.message:
            html += f"""
            <div class="details">
                <p><strong>Message:</strong> {payload.message}</p>
            </div>
"""

        if payload.error:
            html += f"""
            <div class="error">
                <p><strong>Error:</strong> {payload.error}</p>
            </div>
"""

        html += """
        </div>
        <div class="footer">
            MySQL to Google Sheets Sync
        </div>
    </div>
</body>
</html>
"""
        return html
