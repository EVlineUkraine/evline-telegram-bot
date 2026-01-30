import os
import json
import datetime
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Requests")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

if not BOT_TOKEN:
    raise RuntimeError("Missing env BOT_TOKEN")
if not SPREADSHEET_ID:
    raise RuntimeError("Missing env SPREADSHEET_ID")
if not GOOGLE_CREDS_JSON:
    raise RuntimeError("Missing env GOOGLE_CREDS_JSON")

creds_dict = json.loads(GOOGLE_CREDS_JSON)
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

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

    sheet.append_row([
        timestamp,
        str(user.id),
        user.username or "",
        user.full_name or "",
        text,
        "New"
    ])

    await update.message.reply_text("Дякуємо 🙌\nЗапит прийнято в роботу, вже шукаємо.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("brands", brands))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()