import os
import re
from collections import defaultdict

from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

warnings = defaultdict(int)

LINK_PATTERN = re.compile(
    r"(https?://|t\.me/|telegram\.me/|www\.)",
    re.IGNORECASE
)

REPLIES = {
    "မင်္ဂလာပါ": "မင်္ဂလာပါ 😄 ဘာလုပ်နေကြတာလဲ?",
    "ဟယ်လို": "ဟယ်လို 👋",
    "hello": "Hello 😄",
    "hi": "Hi 👋",
    "ဟုတ်": "ဟုတ်ပါတယ် 😄",
    "ကျေးဇူး": "ရပါတယ်ဗျာ ❤️",
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Group Help Bot Online!\n\n"
        "🚫 Link spam auto delete\n"
        "⚠️ 3 Warnings = Auto Mute"
    )


async def check_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not message or not user or not chat:
        return

    # Bot message ကို မစစ်
    if user.is_bot:
        return

    text = message.text or ""

    # Link spam
    if LINK_PATTERN.search(text):
        warnings[(chat.id, user.id)] += 1
        count = warnings[(chat.id, user.id)]

        try:
            await message.delete()
        except Exception:
            pass

        if count >= 3:
            try:
                await context.bot.restrict_chat_member(
                    chat.id,
                    user.id,
                    permissions=ChatPermissions(can_send_messages=False)
                )

                await context.bot.send_message(
                    chat.id,
                    f"🔇 {user.first_name} ကို 3 warnings ပြည့်လို့ mute လုပ်လိုက်ပါပြီ။"
                )
            except Exception:
                pass

            warnings[(chat.id, user.id)] = 0

        else:
            await context.bot.send_message(
                chat.id,
                f"⚠️ {user.first_name} Warning {count}/3"
            )

        return

    # Auto reply
    lower_text = text.lower()

    for keyword, reply in REPLIES.items():
        if keyword.lower() in lower_text:
            await message.reply_text(reply)
            break


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN မတွေ့ပါ")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            check_message
        )
    )

    print("🤖 Group Help Bot Started")
    app.run_polling()


if __name__ == "__main__":
    main()