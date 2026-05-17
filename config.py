import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"]       # z BotFather
ALLOWED_USER_ID  = int(os.environ["ALLOWED_USER_ID"]) # tvoje Telegram user ID

# ── Claude (Anthropic) ───────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]   # z console.anthropic.com

# ── OpenAI Whisper (hlasové zprávy) ─────────────────────────────────────────
OPENAI_API_KEY   = os.environ.get("OPENAI_API_KEY", "")  # volitelné, pro hlas

# ── Email (SMTP přes Endora) ─────────────────────────────────────────────────
SMTP_HOST        = os.environ.get("SMTP_HOST", "mail.endora.cz")
SMTP_PORT        = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER        = os.environ.get("SMTP_USER", "info@ai-masters.eu")
SMTP_PASS        = os.environ["SMTP_PASS"]             # heslo od Endory
EMAIL_FROM_NAME  = os.environ.get("EMAIL_FROM_NAME", "Lukas Kadlecek | AI Masters")

# ── Identita agenta ───────────────────────────────────────────────────────────
AGENT_NAME       = "Alex"
OWNER_NAME       = "Lukáš"
OWNER_BUSINESS   = "AI Masters (ai-masters.eu)"
OWNER_SEGMENT    = "estetické kliniky, laserová centra, zubní implantáty (CZ + SK)"
OWNER_GOAL       = "100 platících klientů do konce roku 2026"
