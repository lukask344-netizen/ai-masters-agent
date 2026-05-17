"""
AI Masters — hlavní Telegram bot
Lukášův osobní AI agent: text, hlas, emaily s schvalováním, paměť.

Spuštění:
    python main.py

Příkazy v Telegramu:
    /start      — přivítání
    /rano       — ranní briefing
    /reset      — smaž konverzační historii
    /zapamatuj  — ulož fakt (např. /zapamatuj kontakt Jana = jan@klinika.cz)
"""

import asyncio, logging, os, json, tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

import config, memory, brain, email_agent

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO
)
log = logging.getLogger(__name__)

# ── Bezpečnost: jen Lukáš může bota ovládat ─────────────────────────────────

def only_owner(func):
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if uid != config.ALLOWED_USER_ID:
            await update.message.reply_text("⛔ Nemáš přístup.")
            return
        return await func(update, ctx)
    return wrapper

# ── Utility ──────────────────────────────────────────────────────────────────

async def send(update: Update, text: str, parse_mode: str = "Markdown"):
    """Bezpečné odeslání zprávy (rozdělí pokud > 4096 znaků)."""
    for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
        await update.effective_message.reply_text(chunk, parse_mode=parse_mode)

def approval_keyboard(action_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ ANO, proveď", callback_data=f"approve:{action_id}"),
        InlineKeyboardButton("❌ NE, zruš",   callback_data=f"reject:{action_id}")
    ]])

# ── Příkazy ───────────────────────────────────────────────────────────────────

@only_owner
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await send(update,
        f"👋 Ahoj Lukáši, jsem *{config.AGENT_NAME}* — tvůj AI asistent pro AI Masters.\n\n"
        f"Napiš mi cokoliv, pošli hlasovou zprávu, nebo mi řekni co mám udělat.\n\n"
        f"Příkazy:\n"
        f"`/rano` — ranní briefing\n"
        f"`/reset` — nová konverzace\n"
        f"`/zapamatuj klíč = hodnota` — ulož si info"
    )

@only_owner
async def cmd_rano(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("☀️ Připravuji ranní briefing...")
    briefing = brain.morning_briefing()
    await send(update, f"☀️ *RANNÍ BRIEFING*\n\n{briefing}")

@only_owner
async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    memory.clear_history()
    await send(update, "🗑️ Konverzační historii jsem smazal. Začínáme znovu.")

@only_owner
async def cmd_zapamatuj(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace("/zapamatuj", "").strip()
    if "=" not in text:
        await send(update, "Použití: `/zapamatuj klíč = hodnota`\nNapř.: `/zapamatuj kontakt Jana = jana@klinika.cz`")
        return
    key, value = text.split("=", 1)
    memory.remember(key.strip(), value.strip())
    await send(update, f"✅ Zapamatoval jsem si: *{key.strip()}* = {value.strip()}")

# ── Textové zprávy ────────────────────────────────────────────────────────────

@only_owner
async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    await update.effective_message.reply_text("💭 Přemýšlím...")

    text, action = brain.think(user_msg)

    if action:
        action_id = memory.queue_action(action["action"], action)
        preview = _format_action_preview(action)
        await update.effective_message.reply_text(
            preview, parse_mode="Markdown",
            reply_markup=approval_keyboard(action_id)
        )
    else:
        if text:
            await send(update, text)

def _format_action_preview(action: dict) -> str:
    if action.get("action") == "send_email":
        return email_agent.compose_preview(
            action.get("to", "?"),
            action.get("subject", "?"),
            action.get("body", "?")
        )
    return f"🤖 Chci provést akci: `{action.get('action')}`\n```{json.dumps(action, ensure_ascii=False, indent=2)}```\nSouhlas?"

# ── Hlasové zprávy ────────────────────────────────────────────────────────────

@only_owner
async def handle_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    await update.effective_message.reply_text("🎙️ Transkribuji hlas...")

    # Stáhni OGG soubor
    file = await ctx.bot.get_file(voice.file_id)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        ogg_path = tmp.name

    try:
        transcript = await _transcribe(ogg_path)
    finally:
        os.unlink(ogg_path)

    if not transcript:
        await send(update, "❌ Nepodařilo se přepsat hlas. Zkus to znovu.")
        return

    await update.effective_message.reply_text(f'🎙️ *Rozuměl jsem:* "{transcript}"', parse_mode="Markdown")
    await handle_text_raw(update, ctx, transcript)

async def _transcribe(ogg_path: str) -> str | None:
    """Přepíše hlasovou zprávu přes OpenAI Whisper."""
    if not config.OPENAI_API_KEY:
        return "[Whisper není nastaven — napiš OPENAI_API_KEY do .env]"
    try:
        import openai
        client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        with open(ogg_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="cs"
            )
        return result.text
    except Exception as e:
        log.error(f"Whisper error: {e}")
        return None

async def handle_text_raw(update: Update, ctx: ContextTypes.DEFAULT_TYPE, text: str):
    """Zpracuj text (z přepisu hlasu nebo textu) — sdílená logika."""
    reply_text, action = brain.think(text)
    if action:
        action_id = memory.queue_action(action["action"], action)
        preview = _format_action_preview(action)
        await update.effective_message.reply_text(
            preview, parse_mode="Markdown",
            reply_markup=approval_keyboard(action_id)
        )
    else:
        if reply_text:
            await send(update, reply_text)

# ── Schvalovací tlačítka ──────────────────────────────────────────────────────

async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != config.ALLOWED_USER_ID:
        return

    data = query.data  # "approve:42" nebo "reject:42"
    decision, action_id_str = data.split(":", 1)
    action_id = int(action_id_str)

    action_data = memory.pop_action(action_id)
    if not action_data:
        await query.edit_message_text("⚠️ Tato akce již neexistuje nebo vypršela.")
        return

    if decision == "reject":
        await query.edit_message_text("❌ Akce zrušena.")
        memory.save_message("user", "[SYSTEM] Uživatel zamítl akci: " + action_data["action"])
        return

    # Proveď akci
    action = action_data["payload"]
    result = await _execute_action(action)
    await query.edit_message_text(result, parse_mode="Markdown")
    memory.save_message("assistant", f"[SYSTEM] Akce {action['action']} provedena: {result}")

async def _execute_action(action: dict) -> str:
    name = action.get("action")

    if name == "send_email":
        ok = email_agent.send_email(
            to      = action["to"],
            subject = action["subject"],
            body    = action["body"]
        )
        if ok:
            return f"✅ Email odeslán na *{action['to']}*"
        else:
            return "❌ Email se nepodařilo odeslat. Zkontroluj SMTP nastavení."

    if name == "remind_me":
        memory.remember(f"připomenutí_{action.get('when','')}", action.get("text", ""))
        return f"✅ Připomenutí uloženo: {action.get('text')}"

    return f"⚠️ Neznámá akce: {name}"

# ── Spuštění ──────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(config.TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("rano",       cmd_rano))
    app.add_handler(CommandHandler("reset",      cmd_reset))
    app.add_handler(CommandHandler("zapamatuj",  cmd_zapamatuj))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(CallbackQueryHandler(handle_callback))

    log.info(f"Agent {config.AGENT_NAME} spuštěn. Čekám na zprávy...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
