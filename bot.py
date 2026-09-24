import os
import re
import asyncio
import time
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

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "meta-llama/llama-3.3-70b-instruct:free"

warnings = defaultdict(int)
history = defaultdict(lambda: deque(maxlen=10))

# User တစ်ယောက်ချင်းစီ AI request အကြား
# အနည်းဆုံး 2 seconds ခြား
last_request = defaultdict(float)
REQUEST_COOLDOWN = 2

LINK_PATTERN = re.compile(
    r"(https?://|t\.me/|telegram\.me/|www\.)",
    re.IGNORECASE
)


# =========================
# AI CLEAN
# =========================

def clean_reply(text):

    if not text:
        return None

    if isinstance(text, list):
        parts = []

        for item in text:
            if isinstance(item, dict):
                value = item.get("text")

                if value:
                    parts.append(str(value))

            elif isinstance(item, str):
                parts.append(item)

        text = "".join(parts)

    text = str(text).strip()

    # Emoji ဖျက်
    text = re.sub(
        r"[\U0001F300-\U0001FAFF"
        r"\U00002700-\U000027BF"
        r"\U0001F1E6-\U0001F1FF]+",
        "",
        text
    )

    text = text.strip()

    if not text:
        return None

    return text


# =========================
# ASK AI
# =========================

def ask_noe(chat_id, user_name, user_text):

    now = time.time()

    # Request အရမ်းမြန်မသွားအောင်
    elapsed = now - last_request[chat_id]

    if elapsed < REQUEST_COOLDOWN:
        time.sleep(REQUEST_COOLDOWN - elapsed)

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

    # Previous conversation
    messages.extend(list(history[chat_id]))

    # Current message
    messages.append({
        "role": "user",
        "content": f"{user_name}: {user_text}"
    })

    # =========================
    # TRY REQUEST
    # =========================

    max_attempts = 4

    for attempt in range(1, max_attempts + 1):

        try:

            print(
                f"AI REQUEST: attempt={attempt} "
                f"chat={chat_id} "
                f"user={user_name}"
            )

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",

                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://openrouter.ai/",
                    "X-Title": "Noe Telegram Bot"
                },

                json={
                    "model": MODEL,
                    "messages": messages,
                    "max_tokens": 100,
                    "temperature": 0.6
                },

                timeout=30
            )

            print("AI STATUS:", response.status_code)

            # =========================
            # SUCCESS
            # =========================

            if response.status_code == 200:

                try:
                    data = response.json()
                except Exception as e:
                    print("AI JSON ERROR:", repr(e))
                    return None

                choices = data.get("choices")

                if not choices:
                    print("AI EMPTY CHOICES:", data)
                    return None

                message_data = choices[0].get("message", {})

                if not isinstance(message_data, dict):
                    print("AI BAD MESSAGE:", message_data)
                    return None

                content = message_data.get("content")

                reply = clean_reply(content)

                if not reply:
                    print("AI NO TEXT:", data)
                    return None

                # =========================
                # SAVE HISTORY
                # =========================

                history[chat_id].append({
                    "role": "user",
                    "content": f"{user_name}: {user_text}"
                })

                history[chat_id].append({
                    "role": "assistant",
                    "content": reply
                })

                print("AI OK:", reply)

                return reply

            # =========================
            # RATE LIMIT 429
            # =========================

            if response.status_code == 429:

                print("AI 429 RATE LIMIT")

                if attempt < max_attempts:

                    # Retry-After ရှိရင် အသုံးပြု
                    retry_after = response.headers.get(
                        "Retry-After"
                    )

                    try:
                        wait_time = float(retry_after)
                    except Exception:
                        wait_time = attempt * 5

                    # အများကြီးမစောင့်စေဖို့
                    wait_time = min(wait_time, 30)

                    print(
                        f"AI 429 WAIT: {wait_time} seconds"
                    )

                    time.sleep(wait_time)

                    continue

                print("AI 429 FINAL")
                return None

            # =========================
            # OTHER ERRORS
            # =========================

            print(
                "AI ERROR:",
                response.status_code,
                response.text[:1000]
            )

            return None

        except requests.Timeout:

            print(
                f"AI TIMEOUT attempt={attempt}"
            )

            if attempt < max_attempts:

                time.sleep(3)

                continue

            return None

        except requests.RequestException as e:

            print(
                "AI REQUEST ERROR:",
                repr(e)
            )

            if attempt < max_attempts:

                time.sleep(3)

                continue

            return None

        except Exception as e:

            print(
                "AI EXCEPTION:",
                repr(e)
            )

            return None

    return None


# =========================
# /START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.message:

        await update.message.reply_text(
            "Noe ရောက်နေပြီ"
        )


# =========================
# MESSAGE CHECK
# =========================

async def check_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not message:
        return

    if not user:
        return

    if not chat:
        return

    # Bot message မဖတ်
    if user.is_bot:
        return

    text = message.text or ""

    if not text.strip():
        return

    print(
        f"MESSAGE: chat={chat.id} "
        f"user={user.first_name} "
        f"text={text}"
    )

    # =========================
    # LINK SPAM
    # =========================

    if LINK_PATTERN.search(text):

        key = (chat.id, user.id)

        warnings[key] += 1

        count = warnings[key]

        print(
            f"LINK WARNING: "
            f"{user.first_name} "
            f"{count}/3"
        )

        try:

            await message.delete()

        except Exception as e:

            print(
                "DELETE ERROR:",
                repr(e)
            )

        # =========================
        # 3 WARNINGS = MUTE
        # =========================

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
                    f"{user.first_name} ကို "
                    f"3 warnings ပြည့်လို့ mute လုပ်လိုက်ပြီ"
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

    # =========================
    # SEND TO AI
    # =========================

    print("SENDING TO AI...")

    reply = await asyncio.to_thread(
        ask_noe,
        chat.id,
        user.first_name,
        text
    )

    # =========================
    # AI FAILED
    # =========================

    if reply is None:

        print(
            "AI REPLY FAILED - NO MESSAGE SENT"
        )

        return

    # =========================
    # SEND AI REPLY
    # =========================

    try:

        await message.reply_text(
            reply
        )

        print("TELEGRAM REPLY SENT")

    except Exception as e:

        print(
            "TELEGRAM REPLY ERROR:",
            repr(e)
        )


# =========================
# ERROR HANDLER
# =========================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "TELEGRAM ERROR:",
        repr(context.error)
    )


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

    print("BOT TOKEN: OK")
    print("OPENROUTER KEY: OK")
    print("MODEL:", MODEL)

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

    app.add_error_handler(
        error_handler
    )

    print(
        "NOE AI CHAT STARTED"
    )

    app.run_polling(
        drop_pending_updates=True
    )


# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()
