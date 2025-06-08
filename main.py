from fastapi.middleware.cors import CORSMiddleware
from models.index import ChatMessage
from providers.ollama import query_rag, reset_context
from fastapi import FastAPI, Request, HTTPException
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import os
from contextlib import asynccontextmanager
import asyncio

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_PATH = "/telegram_webhook"
APP_URL = os.environ.get("APP_URL")
Application = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global Application
    Application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    await Application.initialize()
    Application.add_handler(CommandHandler("start", start))
    Application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    Application.add_handler(CommandHandler("reset", reset))
    bot = Bot(TELEGRAM_BOT_TOKEN)
    await Application.bot.set_webhook(url=f"{APP_URL}{WEBHOOK_PATH}")
    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Приветствую! Я консультант для абитуриентов Алтайского Государственного Университета.\n Пожалуйста, задайте ваш вопрос, и я постараюсь предоставить вам наилучший ответ, основываясь на имеющейся информации. 😉",
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    try:
        response_text = await reset_context(chat_id)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response_text)
    except Exception as e:
        print(f"Error during reset_context processing: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла ошибка при обработке вашего запроса.",
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    question_text = update.message.text
    if question_text:
        message = ChatMessage(question=question_text)
        try:
            processing_message = await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="Обрабатываю ваш вопрос, это может занять некоторое время..."
            )
            processing_message_id = processing_message.message_id
            response_text = await query_rag(message, chat_id)
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_message_id)
            except Exception as e:
                 print(f"Error deleting message: {e}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text=response_text)
        except Exception as e:
            print(f"Error during query_rag processing: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Произошла ошибка при обработке вашего запроса.",
            )
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Я не понял ваш вопрос.")

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        if Application is None:
            raise ValueError("Application not initialized.  Check startup event.")
        update = Update.de_json(data, Application.bot)
        asyncio.create_task(Application.process_update(update))
        return {"ok": True}
    except Exception as e:
        print(f"Error processing Telegram webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/")
async def read_root():
    return {"Hello": "I'm your telegram bot's backend!"}


