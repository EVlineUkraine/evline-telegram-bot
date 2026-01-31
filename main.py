import os
import json
import datetime
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# =========================
# ENV
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Requests")

# Мы переходим на Secret File в Render (самый надежный способ)
# Render secret files доступны по /etc/secrets/<filename>
GOOGLE_CREDS_FILE = os.getenv("GOOGLE_CREDS_FILE", "/etc/secrets/google_creds.json")

# Оставим запасной вариант (если вдруг захочешь хранить в env),
# но он НЕ обязателен и может быть удалён.
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

if not BOT_TOKEN:
    raise RuntimeError("Missing env BOT_TOKEN")
if not SPREADSHEET_ID:
    raise RuntimeError("Missing env SPREADSHEET_ID")

# =========================
# Google auth
# =========================
scopes = ["https://www.googleapis.com/auth/spreadsheets"]

def build_credentials() -> Credentials:
    """
    1) Основной путь: secret file /etc/secrets/google_creds.json
    2) Запасной путь: переменная GOOGLE_CREDS_JSON (если файл не найден)
    """
    # 1) Secret File
    if GOOGLE_CREDS_FILE and os.path.exists(GOOGLE_CREDS_FILE):
        return Credentials.from_service_account_file(GOOGLE_CREDS_FILE, scopes=scopes)

    # 2) Fallback: env JSON
    if GOOGLE_CREDS_JSON:
        try:
            creds_dict = json.loads(GOOGLE_CREDS_JSON)
            return Credentials.from_service_account_info(creds_dict, scopes=scopes)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid GOOGLE_CREDS_JSON (JSON decode error): {e}") from e

    raise RuntimeError("Missing Google credentials: provide GOOGLE_CREDS_FILE (secret file) or GOOGLE_CREDS_JSON")

credentials = build_credentials()
gc = gspread.authorize(credentials)

# Важно: worksheet открываем один раз при старте
sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)


# =========================
# Bot handlers
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вітаю 👋\n"
        "Напишіть, будь ласка:\n"
        "• марку та модель авто\n"
        "• яку запчастину шукаєте\n"
        "• VIN-код (якщо є)\n\n"
        "Менеджер скоро підключиться."
    )

async def brands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Працюємо з брендами:\n"
        "BYD, Xiaomi, Lynk & Co, Fangchengbao (Leopard), ZEEKR, NIO, XPENG, Li Auto, AITO, AVATR, Denza."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text or ""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Пытаемся записать в таблицу, но если Google временно недоступен —
    # бот НЕ должен падать.
    try:
        sheet.append_row(
            [
                timestamp,
                str(user.id),
                user.username or "",
                user.full_name or "",
                text,
                "New",
            ],
            value_input_option="RAW",
        )
        await update.message.reply_text("Дякуємо 🙌\nЗапит прийнято в роботу, вже шукаємо.")
    except Exception:
        # Не показываем пользователю тех.ошибки — просто подтверждаем прием
        await update.message.reply_text(
            "Дякуємо 🙌\nЗапит прийнято. Якщо відповідь не прийде швидко — продублюйте повідомлення ще раз."
        )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("brands", brands))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
