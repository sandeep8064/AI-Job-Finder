"""
Email Notification Service — Sends HTML email digests of matched job listings.
Uses SMTP (Gmail App Password recommended).
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List

from utils.time_utils import get_ist_strftime

from jinja2 import Template

from config import EmailConfig


# Load email template
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")


def _load_template() -> Template:
    """Load the HTML email template."""
    template_path = os.path.join(TEMPLATE_DIR, "email_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return Template(f.read())


def send_job_digest(
    email_config: EmailConfig,
    scored_jobs: list,
    max_jobs: int = 20,
) -> bool:
    """
    Send an HTML email digest of matched job listings.

    Args:
        email_config: SMTP configuration
        scored_jobs: List of ScoredJob objects (from matcher)
        max_jobs: Maximum number of jobs to include in email

    Returns:
        True if email sent successfully, False otherwise
    """
    if not scored_jobs:
        print("  [Email] No jobs to send.")
        return False

    if not email_config.sender_email or not email_config.sender_password:
        print("  [Email] Email credentials not configured. Skipping email.")
        return False

    if not email_config.recipient_email:
        print("  [Email] Recipient email not configured. Skipping email.")
        return False

    # Limit jobs in email
    top_jobs = scored_jobs[:max_jobs]

    # Render HTML template
    try:
        template = _load_template()
        html_content = template.render(
            jobs=top_jobs,
            total_found=len(scored_jobs),
            date=get_ist_strftime("%B %d, %Y at %I:%M %p IST"),
        )
    except Exception as e:
        print(f"  [Email] Template error: {e}")
        # Fallback: plain text
        html_content = _build_fallback_html(top_jobs, len(scored_jobs))

    # Build email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔍 Ai Job finder: {len(top_jobs)} New Job Matches — {get_ist_strftime('%b %d')}"
    msg["From"] = email_config.sender_email
    msg["To"] = email_config.recipient_email

    # Plain text fallback
    plain_text = _build_plain_text(top_jobs)
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    # Send via SMTP
    try:
        print(f"  [Email] Sending digest with {len(top_jobs)} jobs to {email_config.recipient_email}...")
        with smtplib.SMTP(email_config.smtp_server, email_config.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(email_config.sender_email, email_config.sender_password)
            server.sendmail(
                email_config.sender_email,
                email_config.recipient_email,
                msg.as_string(),
            )
        print("  [Email] ✓ Digest sent successfully!")
        return True
    except smtplib.SMTPAuthenticationError:
        print("  [Email] ✗ Authentication failed. Check your email/password (use Gmail App Password).")
        return False
    except Exception as e:
        print(f"  [Email] ✗ Failed to send: {e}")
        return False


def _build_plain_text(scored_jobs: list) -> str:
    """Build plain text fallback for the email."""
    lines = ["=== Ai Job finder — New Matches ===\n"]
    for i, sj in enumerate(scored_jobs, 1):
        lines.append(f"{i}. {sj.job.title} at {sj.job.company}")
        lines.append(f"   Location: {sj.job.location or 'N/A'}")
        lines.append(f"   Match: {sj.score_pct}%")
        lines.append(f"   Apply: {sj.job.url}")
        lines.append(f"   Reasons: {', '.join(sj.match_reasons)}")
        lines.append("")
    return "\n".join(lines)


def _build_fallback_html(scored_jobs: list, total: int) -> str:
    """Build a simple fallback HTML if template fails."""
    rows = ""
    for sj in scored_jobs:
        rows += f"""
        <tr>
            <td style="padding:12px;border-bottom:1px solid #eee;">
                <strong>{sj.job.title}</strong><br>
                <span style="color:#666;">{sj.job.company} — {sj.job.location or 'N/A'}</span><br>
                <span style="color:#2563eb;">Match: {sj.score_pct}%</span> |
                <a href="{sj.job.url}" style="color:#2563eb;">Apply →</a>
            </td>
        </tr>
        """
    return f"""
    <html><body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:20px;">
    <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:8px;padding:24px;">
        <h2 style="color:#1a1a2e;">🔍 Ai Job finder — {total} Matches Found</h2>
        <table style="width:100%;">{rows}</table>
    </div>
    </body></html>
    """
