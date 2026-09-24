import os
import re
import requests
from collections import defaultdict

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
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are Noe, a Burmese Telegram group chat bot. "
                            "Talk like a close Burmese friend. "
                            "Use very natural everyday Burmese. "
                            "Keep replies short, usually one sentence. "
                            "Do not sound formal or robotic. "
                            "Never use emojis. "
                            "Never use 'ကျွန်ုပ်', 'အသုံးပြုသူ', or formal assistant language. "
                            "Do not repeat the user's words. "
                            "Do not make up strange meanings. "
                            "If someone says 'မင်္ဂလာပါ', simply say 'မင်္ဂလာပါ'. "
                            "If someone asks 'ဘာလုပ်နေတာလဲ', reply naturally like "
                            "'ဒီမှာပဲ နင်ကရော'. "
                            "If someone asks 'နေကောင်းလား', reply naturally like "
                            "'ကောင်းတယ် နင်ရော'. "
                            "If someone asks whether you are a bot or AI, answer honestly."
                        )
                    },
                    {
                        "role": "user",
                        "content": user_text
                    }
                ],
                "max_tokens": 50,
                "temperature": 0.4
            },
            timeout=15
        )

        if response.status_code != 200:
            print("AI ERROR:", response.status_code, response.text)
            return None

        data = response.json()
        choices = data.get("choices", [])

        if not choices:
            print("NO RESPONSE:", data)
            return None

        reply = choices[0].get("message", {}).get("content", "")

        if not reply:
            return None

        reply = reply.strip()

        # Emoji ဖျက်
        reply = re.sub(
            r"[\U0001F300-\U0001FAFF"
            r"\U00002700-\U000027BF"
            r"\U0001F1E6-\U0001F1FF]+",
            "",
            reply
        ).strip()

        return reply if reply else None

    except Exception as e:
        print("AI ERROR:", repr(e))
        return None


def simple_reply(text):
    t = text.strip()

    if t == "မင်္ဂလာပါ":
        return "မင်္ဂလာပါ"

    if t in ["ဟယ်လို", "ဟလို"]:
        return "ဟယ်လို"

    if t == "နေကောင်းလား":
        return "ကောင်းတယ် နင်ရော"

    if t == "ဘာလုပ်နေတာလဲ":
        return "ဒီမှာပဲ နင်ကရော"

    if t == "စားပြီးပြီလား":
        return "မစားရသေးဘူး နင်ရော"

    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Noe ရောက်နေပြီ")


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

    # Link spam
    if LINK_PATTERN.search(text):
        key = (chat.id, user.id)
        warnings[key] += 1

        count = warnings[key]

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

            warnings[key] = 0

        else:
            await context.bot.send_message(
                chat.id,
                f"{user.first_name} Warning {count}/3"
            )

        return

    # အရင်ဆုံး ရိုးရိုးစာတွေကို ချက်ချင်းပြန်
    reply = simple_reply(text)

    # မရှိရင် AI ကိုမေး
    if reply is None:
        reply = ask_noe(text)

    # AI မရရင် fallback
    if reply is None:
        reply = "အင်း ပြောလေ"

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

    print("NOE STARTED")

    app.run_polling()


if __name__ == "__main__":
    main()
