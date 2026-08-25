import logging
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


TITLE, CONTENT, LINK, PHOTO, REVIEW, CHANNEL, CONFIRM = range(7)
NEW_LINE = chr(10)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


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


def clear_draft(
    context: ContextTypes.DEFAULT_TYPE
):
    keys = [
        "draft_title",
        "draft_content",
        "draft_link",
        "draft_photo_file_id",
        "draft_photo_url",
        "selected_channel",
    ]

    for key in keys:
        context.user_data.pop(
            key,
            None
        )


def build_post_text(
    title: str,
    content: str,
    link: str | None
) -> str:
    text = (
        title
        + NEW_LINE
        + NEW_LINE
        + content
    )

    if link:
        text = (
            text
            + NEW_LINE
            + NEW_LINE
            + "رابط الموضوع:"
            + NEW_LINE
            + link
        )

    return text


def start_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "إنشاء مسودة",
                callback_data="create_draft"
            )
        ],
        [
            InlineKeyboardButton(
                "مساعدة",
                callback_data="show_help"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def review_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "اعتماد المسودة",
                callback_data="approve_first"
            )
        ],
        [
            InlineKeyboardButton(
                "رفض المسودة",
                callback_data="reject_draft"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def channel_keyboard() -> InlineKeyboardMarkup:
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

    return InlineKeyboardMarkup(keyboard)


def confirm_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "تأكيد",
                callback_data="final_confirm"
            )
        ],
        [
            InlineKeyboardButton(
                "إلغاء",
                callback_data="cancel_publish"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def publish_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "نشر الآن",
                callback_data="publish_now"
            )
        ],
        [
            InlineKeyboardButton(
                "إلغاء",
                callback_data="cancel_publish"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def edit_callback_message(
    query,
    text: str,
    reply_markup=None
):
    message = query.message

    if message is not None and message.photo:
        return await query.edit_message_caption(
            caption=text,
            reply_markup=reply_markup
        )

    return await query.edit_message_text(
        text=text,
        reply_markup=reply_markup
    )


async def myid_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return

    user = update.effective_user

    if user is None:
        await update.message.reply_text(
            "تعذر الحصول على رقم المستخدم."
        )
        return

    await update.message.reply_text(
        "رقم Telegram الخاص بك هو: "
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
            "غير مسموح. استخدم /myid لمعرفة رقم حسابك."
        )
        return

    await update.message.reply_text(
        "مرحبًا بك. اختر إجراءً:",
        reply_markup=start_keyboard()
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return

    await update.message.reply_text(
        "الأوامر المتاحة:"
        + NEW_LINE
        + "/start - القائمة الرئيسية"
        + NEW_LINE
        + "/myid - عرض رقم الحساب"
        + NEW_LINE
        + "/help - المساعدة"
        + NEW_LINE
        + "/cancel - إلغاء العملية"
    )


async def draft_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if query is None:
        return ConversationHandler.END

    await query.answer()

    if not is_admin(update):
        await edit_callback_message(
            query,
            "غير مسموح."
        )
        return ConversationHandler.END

    clear_draft(context)

    await edit_callback_message(
        query,
        "أرسل عنوان المسودة."
    )

    return TITLE


async def receive_title(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return TITLE

    if update.message.text is None:
        await update.message.reply_text(
            "أرسل نصًا فقط."
        )
        return TITLE

    title = update.message.text.strip()

    if not title:
        await update.message.reply_text(
            "العنوان لا يمكن أن يكون فارغًا."
        )
        return TITLE

    context.user_data["draft_title"] = title

    await update.message.reply_text(
        "أرسل محتوى المسودة."
    )

    return CONTENT


async def receive_content(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return CONTENT

    if update.message.text is None:
        await update.message.reply_text(
            "أرسل نصًا فقط."
        )
        return CONTENT

    content = update.message.text.strip()

    if not content:
        await update.message.reply_text(
            "المحتوى لا يمكن أن يكون فارغًا."
        )
        return CONTENT

    context.user_data["draft_content"] = content

    await update.message.reply_text(
        "أرسل رابط الموضوع أو المقالة، أو اكتب /skip."
    )

    return LINK


async def receive_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return LINK

    if update.message.text is None:
        await update.message.reply_text(
            "أرسل رابطًا يبدأ بـ http أو https، أو اكتب /skip."
        )
        return LINK

    link = update.message.text.strip()

    if link == "/skip":
        context.user_data.pop(
            "draft_link",
            None
        )

    elif link.startswith(
        ("http://", "https://")
    ):
        context.user_data["draft_link"] = link

    else:
        await update.message.reply_text(
            "الرابط يجب أن يبدأ بـ http:// أو https://، "
            "أو اكتب /skip."
        )
        return LINK

    await update.message.reply_text(
        "أرسل صورة، أو رابط صورة، أو اكتب /skip."
    )

    return PHOTO


async def receive_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return PHOTO

    if update.message.photo:
        largest_photo = update.message.photo[-1]

        context.user_data["draft_photo_file_id"] = (
            largest_photo.file_id
        )

        context.user_data.pop(
            "draft_photo_url",
            None
        )

    elif update.message.text:
        value = update.message.text.strip()

        if value == "/skip":
            context.user_data.pop(
                "draft_photo_file_id",
                None
            )

            context.user_data.pop(
                "draft_photo_url",
                None
            )

        elif value.startswith(
            ("http://", "https://")
        ):
            context.user_data["draft_photo_url"] = value

            context.user_data.pop(
                "draft_photo_file_id",
                None
            )

        else:
            await update.message.reply_text(
                "أرسل صورة أو رابط صورة صحيح أو اكتب /skip."
            )
            return PHOTO

    else:
        await update.message.reply_text(
            "أرسل صورة أو رابط صورة أو اكتب /skip."
        )
        return PHOTO

    await send_preview(
        update,
        context
    )

    return REVIEW


async def send_preview(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    title = context.user_data.get(
        "draft_title",
        ""
    )

    content = context.user_data.get(
        "draft_content",
        ""
    )

    link = context.user_data.get(
        "draft_link"
    )

    photo_file_id = context.user_data.get(
        "draft_photo_file_id"
    )

    photo_url = context.user_data.get(
        "draft_photo_url"
    )

    post_text = build_post_text(
        title,
        content,
        link
    )

    has_photo = bool(
        photo_file_id
        or photo_url
    )

    preview_text = (
        "معاينة المسودة:"
        + NEW_LINE
        + NEW_LINE
        + post_text
        + NEW_LINE
        + NEW_LINE
        + "الصورة: "
        + ("موجودة" if has_photo else "غير موجودة")
    )

    keyboard = review_keyboard()

    if update.message is None:
        return

    if photo_file_id:
        await update.message.reply_photo(
            photo=photo_file_id,
            caption=preview_text,
            reply_markup=keyboard
        )
        return

    if photo_url:
        try:
            await update.message.reply_photo(
                photo=photo_url,
                caption=preview_text,
                reply_markup=keyboard
            )
            return

        except TelegramError:
            logger.exception(
                "Could not load image URL"
            )

    await update.message.reply_text(
        preview_text,
        reply_markup=keyboard
    )


async def approve_draft(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if query is None:
        return CHANNEL

    await query.answer()

    if not is_admin(update):
        await edit_callback_message(
            query,
            "غير مسموح."
        )
        return ConversationHandler.END

    await edit_callback_message(
        query,
        "تم اعتماد المسودة. اختر قناة النشر:",
        reply_markup=channel_keyboard()
    )

    return CHANNEL


async def reject_draft(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if query is None:
        return ConversationHandler.END

    await query.answer()

    clear_draft(context)

    await edit_callback_message(
        query,
        "تم رفض المسودة."
    )

    return ConversationHandler.END


async def choose_channel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if query is None:
        return CHANNEL

    await query.answer()

    channel_name = query.data.replace(
        "channel_",
        ""
    )

    context.user_data["selected_channel"] = (
        channel_name
    )

    await edit_callback_message(
        query,
        "القناة المختارة: "
        + channel_name
        + ". هل تريد المتابعة؟",
        reply_markup=confirm_keyboard()
    )

    return CONFIRM


async def final_confirm(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if query is None:
        return CONFIRM

    await query.answer()

    selected_channel = context.user_data.get(
        "selected_channel"
    )

    if selected_channel != "telegram":
        await edit_callback_message(
            query,
            "النشر مفعّل حاليًا لقناة Telegram فقط."
        )
        return CONFIRM

    await edit_callback_message(
        query,
        "تم التأكيد النهائي. اضغط نشر الآن:",
        reply_markup=publish_keyboard()
    )

    return CONFIRM


async def publish_now(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if query is None:
        return CONFIRM

    await query.answer()

    title = context.user_data.get(
        "draft_title",
        "منشور بلا عنوان"
    )

    content = context.user_data.get(
        "draft_content",
        ""
    )

    link = context.user_data.get(
        "draft_link"
    )

    photo_file_id = context.user_data.get(
        "draft_photo_file_id"
    )

    photo_url = context.user_data.get(
        "draft_photo_url"
    )

    post_text = build_post_text(
        title,
        content,
        link
    )

    try:
        if photo_file_id:
            sent_message = await context.bot.send_photo(
                chat_id=settings.telegram_channel_id,
                photo=photo_file_id,
                caption=post_text
            )

        elif photo_url:
            sent_message = await context.bot.send_photo(
                chat_id=settings.telegram_channel_id,
                photo=photo_url,
                caption=post_text
            )

        else:
            sent_message = await context.bot.send_message(
                chat_id=settings.telegram_channel_id,
                text=post_text
            )

        message_id = sent_message.message_id

        clear_draft(context)

        await edit_callback_message(
            query,
            "تم النشر بنجاح على Telegram."
            + NEW_LINE
            + "رقم المنشور: "
            + str(message_id)
        )

        return ConversationHandler.END

    except TelegramError as error:
        logger.exception(
            "Publishing failed"
        )

        await edit_callback_message(
            query,
            "فشل النشر على Telegram:"
            + NEW_LINE
            + str(error)
        )

        return CONFIRM


async def cancel_publish(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if query is not None:
        await query.answer()

        await edit_callback_message(
            query,
            "تم إلغاء العملية."
        )

    clear_draft(context)

    return ConversationHandler.END


async def cancel_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    clear_draft(context)

    if update.message is not None:
        await update.message.reply_text(
            "تم إلغاء العملية."
        )

    return ConversationHandler.END


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):
    logger.error(
        "Exception while handling an update:",
        exc_info=context.error
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
        LINK: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_link
            )
        ],
        PHOTO: [
            MessageHandler(
                filters.PHOTO,
                receive_photo
            ),
            MessageHandler(
                filters.TEXT,
                receive_photo
            ),
        ],
        REVIEW: [
            CallbackQueryHandler(
                approve_draft,
                pattern="^approve_first$"
            ),
            CallbackQueryHandler(
                reject_draft,
                pattern="^reject_draft$"
            ),
        ],
        CHANNEL: [
            CallbackQueryHandler(
                choose_channel,
                pattern="^channel_(telegram|x|reddit)$"
            ),
        ],
        CONFIRM: [
            CallbackQueryHandler(
                final_confirm,
                pattern="^final_confirm$"
            ),
            CallbackQueryHandler(
                publish_now,
                pattern="^publish_now$"
            ),
            CallbackQueryHandler(
                cancel_publish,
                pattern="^cancel_publish$"
            ),
        ],
    },
    fallbacks=[
        CommandHandler(
            "cancel",
            cancel_command
        )
    ],
    allow_reentry=True
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

telegram_app.add_error_handler(
    error_handler
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
    version="0.5.3",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {
        "name": "MENA Content Agent",
        "status": "running",
        "version": "0.5.3"
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

    return Response(
        status_code=200
    )
