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

import requests

TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

warnings = defaultdict(int)

LINK_PATTERN = re.compile(
    r"(https?://|t\.me/|telegram\.me/|www\.)",
    re.IGNORECASE
)


def ask_noe(user_text):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openrouter/free",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Your name is Noe. "
                            "You are a friendly Burmese-speaking AI group assistant. "
                            "Reply naturally, warmly and briefly. "
                            "Use Burmese when the user speaks Burmese. "
                            "You are an AI bot, not a real human. "
                            "Do not claim to be a real person."
                        ),
                    },
                    {
                        "role": "user",
                        "content": user_text,
                    },
                ],
            },
            timeout=30,
        )

        data = response.json()

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("AI ERROR:", e)
        return "အခုခဏ AI ပြန်မဖြေနိုင်သေးဘူးနော် 😅"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎀 Noe AI Online!\n\n"
        "🤖 Natural AI Reply\n"
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
                    permissions=ChatPermissions(
                        can_send_messages=False
                    )
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

    # AI reply
    if not OPENROUTER_API_KEY:
        return

    reply = ask_noe(text)

    if reply:
        await message.reply_text(reply)


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN မတွေ့ပါ")

    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY မတွေ့ပါ")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            check_message
        )
    )

    print("🎀 Noe AI Group Bot Started")
    app.run_polling()


if __name__ == "__main__":
    main()