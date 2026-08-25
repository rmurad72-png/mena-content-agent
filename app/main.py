from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
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
    if update.message is None:
        return

    if not is_admin(update):
        await update.message.reply_text(
            "Access denied."
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "Create draft",
                callback_data="create_draft"
            )
        ],
        [
            InlineKeyboardButton(
                "Help",
                callback_data="show_help"
            )
        ],
    ]

    await update.message.reply_text(
        "Welcome to the content agent. Choose an action:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return

    if not is_admin(update):
        await update.message.reply_text(
            "Access denied."
        )
        return

    await update.message.reply_text(
        "Commands: /start and /help"
    )


async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if query is None:
        return

    await query.answer()

    if not is_admin(update):
        await query.edit_message_text(
            "Access denied."
        )
        return

    if query.data == "show_help":
        await query.edit_message_text(
            "Commands: /start and /help"
        )
        return

    if query.data == "create_draft":
        keyboard = [
            [
                InlineKeyboardButton(
                    "Approve",
                    callback_data="approve_first"
                )
            ],
            [
                InlineKeyboardButton(
                    "Reject",
                    callback_data="reject_draft"
                )
            ],
        ]

        await query.edit_message_text(
            "Test draft. Choose an action:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if query.data == "approve_first":
        keyboard = [
            [
                InlineKeyboardButton(
                    "Telegram",
                    callback_data="channel_telegram"
                )
            ],
            [
                InlineKeyboardButton(
                    "X",
                    callback_data="channel_x"
                )
            ],
            [
                InlineKeyboardButton(
                    "Reddit",
                    callback_data="channel_reddit"
                )
            ],
        ]

        await query.edit_message_text(
            "First approval completed. Choose a channel:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if query.data == "reject_draft":
        await query.edit_message_text(
            "Draft rejected."
        )
        return

    if query.data.startswith("channel_"):
        channel_name = query.data.replace(
            "channel_",
            ""
        )

        await query.edit_message_text(
            "Selected channel: "
            + channel_name
            + ". Next step: final confirmation."
        )
        return

    await query.edit_message_text(
        "Unknown action."
    )


telegram_app.add_handler(
    CommandHandler("start", start_command)
)

telegram_app.add_handler(
    CommandHandler("help", help_command)
)

telegram_app.add_handler(
    CallbackQueryHandler(button_handler)
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
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "name": "MENA Content Agent",
        "status": "running",
        "version": "0.2.0"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "environment": settings.environment
    }


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    update = Update.de_json(
        data,
        telegram_app.bot
    )

    await telegram_app.process_update(update)

    return Response(status_code=200)
