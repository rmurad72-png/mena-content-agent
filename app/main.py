from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request, Response
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)


telegram_app = (
    Application.builder()
    .token("PLACEHOLDER")
    .updater(None)
    .build()
)


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "مرحبًا بك في وكيل المحتوى الذكي.

"
        "تم تشغيل البوت بنجاح."
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "الأوامر المتاحة:

"
        "/start - بدء استخدام البوت
"
        "/help - عرض المساعدة"
    )


telegram_app.add_handler(
    CommandHandler("start", start_command)
)

telegram_app.add_handler(
    CommandHandler("help", help_command)
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_app.initialize()
    await telegram_app.start()
    yield
    await telegram_app.stop()
    await telegram_app.shutdown()


app = FastAPI(
    title="MENA Content Agent",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "name": "MENA Content Agent",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "environment": "production"
    }


@app.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None)
):
    expected_secret = "PLACEHOLDER"

    if x_telegram_bot_api_secret_token != expected_secret:
        raise HTTPException(
            status_code=403,
            detail="Invalid webhook secret"
        )

    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)

    return Response(status_code=200)
