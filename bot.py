import os
import re
import asyncio
from collections import defaultdict, deque

import requests

from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

warnings = defaultdict(int)
chat_history = defaultdict(lambda: deque(maxlen=4))

LINK_PATTERN = re.compile(
    r"(https?://|t\.me/|telegram\.me/|www\.)",
    re.IGNORECASE
)


def ask_noe(chat_id, user_name, user_text):
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Noe in a Burmese Telegram group. "
                    "Talk naturally like a close Burmese friend. "
                    "Use simple everyday Burmese. "
                    "Keep replies short, usually one sentence. "
                    "Answer directly and naturally. "
                    "Do not sound like an AI assistant. "
                    "Do not use formal Burmese. "
                    "Do not use words like ကျွန်ုပ် or အသုံးပြုသူ. "
                    "Do not repeat the user's message. "
                    "Do not invent strange meanings or questions. "
                    "Never use emojis or decorative symbols. "
                    "Do not give long explanations unless necessary. "
                    "Match the user's casual speaking style. "
                    "Do not make up personal information. "
                    "If asked whether you are an AI or bot, answer honestly. "
                    "Never claim to be a real human."
                ),
            }
        ]

        messages.extend(list(chat_history[chat_id]))

        messages.append(
            {
                "role": "user",
                "content": f"{user_name}: {user_text}",
            }
        )

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openrouter/free",
                "models": [
                    "openrouter/free"
                ],
                "messages": messages,
                "max_tokens": 60,
                "temperature": 0.5,
            },
            timeout=20,
        )

        if response.status_code != 200:
            print("OPENROUTER ERROR:", response.status_code)
            print(response.text)
            return "ခဏလေး"

        data = response.json()
        choices = data.get("choices")

        if not choices:
            print("NO CHOICES:", data)
            return "ခဏလေး"

        reply = choices[0].get("message", {}).get("content", "")

        if not reply:
            print("EMPTY REPLY:", data)
            return "ခဏလေး"

        reply = reply.strip()

        # Remove emojis
        reply = re.sub(
            r"[\U0001F300-\U0001FAFF"
            r"\U00002700-\U000027BF"
            r"\U0001F1E6-\U0001F1FF]+",
            "",
            reply
        ).strip()

        if not reply:
            return "ခဏလေး"

        chat_history[chat_id].append(
            {
                "role": "user",
                "content": f"{user_name}: {user_text}",
            }
        )

        chat_history[chat_id].append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        return reply

    except Exception as e:
        print("AI ERROR:", repr(e))
        return "ခဏလေး"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "Noe ရောက်နေပြီ"
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

    if not text.strip():
        return

    if LINK_PATTERN.search(text):
        warnings[(chat.id, user.id)] += 1
        count = warnings[(chat.id, user.id)]

        try:
            await message.delete()
        except Exception as e:
            print("DELETE ERROR:", repr(e))

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
                    f"{user.first_name} ကို 3 warnings ပြည့်လို့ mute လုပ်လိုက်ပြီ"
                )

            except Exception as e:
                print("MUTE ERROR:", repr(e))

            warnings[(chat.id, user.id)] = 0

        else:
            await context.bot.send_message(
                chat.id,
                f"{user.first_name} Warning {count}/3"
            )

        return

    if not OPENROUTER_API_KEY:
        print("OPENROUTER_API_KEY မတွေ့ပါ")
        return

    reply = await asyncio.to_thread(
        ask_noe,
        chat.id,
        user.first_name,
        text
    )

    if reply:
        await message.reply_text(reply)


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN မတွေ့ပါ")

    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY မတွေ့ပါ")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            check_message
        )
    )

    print("Noe Stable Natural Chat Started")

    app.run_polling()


if __name__ == "__main__":
    main()
