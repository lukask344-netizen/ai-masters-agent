"""
Email Autopilot — odesílá emaily jako info@ai-masters.eu přes SMTP (Endora).
Každý email musí být nejprve schválen uživatelem přes Telegram tlačítko.
"""
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config

def send_email(to: str, subject: str, body: str) -> bool:
    """
    Odešle email. Vrátí True při úspěchu, False při chybě.
    POZOR: Volat až po schválení uživatelem!
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{config.EMAIL_FROM_NAME} <{config.SMTP_USER}>"
    msg["To"]      = to

    # Plain text i HTML verze
    text_part = MIMEText(body, "plain", "utf-8")
    msg.attach(text_part)

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, context=ctx) as server:
            server.login(config.SMTP_USER, config.SMTP_PASS)
            server.sendmail(config.SMTP_USER, [to], msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False

def compose_preview(to: str, subject: str, body: str) -> str:
    """Vrátí lidsky čitelný náhled emailu pro schvalovací zprávu v Telegramu."""
    preview = body[:400] + ("..." if len(body) > 400 else "")
    return (
        f"📧 *Chystám email k odeslání:*\n\n"
        f"*Komu:* `{to}`\n"
        f"*Předmět:* {subject}\n\n"
        f"*Text:*\n{preview}\n\n"
        f"Mám ho odeslat?"
    )
