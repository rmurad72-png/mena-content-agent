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


TITLE, CONTENT, PHOTO = range(3)
EDIT_TITLE, EDIT_CONTENT, EDIT_PHOTO = range(3, 6)

NEW_LINE = chr(10)
SKIP_COMMAND = "/تخطي"
CANCEL_COMMAND = "/إلغاء"


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


def clear_draft(context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("draft_title", None)
    context.user_data.pop("draft_content", None)
    context.user_data.pop("draft_photo_file_id", None)
    context.user_data.pop("draft_photo_url", None)
    context.user_data.pop("selected_channel", None)


def build_post_text(
    title: str,
    content: str
) -> str:
    return (
        title
        + NEW_LINE
        + NEW_LINE
        + content
    )


def main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "إنشاء مسودة",
                callback_data="create_draft"
            )
        ],
        [
            InlineKeyboardButton(
                "قوالب جاهزة",
                callback_data="templates"
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


def draft_review_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "تعديل العنوان",
                callback_data="edit_title"
            ),
            InlineKeyboardButton(
                "تعديل المحتوى",
                callback_data="edit_content"
            ),
        ],
        [
            InlineKeyboardButton(
                "تعديل الصورة",
                callback_data="edit_photo"
            )
        ],
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


def template_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "خبر مختصر",
                callback_data="template_news"
            )
        ],
        [
            InlineKeyboardButton(
                "نصيحة",
                callback_data="template_tip"
            )
        ],
        [
            InlineKeyboardButton(
                "منشور تعريفي",
                callback_data="template_intro"
            )
        ],
        [
            InlineKeyboardButton(
                "رجوع",
                callback_data="back_home"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def build_template(
    template_name: str
) -> tuple[str, str]:
    if template_name == "news":
        return (
            "خبر اليوم",
            "اكتب هنا ملخص الخبر وأهم التفاصيل."
        )

    if template_name == "tip":
        return (
            "نصيحة اليوم",
            "اكتب هنا النصيحة أو المعلومة المفيدة."
        )

    return (
        "منشور تعريفي",
        "اكتب هنا التعريف بالموضوع أو الخدمة."
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
        "مرحبًا بك في وكيل صناعة المحتوى. اختر إجراءً:",
        reply_markup=main_keyboard()
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return

    if not is_admin(update):
        await update.message.reply_text(
            "غير مسموح."
        )
        return

    help_text = (
        "الأوامر المتاحة:"
        + NEW_LINE
        + "/start - القائمة الرئيسية"
        + NEW_LINE
        + "/myid - عرض رقم الحساب"
        + NEW_LINE
        + "/cancel - إلغاء العملية الحالية"
        + NEW_LINE
        + "/إلغاء - إلغاء المسودة"
    )

    await update.message.reply_text(help_text)


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


async def template_start(
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

    await query.edit_message_text(
        "اختر قالبًا:",
        reply_markup=template_keyboard()
    )

    return ConversationHandler.END


async def receive_template(
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

    template_name = query.data.replace(
        "template_",
        ""
    )

    title, content = build_template(
        template_name
    )

    context.user_data["draft_title"] = title
    context.user_data["draft_content"] = content

    await query.edit_message_text(
        "تم اختيار القالب."
        + NEW_LINE
        + "أرسل عنوانًا جديدًا أو استخدم العنوان المقترح:"
        + NEW_LINE
        + title
    )

    return EDIT_TITLE


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
        "أرسل صورة، أو رابط صورة، أو اكتب /تخطي."
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
        possible_url = update.message.text.strip()

        if (
            possible_url.startswith("http://")
            or possible_url.startswith("https://")
        ):
            context.user_data["draft_photo_url"] = (
                possible_url
            )

            context.user_data.pop(
                "draft_photo_file_id",
                None
            )
        else:
            await update.message.reply_text(
                "أرسل صورة، أو رابطًا يبدأ بـ http أو https، "
                "أو اكتب /تخطي."
            )
            return PHOTO

    else:
        await update.message.reply_text(
            "أرسل صورة، أو رابط صورة، أو اكتب /تخطي."
        )
        return PHOTO

    await send_preview(
        update,
        context
    )

    return ConversationHandler.END


async def skip_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return ConversationHandler.END

    context.user_data.pop(
        "draft_photo_file_id",
        None
    )

    context.user_data.pop(
        "draft_photo_url",
        None
    )

    await send_preview(
        update,
        context
    )

    return ConversationHandler.END


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

    has_photo = (
        bool(
            context.user_data.get(
                "draft_photo_file_id"
            )
        )
        or bool(
            context.user_data.get(
                "draft_photo_url"
            )
        )
    )

    photo_status = "موجودة" if has_photo else "غير موجودة"

    preview_text = (
        "معاينة المسودة"
        + NEW_LINE
        + NEW_LINE
        + "العنوان:"
        + NEW_LINE
        + title
        + NEW_LINE
        + NEW_LINE
        + "المحتوى:"
        + NEW_LINE
        + content
        + NEW_LINE
        + NEW_LINE
        + "الصورة: "
        + photo_status
    )

    keyboard = draft_review_keyboard()

    if update.message is not None:
        if context.user_data.get("draft_photo_file_id"):
            await update.message.reply_photo(
                photo=context.user_data[
                    "draft_photo_file_id"
                ],
                caption=preview_text,
                reply_markup=keyboard
            )
            return

        if context.user_data.get("draft_photo_url"):
            try:
                await update.message.reply_photo(
                    photo=context.user_data[
                        "draft_photo_url"
                    ],
                    caption=preview_text,
                    reply_markup=keyboard
                )
                return
            except TelegramError:
                await update.message.reply_text(
                    "تعذر تحميل رابط الصورة. "
                    "يمكنك تعديل الصورة أو حذفها.",
                    reply_markup=keyboard
                )
                return

        await update.message.reply_text(
            preview_text,
            reply_markup=keyboard
        )
        return

    if update.callback_query is not None:
        await update.callback_query.edit_message_text(
            preview_text,
            reply_markup=keyboard
        )


async def edit_title_start(
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

    await query.edit_message_text(
        "أرسل العنوان الجديد."
    )

    return EDIT_TITLE


async def edit_title_receive(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return ConversationHandler.END

    if update.message.text is None:
        await update.message.reply_text(
            "أرسل نصًا فقط."
        )
        return EDIT_TITLE

    title = update.message.text.strip()

    if not title:
        await update.message.reply_text(
            "العنوان لا يمكن أن يكون فارغًا."
        )
        return EDIT_TITLE

    context.user_data["draft_title"] = title

    await send_preview(
        update,
        context
    )

    return ConversationHandler.END


async def edit_content_start(
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

    await query.edit_message_text(
        "أرسل المحتوى الجديد."
    )

    return EDIT_CONTENT


async def edit_content_receive(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return ConversationHandler.END

    if update.message.text is None:
        await update.message.reply_text(
            "أرسل نصًا فقط."
        )
        return EDIT_CONTENT

    content = update.message.text.strip()

    if not content:
        await update.message.reply_text(
            "المحتوى لا يمكن أن يكون فارغًا."
        )
        return EDIT_CONTENT

    context.user_data["draft_content"] = content

    await send_preview(
        update,
        context
    )

    return ConversationHandler.END


async def edit_photo_start(
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

    await query.edit_message_text(
        "أرسل صورة جديدة، أو رابط صورة، أو اكتب /حذف_الصورة."
    )

    return EDIT_PHOTO


async def edit_photo_receive(
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

        await send_preview(
            update,
            context
        )

        return ConversationHandler.END

    if update.message.text:
        possible_url = update.message.text.strip()

        if (
            possible_url.startswith("http://")
            or possible_url.startswith("https://")
        ):
            context.user_data["draft_photo_url"] = (
                possible_url
            )

            context.user_data.pop(
                "draft_photo_file_id",
                None
            )

            await send_preview(
                update,
                context
            )

            return ConversationHandler.END

    await update.message.reply_text(
        "أرسل صورة، أو رابطًا صحيحًا، أو اكتب /حذف_الصورة."
    )

    return EDIT_PHOTO


async def delete_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message is None:
        return ConversationHandler.END

    context.user_data.pop(
        "draft_photo_file_id",
        None
    )

    context.user_data.pop(
        "draft_photo_url",
        None
    )

    await send_preview(
        update,
        context
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

    if query.data == "show_help":
        await query.edit_message_text(
            "استخدم /start لفتح القائمة الرئيسية."
        )
        return

    if query.data == "templates":
        await query.edit_message_text(
            "اختر قالبًا:",
            reply_markup=template_keyboard()
        )
        return

    if query.data == "back_home":
        await query.edit_message_text(
            "اختر إجراءً:",
            reply_markup=main_keyboard()
        )
        return

    if query.data.startswith("template_"):
        await receive_template(
            update,
            context
        )
        return

    if query.data == "edit_title":
        await query.edit_message_text(
            "أرسل العنوان الجديد."
        )
        context.user_data["editing"] = "title"
        return

    if query.data == "edit_content":
        await query.edit_message_text(
            "أرسل المحتوى الجديد."
        )
        context.user_data["editing"] = "content"
        return

    if query.data == "edit_photo":
        await query.edit_message_text(
            "أرسل صورة جديدة، أو رابط صورة، "
            "أو اكتب /حذف_الصورة."
        )
        context.user_data["editing"] = "photo"
        return

    if query.data == "approve_first":
        await query.edit_message_text(
            "تم اعتماد المسودة. اختر قناة النشر:",
            reply_markup=channel_keyboard()
        )
        return

    if query.data == "reject_draft":
        clear_draft(context)

        await query.edit_message_text(
            "تم رفض المسودة."
        )
        return

    if query.data.startswith("channel_"):
        channel_name = query.data.replace(
            "channel_",
        
