"""SMTP e-mail delivery shared by password recovery and password change."""

import html as html_lib
import logging
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import parseaddr


logger = logging.getLogger("nivora")


@dataclass
class EmailResult:
    sent: bool
    error: str | None = None


class EmailService:
    """Sends e-mails with the NIVORA_SMTP_* settings.

    ``send`` only reports success when the SMTP server accepted the message;
    it never pretends that an e-mail was delivered.
    """

    def __init__(self, config):
        self.host = (getattr(config, "SMTP_HOST", None) or "").strip()
        self.port = int(getattr(config, "SMTP_PORT", 587) or 587)
        self.username = (getattr(config, "SMTP_USERNAME", None) or "").strip()
        password = getattr(config, "SMTP_PASSWORD", None) or ""
        # Google shows app passwords in groups ("abcd efgh ijkl mnop"); the
        # spaces are not part of the password.
        if "gmail" in self.host.lower():
            password = "".join(password.split())
        self.password = password
        self.use_tls = bool(getattr(config, "SMTP_USE_TLS", True))
        self.use_ssl = bool(getattr(config, "SMTP_USE_SSL", False)) or self.port == 465
        configured_from = (getattr(config, "SMTP_FROM", None) or "").strip()
        if not parseaddr(configured_from)[1] or configured_from.endswith("@localhost>"):
            configured_from = f"Nivora <{self.username}>" if self.username else ""
        self.sender = configured_from

    def missing_settings(self) -> list[str]:
        """Names of the environment variables that still need a value."""
        missing = []
        if not self.host:
            missing.append("NIVORA_SMTP_HOST")
        if not self.username:
            missing.append("NIVORA_SMTP_USERNAME")
        if not self.password:
            missing.append("NIVORA_SMTP_PASSWORD")
        if not self.sender:
            missing.append("NIVORA_SMTP_FROM")
        return missing

    def send(self, to: str, subject: str, text: str, html: str | None = None) -> EmailResult:
        missing = self.missing_settings()
        if missing:
            logger.error(
                "Correo no enviado: faltan variables de entorno %s", ", ".join(missing)
            )
            return EmailResult(False, "not_configured")

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.sender
        message["To"] = to
        message.set_content(text)
        if html:
            message.add_alternative(html, subtype="html")

        try:
            context = ssl.create_default_context()
            if self.use_ssl:
                smtp = smtplib.SMTP_SSL(self.host, self.port, timeout=15, context=context)
            else:
                smtp = smtplib.SMTP(self.host, self.port, timeout=15)
            with smtp:
                if not self.use_ssl and self.use_tls:
                    smtp.starttls(context=context)
                smtp.login(self.username, self.password)
                refused = smtp.send_message(message)
        except smtplib.SMTPAuthenticationError:
            logger.exception(
                "El servidor SMTP rechazó el usuario o la contraseña "
                "(en Gmail usa una contraseña de aplicación)"
            )
            return EmailResult(False, "auth_failed")
        except (OSError, smtplib.SMTPException):
            logger.exception("No se pudo enviar el correo a través de %s:%s", self.host, self.port)
            return EmailResult(False, "send_failed")

        if refused:
            logger.error("El servidor SMTP rechazó el destinatario: %s", refused)
            return EmailResult(False, "recipient_refused")
        return EmailResult(True)


def reset_code_email(name: str, code: str, ttl_seconds: int, change: bool) -> tuple[str, str, str]:
    """Build subject, plain text and HTML for a password reset code e-mail."""
    minutes = max(1, ttl_seconds // 60)
    greeting = f"Hola {name}," if name else "Hola,"
    action = "cambiar tu contraseña" if change else "recuperar tu cuenta"
    subject = f"{code} es tu código de Nivora"
    text = (
        f"{greeting}\n\n"
        f"Tu código para {action} en Nivora es:\n\n"
        f"    {code}\n\n"
        f"Escríbelo en Nivora junto con tu contraseña nueva. Es válido durante "
        f"{minutes} minutos y solo puede usarse una vez.\n\n"
        "Si no solicitaste este código, ignora este mensaje: tu contraseña actual "
        "seguirá funcionando. Nunca compartas este código con nadie.\n\n"
        "Equipo de Nivora"
    )
    html = (
        f"<p>{html_lib.escape(greeting)}</p>"
        f"<p>Tu código para {action} en Nivora es:</p>"
        '<p style="font-size:28px;font-weight:bold;letter-spacing:6px;'
        f'font-family:monospace">{code}</p>'
        f"<p>Escríbelo en Nivora junto con tu contraseña nueva. Es válido durante "
        f"{minutes} minutos y solo puede usarse una vez.</p>"
        "<p>Si no solicitaste este código, ignora este mensaje: tu contraseña actual "
        "seguirá funcionando. Nunca compartas este código con nadie.</p>"
        "<p>Equipo de Nivora</p>"
    )
    return subject, text, html
