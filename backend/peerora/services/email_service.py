"""Sending email (used for password-reset links).

Backends (EMAIL_BACKEND, see config.py):
  smtp   - real delivery through any SMTP provider (Gmail, SendGrid, Brevo,
           Mailgun, Amazon SES, ...). Uses Python's standard smtplib.
  outbox - local development only: each email is written as a .eml file to
           EMAIL_OUTBOX_DIR (git-ignored). Refused on Vercel, and refused
           when DATABASE_URL is not SQLite unless EMAIL_OUTBOX_ALLOW_REMOTE_DB=true.
  (none) - email is not configured. is_email_configured() is False and callers
           must say so instead of pretending a message was sent.

Message bodies are never logged (they contain reset links).
"""

import logging
import re
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from peerora.config import (
    get_email_backend,
    get_email_outbox_dir,
    get_public_app_url,
    get_smtp_settings,
    is_production_host,
    outbox_allowed_with_remote_database,
    uses_local_database,
)
from peerora.core.timeutils import utcnow

logger = logging.getLogger("peerora.email")


class EmailNotConfiguredError(RuntimeError):
    """No usable email backend is configured."""


class EmailDeliveryError(RuntimeError):
    """The configured backend failed to deliver the message."""


def configuration_problem() -> str | None:
    """Why email cannot be sent, or None when it can. Never contains secrets."""
    backend = get_email_backend()
    if backend is None:
        return "EMAIL_BACKEND is not set to 'smtp' or 'outbox'."
    if not get_public_app_url():
        return "PUBLIC_APP_URL is not set, so reset links cannot be built."
    if backend == "outbox" and is_production_host():
        return "The 'outbox' email backend is for local development and is disabled on Vercel."
    if backend == "outbox" and not uses_local_database() and not outbox_allowed_with_remote_database():
        return ("The 'outbox' email backend only works with a local SQLite database "
                "(set EMAIL_OUTBOX_ALLOW_REMOTE_DB=true to allow it on purpose).")
    if backend == "smtp":
        settings = get_smtp_settings()
        missing = [name for name, key in (("SMTP_HOST", "host"), ("EMAIL_FROM", "sender")) if not settings[key]]
        if missing:
            return f"Missing email settings: {', '.join(missing)}."
    return None


def is_email_configured() -> bool:
    return configuration_problem() is None


def _build_message(to: str, subject: str, body: str, sender: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = to
    message["Subject"] = subject
    message["Date"] = formatdate(localtime=False)
    message["Message-ID"] = make_msgid(domain="peerora")
    # Plain 7-bit text keeps long links on one line (readable outbox files, and
    # clickable in every client); non-ASCII text (e.g. Bangla names) falls back
    # to quoted-printable, which every mail client decodes.
    message.set_content(body, cte="7bit" if body.isascii() else "quoted-printable")
    return message


def _send_smtp(message: EmailMessage) -> None:
    settings = get_smtp_settings()
    context = ssl.create_default_context()
    try:
        if settings["ssl"]:
            server = smtplib.SMTP_SSL(str(settings["host"]), int(settings["port"]), timeout=15, context=context)
        else:
            server = smtplib.SMTP(str(settings["host"]), int(settings["port"]), timeout=15)
        with server as connection:
            if settings["starttls"] and not settings["ssl"]:
                connection.starttls(context=context)
            if settings["username"]:
                connection.login(str(settings["username"]), str(settings["password"]))
            connection.send_message(message)
    except (smtplib.SMTPException, OSError) as error:
        # Only the error type is logged: SMTP errors can echo addresses or server details.
        raise EmailDeliveryError(type(error).__name__) from None


def _write_outbox(message: EmailMessage) -> None:
    folder = get_email_outbox_dir()
    folder.mkdir(parents=True, exist_ok=True)
    safe_to = re.sub(r"[^A-Za-z0-9@._-]", "_", str(message["To"]))[:80]
    path = folder / f"{utcnow():%Y%m%dT%H%M%S%f}-{safe_to}.eml"
    path.write_bytes(bytes(message))
    path.chmod(0o600)  # readable only by the developer
    logger.info("Development email written to the outbox folder (%s).", path.name)


def send_email(to: str, subject: str, body: str) -> None:
    problem = configuration_problem()
    if problem is not None:
        raise EmailNotConfiguredError(problem)
    backend = get_email_backend()
    sender = str(get_smtp_settings()["sender"] or "Peerora <no-reply@peerora.local>")
    message = _build_message(to, subject, body, sender)
    if backend == "smtp":
        _send_smtp(message)
    else:
        _write_outbox(message)
