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

# =========================
# ENV
# =========================

TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# =========================
# SETTINGS
# =========================

warnings = defaultdict(int)

# Each chat keeps a short conversation history
chat_history = defaultdict(lambda: deque(maxlen=10))

LINK_PATTERN = re.compile(
    r"(https?://|t\.me/|telegram\.me/|www\.)",
    re.IGNORECASE
)

# =========================
# NOE AI
# =========================

def ask_noe(chat_id, user_name, user_text):
    try:
        history = list(chat_history[chat_id])

        messages = [
            {
                "role": "system",
                "content": (
                    "Your name is Noe. "
                    "You are a friendly Burmese-speaking chat companion "
                    "in a Telegram group. "

                    "Talk naturally like a normal person chatting with friends. "
                    "Do not sound like a customer-service bot. "
                    "Do not sound formal, robotic, or like an AI assistant. "

                    "Use natural everyday Burmese chat language. "
                    "Match the user's mood and style. "
                    "If they are casual, be casual. "
                    "If they joke, you can joke back. "
                    "If they are serious, answer seriously. "
                    "If they are sad, respond warmly. "

                    "Keep normal replies short and conversational. "
                    "Do not unnecessarily explain things. "
                    "Do not repeat the user's message. "
                    "Do not use words like 'ကျွန်ုပ်', 'အသုံးပြုသူ', "
                    "'ကူညီပေးနိုင်ပါတယ်', or other overly formal AI language. "

                    "Do not introduce yourself as an AI unless asked. "
                    "If someone directly asks whether you are an AI or bot, "
                    "answer honestly that you are an AI bot. "
                    "Never claim to be a real human. "

                    "Remember the recent conversation context and answer "
                    "based on what was actually said before. "

                    "When someone simply says hello, reply naturally. "
                    "For example, a simple 'မင်္ဂလာပါ 😄' is enough. "

                    "When someone asks what you are doing, answer casually "
                    "instead of giving a robotic explanation. "

                    "Do not turn every conversation into a help-desk response. "
                    "You are here to chat naturally with the group."
                ),
            }
        ]

        # Add recent conversation
        messages.extend(history)

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
                "messages": messages,
            },
            timeout=30,
        )

        if response.status_code != 200:
            print("OPENROUTER ERROR:", response.status_code)
            print(response.text)
            return "ခဏလေးနော် 😅"

        data = response.json()

        choices = data.get("choices")

        if not choices:
            print("AI RESPONSE ERROR:", data)
            return "ဟယ် ဘာပြန်ပြောရမလဲ 😅"

        reply = choices[0]["message"]["content"]

        if not reply:
            return "ခဏစဉ်းစားနေတယ် 😅"

        reply = reply.strip()

        # Save conversation
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
        return "ခဏလေးနော် 😅"


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "🎀 Noe ရောက်နေပြီနော် 😄\n\n"
            "စကားပြောလို့ရတယ်။\n"
            "🚫 Link Spam Auto Delete\n"
            "⚠️ 3 Warnings = Auto Mute"
        )


# =========================
# MESSAGE HANDLER
# =========================

async def check_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not message or not user or not chat:
        return

    # Ignore bots
    if user.is_bot:
        return

    text = message.text or ""

    if not text.strip():
        return

    # =========================
    # LINK SPAM
    # =========================

    if LINK_PATTERN.search(text):

        warnings[(chat.id, user.id)] += 1

        count = warnings[(chat.id, user.id)]

        try:
            await message.delete()
        except Exception as e:
            print("DELETE ERROR:", repr(e))

        # 3 warnings = mute
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
                    f"🔇 {user.first_name} ကို "
                    f"3 warnings ပြည့်လို့ mute လုပ်လိုက်ပြီနော်။"
                )

            except Exception as e:
                print("MUTE ERROR:", repr(e))

            warnings[(chat.id, user.id)] = 0

        else:

            await context.bot.send_message(
                chat.id,
                f"⚠️ {user.first_name} "
                f"Warning {count}/3"
            )

        return

    # =========================
    # AI CHAT
    # =========================

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


# =========================
# MAIN
# =========================

def main():

    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN မတွေ့ပါ"
        )

    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY မတွေ့ပါ"
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            check_message
        )
    )

    print("🎀 Noe Natural AI Group Bot Started")

    app.run_polling()


if __name__ == "__main__":
    main()