import os
import re
import requests
from collections import defaultdict, deque

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
history = defaultdict(lambda: deque(maxlen=10))

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
                    "မင်းက Noe ဆိုတဲ့ Telegram group chat bot ပါ။ "
                    "မြန်မာသူငယ်ချင်းတစ်ယောက်နဲ့ chat နေသလို သဘာဝကျကျ ပြောပါ။ "
                    "အသုံးများတဲ့ နေ့စဉ်မြန်မာစကားကို သုံးပါ။ "
                    "စကားတိုတိုနဲ့ တိုက်ရိုက်ပြန်ပါ။ "
                    "Formal မပြောပါနဲ့။ "
                    "ကျွန်ုပ်၊ အသုံးပြုသူ၊ AI assistant စတဲ့ formal စကားတွေ မသုံးပါနဲ့။ "
                    "Emoji မသုံးပါနဲ့။ "
                    "User ပြောတဲ့အကြောင်းအရာကို သေချာနားလည်ပြီး တိုက်ရိုက်ဖြေပါ။ "
                    "အရင် message တွေကို context အနေနဲ့ အသုံးပြုပြီး "
                    "နောက် message နဲ့ ဆက်စပ်အောင် ပြန်ပါ။ "
                    "အကြောင်းမဲ့ မေးခွန်းတွေ မဖန်တီးပါနဲ့။ "
                    "User က စကားတစ်ခွန်းပြောရင် အဲဒီစကားနဲ့ သက်ဆိုင်တဲ့ "
                    "သဘာဝကျတဲ့ တုံ့ပြန်မှုကို ပေးပါ။ "
                    "အဖြေကို မရှည်စေပါနဲ့။ "
                    "User က ဟာသပြောရင် သဘာဝကျကျ ပြန်ပြောပါ။ "
                    "User က မေးခွန်းမေးရင် အဖြေကို တိုက်ရိုက်ပေးပါ။ "
                    "User က ရင်းနှီးတဲ့စကားသုံးရင် ရင်းနှီးတဲ့စကားနဲ့ ပြန်ပါ။ "
                    "Bot သို့မဟုတ် AI ဟုတ်လားလို့ တိုက်ရိုက်မေးရင် ရိုးသားစွာ ဖြေပါ။ "
                    "ကိုယ့်ကိုယ်ကို လူအစစ်လို့ မပြောပါနဲ့။"
                )
            }
        ]

        # အရင်စကားတွေ ထည့်မယ်
        messages.extend(list(history[chat_id]))

        # လက်ရှိ message
        messages.append({
            "role": "user",
            "content": f"{user_name}: {user_text}"
        })

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": messages,
                "max_tokens": 80,
                "temperature": 0.5
            },
            timeout=20
        )

        if response.status_code != 200:
            print("AI ERROR:", response.status_code)
            print(response.text)
            return None

        data = response.json()
        choices = data.get("choices", [])

        if not choices:
            print("NO CHOICES:", data)
            return None

        reply = choices[0].get(
            "message", {}
        ).get(
            "content", ""
        ).strip()

        if not reply:
            return None

        # Emoji ဖယ်
        reply = re.sub(
            r"[\U0001F300-\U0001FAFF"
            r"\U00002700-\U000027BF"
            r"\U0001F1E6-\U0001F1FF]+",
            "",
            reply
        ).strip()

        if not reply:
            return None

        # History ထဲသိမ်း
        history[chat_id].append({
            "role": "user",
            "content": f"{user_name}: {user_text}"
        })

        history[chat_id].append({
            "role": "assistant",
            "content": reply
        })

        return reply

    except Exception as e:
        print("AI ERROR:", repr(e))
        return None


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

    # စကားတိုင်း AI ကိုပို့
    reply = await __import__("asyncio").to_thread(
        ask_noe,
        chat.id,
        user.first_name,
        text
    )

    if reply is None:
        reply = "အင်း"

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

    print("NOE NATURAL CHAT STARTED")

    app.run_polling()


if __name__ == "__main__":
    main()