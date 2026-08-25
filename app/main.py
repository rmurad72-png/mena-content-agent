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


TITLE, CONTENT, LINK, PHOTO = range(4)
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
    context.user_data.pop("draft_title", None)
    context.user_data.pop("draft_content", None)
    context.user_data.pop("draft_link", None)
    context.user_data.pop("draft_photo_file_id", None)
    context.user_data.pop("draft_photo_url", None)
    context.user_data.pop("selected_channel", None)


def build_post_text(
    title: str,
    content: str,
    link: str | None
) -> str:
    post_text = (
        title
        + NEW_LINE
        + NEW_LINE
        + content
    )

    if link:
        post_text = (
            post_text
            + NEW_LINE
            + NEW_LINE
            + "رابط الموضوع:"
            + NEW_LINE
            + link
        )

    return post_text


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


def confirmation_keyboard() -> InlineKeyboardMarkup:
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
        + "/cancel - إلغاء العملية الحالية"
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
        await query.edit_message_text(
            "غير مسموح."
        )
        return ConversationHandler.END

    clear_draft(context)

    await query.edit_message_text(
        "أرسل عنوان المسودة."
    )

    return TITLE


async def receive_title(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return ConversationHandler.END

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
        return ConversationHandler.END

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
        return ConversationHandler.END

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

        await update.message.reply_text(
            "أرسل صورة، أو رابط صورة، أو اكتب /skip."
        )

        return PHOTO

    if not (
        link.startswith("http://")
        or link.startswith("https://")
    ):
        await update.message.reply_text(
            "الرابط غير صحيح. يجب أن يبدأ بـ http أو https."
        )
        return LINK

    context.user_data["draft_link"] = link

    await update.message.reply_text(
        "أرسل صورة، أو رابط صورة، أو اكتب /skip."
    )

    return PHOTO


async def receive_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return ConversationHandler.END

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
        photo_value = update.message.text.strip()

        if photo_value == "/skip":
            context.user_data.pop(
                "draft_photo_file_id",
                None
            )

            context.user_data.pop(
                "draft_photo_url",
                None
            )

        elif (
            photo_value.startswith("http://")
            or photo_value.startswith("https://")
        ):
            context.user_data["draft_photo_url"] = (
                photo_value
            )

            context.user_data.pop(
                "draft_photo_file_id",
                None
            )

        else:
            await update.message.reply_text(
                "أرسل صورة، أو رابط صورة صحيح، أو اكتب /skip."
            )
            return PHOTO

    else:
        await update.message.reply_text(
            "أرسل صورة، أو رابط صورة، أو اكتب /skip."
        )
        return PHOTO

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

    post_text = build_post_text(
        title,
        content,
        link
    )

    has_photo = bool(
        context.user_data.get(
            "draft_photo_file_id"
        )
        or context.user_data.get(
            "draft_photo_url"
        )
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

    photo_file_id = context.user_data.get(
        "draft_photo_file_id"
    )

    photo_url = context.user_data.get(
        "draft_photo_url"
    )

    if photo_file_id:
        await update.message.reply_photo(
            photo=photo_file_id,
            caption=preview_text,
            reply_markup=review_keyboard()
        )

    elif photo_url:
        try:
            await update.message.reply_photo(
                photo=photo_url,
                caption=preview_text,
                reply_markup=review_keyboard()
            )
        except TelegramError:
            await update.message.reply_text(
                "تعذر تحميل رابط الصورة.",
                reply_markup=review_keyboard()
            )

    else:
        await update.message.reply_text(
            preview_text,
            reply_markup=review_keyboard()
        )

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
            "غير مسموح."
        )
        return

    callback_data = query.data

    if callback_data == "show_help":
        await query.edit_message_text(
            "استخدم /start لفتح القائمة الرئيسية."
        )
        return

    if callback_data == "approve_first":
        await query.edit_message_text(
            "تم اعتماد المسودة. اختر قناة النشر:",
            reply_markup=channel_keyboard()
        )
        return

    if callback_data == "reject_draft":
        clear_draft(context)

        await query.edit_message_text(
            "تم رفض المسودة."
        )
        return

    if callback_data.startswith("channel_"):
        channel_name = callback_data.replace(
            "channel_",
            ""
        )

        context.user_data["selected_channel"] = (
            channel_name
        )

        await query.edit_message_text(
            "القناة المختارة: "
            + channel_name
            + ". هل تريد المتابعة؟",
            reply_markup=confirmation_keyboard()
        )
        return

    if callback_data == "final_confirm":
        selected_channel = context.user_data.get(
            "selected_channel"
        )

        if selected_channel != "telegram":
            await query.edit_message_text(
                "النشر مفعّل حاليًا لقناة Telegram فقط."
            )
            return

        await query.edit_message_text(
            "تم التأكيد النهائي. اضغط نشر الآن:",
            reply_markup=publish_keyboard()
        )
        return

    if callback_data == "publish_now":
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

            clear_draft(context)

            await query.edit_message_text(
                "تم النشر بنجاح على Telegram."
                + NEW_LINE
                + "رقم المنشور: "
                + str(sent_message.message_id)
            )

        except TelegramError as error:
            logger.exception(
                "Telegram publishing failed"
            )

            await query.edit_message_text(
                "فشل النشر على Telegram:"
                + NEW_LINE
                + str(error)
            )

        return

    if callback_data == "cancel_publish":
        clear_draft(context)

        await query.edit_message_text(
            "تم إلغاء النشر."
        )
        return

    await query.edit_message_text(
        "Unknown action. Callback: "
        + str(callback_data)
    )


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
                filters.TEXT & filters.COMMAND,
                receive_photo
            ),
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_photo
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

telegram_app.add_handler(
    CallbackQueryHandler(
        button_handler
    )
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
    version="0.5.1",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {
        "name": "MENA Content Agent",
        "status": "running",
        "version": "0.5.1"
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
