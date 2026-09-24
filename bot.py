import os
import re
import time
import asyncio
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

# AI request ထပ်ခါထပ်ခါ မပို့အောင်
last_request = defaultdict(float)
REQUEST_COOLDOWN = 2

LINK_PATTERN = re.compile(
    r"(https?://|t\.me/|telegram\.me/|www\.)",
    re.IGNORECASE
)


def clean_reply(reply):
    if not reply:
        return None

    reply = reply.strip()

    # Emoji ဖယ်
    reply = re.sub(
        r"[\U0001F300-\U0001FAFF"
        r"\U00002700-\U000027BF"
        r"\U0001F1E6-\U0001F1FF]+",
        "",
        reply
    ).strip()

    return reply if reply else None


def ask_noe(chat_id, user_name, user_text):

    now = time.time()

    # Request အရမ်းမြန်ရင် မပို့သေး
    wait_time = REQUEST_COOLDOWN - (
        now - last_request[chat_id]
    )

    if wait_time > 0:
        time.sleep(wait_time)

    last_request[chat_id] = time.time()

    messages = [
        {
            "role": "system",
            "content": """
မင်းက Noe ဆိုတဲ့ Telegram group chat bot ပါ။

မြန်မာသူငယ်ချင်းတစ်ယောက်နဲ့ စကားပြောသလို သဘာဝကျကျ ပြောပါ။

စည်းကမ်းများ:
- မြန်မာစကားကို နေ့စဉ်သုံးစကားပုံစံနဲ့ ပြောပါ။
- စကားတိုတိုနဲ့ တိုက်ရိုက်ဖြေပါ။
- အရမ်း formal မပြောပါနဲ့။
- "ကျွန်ုပ်", "အသုံးပြုသူ", "AI assistant" စတဲ့ စကားတွေ မသုံးပါနဲ့။
- Emoji လုံးဝ မသုံးပါနဲ့။
- User ပြောတာကို ပြန်ကူးမပြောပါနဲ့။
- User ရဲ့ အဓိပ္ပာယ်ကို နားလည်ပြီး တိုက်ရိုက်ဖြေပါ။
- အရင် message တွေကို context အဖြစ် အသုံးပြုပါ။
- မေးခွန်းတစ်ခုကို မေးခွန်းနဲ့ ပြန်မဖြေပါနဲ့။
- အဓိပ္ပာယ်မရှိတဲ့ စကား မဖန်တီးပါနဲ့။
- User က ရင်းနှီးတဲ့ပုံစံနဲ့ပြောရင် ရင်းနှီးတဲ့ပုံစံနဲ့ ပြန်ပါ။
- လိုအပ်ရင် တစ်ကြောင်းတည်းနဲ့ ဖြေပါ။
- အကြောင်းအရာရှင်းပြဖို့လိုမှသာ ပိုရှည်ပါ။
- User က "ဘယ်မှာ" လို့မေးရင် အရင် context ကိုကြည့်ပြီး ဖြေပါ။
- User က "ဘာလုပ်" လို့ပြောရင် အရင်စကားနဲ့ဆက်စပ်ပြီး ဖြေပါ။
- Bot/AI ဟုတ်လားလို့ တိုက်ရိုက်မေးရင် ရိုးသားစွာ ဖြေပါ။
- ကိုယ့်ကိုယ်ကို လူအစစ်လို့ မပြောပါနဲ့။
"""
        }
    ]

    messages.extend(list(history[chat_id]))

    messages.append({
        "role": "user",
        "content": f"{user_name}: {user_text}"
    })

    for attempt in range(3):

        try:

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://openrouter.ai/",
                    "X-Title": "Noe Telegram Bot"
                },
                json={
                    "model": "meta-llama/llama-3.3-8b-instruct:free",
                    "messages": messages,
                    "max_tokens": 100,
                    "temperature": 0.6
                },
                timeout=30
            )

            print("AI STATUS:", response.status_code)

            # 429 Rate Limit
            if response.status_code == 429:

                print(
                    "AI ERROR 429 - RATE LIMIT"
                )

                if attempt < 2:

                    wait = 5 * (attempt + 1)

                    print(
                        f"Retrying in {wait} seconds..."
                    )

                    time.sleep(wait)

                    continue

                print(
                    "AI ERROR 429:",
                    response.text
                )

                return None

            # Provider error
            if response.status_code != 200:

                print(
                    "AI PROVIDER ERROR:",
                    response.text
                )

                return None

            try:
                data = response.json()

            except Exception as e:

                print(
                    "AI JSON ERROR:",
                    repr(e)
                )

                return None

            choices = data.get("choices")

            if not choices:

                print(
                    "AI EMPTY:",
                    data
                )

                return None

            message_data = choices[0].get(
                "message",
                {}
            )

            reply = message_data.get(
                "content",
                ""
            )

            reply = clean_reply(reply)

            if not reply:

                print(
                    "AI NO TEXT:",
                    data
                )

                return None

            # History သိမ်း
            history[chat_id].append({
                "role": "user",
                "content": f"{user_name}: {user_text}"
            })

            history[chat_id].append({
                "role": "assistant",
                "content": reply
            })

            return reply

        except requests.exceptions.Timeout:

            print(
                "AI TIMEOUT:",
                attempt + 1
            )

            if attempt < 2:

                time.sleep(3)

                continue

            return None

        except requests.exceptions.RequestException as e:

            print(
                "AI REQUEST ERROR:",
                repr(e)
            )

            return None

        except Exception as e:

            print(
                "AI EXCEPTION:",
                repr(e)
            )

            return None

    return None


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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

    # Bot message မဖတ်
    if user.is_bot:
        return

    text = message.text or ""

    if not text.strip():
        return

    # -----------------------------
    # LINK SPAM
    # -----------------------------

    if LINK_PATTERN.search(text):

        key = (
            chat.id,
            user.id
        )

        warnings[key] += 1

        count = warnings[key]

        try:

            await message.delete()

        except Exception as e:

            print(
                "DELETE ERROR:",
                repr(e)
            )

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

                print(
                    "MUTE ERROR:",
                    repr(e)
                )

            warnings[key] = 0

        else:

            try:

                await context.bot.send_message(
                    chat.id,
                    f"{user.first_name} Warning {count}/3"
                )

            except Exception as e:

                print(
                    "WARNING MESSAGE ERROR:",
                    repr(e)
                )

        return

    # -----------------------------
    # AI CHAT
    # -----------------------------

    reply = await asyncio.to_thread(
        ask_noe,
        chat.id,
        user.first_name,
        text
    )

    # AI reply မရရင် ဘာမှမပို့
    if reply is None:
        return

    try:

        await message.reply_text(
            reply
        )

    except Exception as e:

        print(
            "TELEGRAM REPLY ERROR:",
            repr(e)
        )


def main():

    if not TOKEN:

        raise RuntimeError(
            "BOT_TOKEN မတွေ့ပါ"
        )

    if not OPENROUTER_API_KEY:

        raise RuntimeError(
            "OPENROUTER_API_KEY မတွေ့ပါ"
        )

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

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

    print(
        "NOE AI CHAT STARTED"
    )

    app.run_polling()


if __name__ == "__main__":
    main()
