from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request, Response
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from app.config import settings


telegram_app = (
    Application.builder()
    .token(settings.bot_token)
    .updater(None)
    .build()
)


def is_admin(update: Update) -> bool:
    user = update.effective_user

    if user is None:
        return False

    return user.id in settings.admin_ids


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not is_admin(update):
        await update.message.reply_text(
            "عذرًا، هذا البوت خاص بالمشرفين."
        )
        return

    await update.message.reply_text(
        "مرحبًا بك في وكيل المحتوى الذكي.

"
        "استخدم /help لعرض الأوامر."
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not is_admin(update):
        await update.message.reply_text(
            "عذرًا، هذا البوت خاص بالمشرفين."
        )
        return

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
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "environment": settings.environment
    }


@app.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None)
):
    if (
        x_telegram_bot_api_secret_token
        != settings.telegram_webhook_secret
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid webhook secret"
        )

    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)

    await telegram_app.process_update(update)

    return Response(status_code=200)
