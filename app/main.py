from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.config import settings


TITLE, CONTENT = range(2)


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


async def myid_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return

    user = update.effective_user

    if user is None:
        await update.message.reply_text(
            "User ID is unavailable."
        )
        return

    await update.message.reply_text(
        "Your Telegram User ID is: "
        + str(user.id)
    )


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return

    if not is_admin(update):
        await update.message.reply_text(
            "Access denied. Send /myid to get your ID."
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
            "Access denied. Send /myid to get your ID."
        )
        return

    await update.message.reply_text(
        "Commands: /start, /help, and /myid"
    )


async def draft_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return ConversationHandler.END

    if not is_admin(update):
        await update.message.reply_text(
            "Access denied."
        )
        return ConversationHandler.END

    context.user_data.pop(
        "draft_title",
        None
    )

    context.user_data.pop(
        "draft_content",
        None
    )

    await update.message.reply_text(
        "Please send the draft title."
    )

    return TITLE


async def receive_title(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return ConversationHandler.END

    title = update.message.text.strip()

    if not title:
        await update.message.reply_text(
            "The title cannot be empty. Please send it again."
        )
        return TITLE

    context.user_data["draft_title"] = title

    await update.message.reply_text(
        "Now send the draft content."
    )

    return CONTENT


async def receive_content(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return ConversationHandler.END

    content = update.message.text.strip()

    if not content:
        await update.message.reply_text(
            "The content cannot be empty. Please send it again."
        )
        return CONTENT

    context.user_data["draft_content"] = content

    title = context.user_data.get(
        "draft_title",
        ""
    )

    preview_text = (
        "Draft preview

"
        "Title: "
        + title
        + "

"
        + "Content:
"
        + content
    )

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

    await update.message.reply_text(
        preview_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ConversationHandler.END


async def cancel_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return ConversationHandler.END

    context.user_data.pop(
        "draft_title",
        None
    )

    context.user_data.pop(
        "draft_content",
        None
    )

    await update.message.reply_text(
        "Draft creation cancelled."
    )

    return ConversationHandler.END


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
            "Commands: /start, /help, /myid, and /cancel"
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
            "Approval completed. Choose a channel:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if query.data == "reject_draft":
        context.user_data.pop(
            "draft_title",
            None
        )

        context.user_data.pop(
            "draft_content",
            None
        )

        await query.edit_message_text(
            "Draft rejected."
        )
        return

    if query.data.startswith("channel_"):
        channel_name = query.data.replace(
            "channel_",
            ""
        )

        context.user_data["selected_channel"] = channel_name

        keyboard = [
            [
                InlineKeyboardButton(
                    "Confirm",
                    callback_data="final_confirm"
                )
            ],
            [
                InlineKeyboardButton(
                    "Cancel",
                    callback_data="cancel_publish"
                )
            ],
        ]

        message_text = (
            "Selected channel: "
            + channel_name
            + ". Confirm before publishing:"
        )

        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if query.data == "final_confirm":
        selected_channel = context.user_data.get(
            "selected_channel"
        )

        if selected_channel != "telegram":
            await query.edit_message_text(
                "Only Telegram publishing is enabled currently."
            )
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    "Publish now",
                    callback_data="publish_now"
                )
            ],
            [
                InlineKeyboardButton(
                    "Cancel",
                    callback_data="cancel_publish"
                )
            ],
        ]

        await query.edit_message_text(
            "Final confirmation completed. "
            "Publishing to Telegram is ready.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if query.data == "publish_now":
        title = context.user_data.get(
            "draft_title",
            "Untitled draft"
        )

        content = context.user_data.get(
            "draft_content",
            ""
        )

        draft_text = (
            title
            + "

"
            + content
        )

        try:
            sent_message = await context.bot.send_message(
                chat_id=settings.telegram_channel_id,
                text=draft_text
            )

            context.user_data.pop(
                "draft_title",
                None
            )

            context.user_data.pop(
                "draft_content",
                None
            )

            success_text = (
                "Published successfully to Telegram. "
                "Message ID: "
                + str(sent_message.message_id)
            )

            await query.edit_message_text(
                success_text
            )

        except TelegramError as error:
            error_text = (
                "Telegram publishing failed: "
                + str(error)
            )

            await query.edit_message_text(
                error_text
            )

        return

    if query.data == "cancel_publish":
        context.user_data.pop(
            "selected_channel",
            None
        )

        await query.edit_message_text(
            "Operation cancelled."
        )
        return

    await query.edit_message_text(
        "Unknown action."
    )


draft_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            draft_start,
            pattern="^create_draft$"
        )
    ],
    states={
        TITLE: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_title
            )
        ],
        CONTENT: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_content
            )
        ],
    },
    fallbacks=[
        CommandHandler(
            "cancel",
            cancel_command
        )
    ],
)


telegram_app.add_handler(
    CommandHandler(
        "myid",
        myid_command
    )
)

telegram_app.add_handler(
    CommandHandler(
        "start",
        start_command
    )
)

telegram_app.add_handler(
    CommandHandler(
        "help",
        help_command
    )
)

telegram_app.add_handler(
    draft_conversation
)

telegram_app.add_handler(
    CallbackQueryHandler(
        button_handler
    )
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
    version="0.4.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {
        "name": "MENA Content Agent",
        "status": "running",
        "version": "0.4.0"
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
