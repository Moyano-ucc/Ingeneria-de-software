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

    def is_configured(self) -> bool:
        return not self.missing_settings()

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


def password_email(name: str, link: str, ttl_seconds: int, change: bool) -> tuple[str, str, str]:
    """Build subject, plain text and HTML for a password link e-mail."""
    minutes = max(1, ttl_seconds // 60)
    validity = (
        f"{minutes // 60} hora{'s' if minutes // 60 != 1 else ''}"
        if minutes % 60 == 0
        else f"{minutes} minutos"
    )
    greeting = f"Hola {name}," if name else "Hola,"
    if change:
        subject = "Cambia tu contraseña de Nivora"
        intro = "Recibimos una solicitud para cambiar la contraseña de tu cuenta de Nivora."
    else:
        subject = "Recupera tu contraseña de Nivora"
        intro = "Recibimos una solicitud para recuperar el acceso a tu cuenta de Nivora."
    text = (
        f"{greeting}\n\n{intro}\n\n"
        f"Abre este enlace para crear una contraseña nueva (válido durante {validity}):\n\n"
        f"{link}\n\n"
        "El enlace solo puede usarse una vez. Si no solicitaste este cambio, "
        "ignora este mensaje: tu contraseña actual seguirá funcionando.\n\n"
        "Equipo de Nivora"
    )
    html = (
        f"<p>{html_lib.escape(greeting)}</p><p>{intro}</p>"
        f'<p><a href="{html_lib.escape(link, quote=True)}">Crear una contraseña nueva</a></p>'
        f"<p>El enlace es válido durante {validity} y solo puede usarse una vez.</p>"
        "<p>Si no solicitaste este cambio, ignora este mensaje: tu contraseña actual "
        "seguirá funcionando.</p><p>Equipo de Nivora</p>"
    )
    return subject, text, html
