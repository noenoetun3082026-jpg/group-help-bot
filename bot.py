import os
import random
import time
import json

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# SETTINGS
# =========================

TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not TOKEN:
    print("ERROR: BOT_TOKEN is missing")
    raise SystemExit(1)

REPLY_CHANCE = 0.75
REPLY_COOLDOWN = 0.8
STICKER_LIMIT = 150

STICKER_FILE = "stickers.json"
CUSTOM_FILE = "replies.json"

last_reply_text = {}
last_reply_time = {}
last_user = {}
last_sticker = {}
chat_history = {}

# =========================
# NORMAL REPLIES
# =========================

NORMAL = [
    "သူခိုး",
    "စပ့",
    "ငါလဲဂေ့",
    "မိုးကိုး မရွားဘူးရေးးး",
    "လာပြီလေ",
    "စီ",
    "သေပြ",
    "နယူး",
    "ဆွေ",
    "စောင်း",
    "ဘာလုပ်နေတာလဲ",
    "ဟုတ်လား",
    "အဲ့လိုလား",
    "ငါလဲမသိဘူး",
    "ဘာဖြစ်တာလဲ",
    "အေးလေ",
    "အဲ့ဒါပဲ",
    "ပြောလေ",
    "ဆက်ပြော",
    "နားထောင်နေတယ်",
    "ဟုတ်တယ်",
    "မဟုတ်ဘူးထင်တယ်",
    "အဲ့တာကတော့ဟုတ်တယ်",
    "ဘာတွေပြောနေတာလဲ",
    "မသိဘူးဟ",
    "အေးဆေး",
    "လာပါ",
    "မင်းကလဲ",
    "တော်ပါတော့",
    "အဲ့လိုမလုပ်နဲ့",
    "ဘာလဲဟ",
    "အခုမှလာတာ",
    "ငါလဲအခုရောက်တာ",
    "ရှိတယ်",
    "မရှိဘူး",
    "ရှိပါတယ်",
    "မေးလေ",
    "ပြောကြည့်",
    "အင်း",
    "အင်းပါ",
    "ဟုတ်",
    "ဟုတ်ကဲ့",
    "အိုကေ",
    "ရတယ်",
    "မရဘူး",
    "အဆင်ပြေတယ်",
    "အဆင်မပြေဘူး",
    "ကြည့်မယ်",
    "ထားလိုက်",
    "မပြောတော့ဘူး",
    "ဘာမှမဟုတ်ပါဘူး",
    "အေးပါ",
    "နောက်မှပြော",
    "အခုမအားဘူး",
    "အားတယ်",
    "ဘာလိုချင်တာလဲ",
    "ပြောပါဦး",
    "ကြားတယ်",
    "မကြားဘူး",
    "ပြန်ပြောဦး",
    "ဘယ်လိုဖြစ်တာလဲ",
    "အဲ့ဒါနဲ့ပဲ",
    "မင်းကလဲကွာ",
    "တကယ်လား",
    "မယုံဘူး",
    "ယုံတယ်",
    "အတော်ပဲ",
    "ရယ်ရတယ်",
    "ဟာ",
    "ဟုတ်တော့ဟုတ်တယ်",
    "အင်းဟ",
    "ဘာပဲဖြစ်ဖြစ်",
    "မေးကြည့်ပါ",
    "ငါမသိ",
    "သိတယ်",
    "မသိချင်ဘူး",
    "ပြောလေကွာ",
    "စကားဝင်ပြောပါ",
    "မပျင်းနဲ့",
    "စကားပြောကြမယ်",
    "ငြိမ်နေကြတာပဲ",
    "ဘယ်သူမှမပြောဘူး",
    "အိပ်နေကြတာလား",
    "ငါတော့မအိပ်သေးဘူး",
    "ဒီမှာပါ",
    "ရှိပါတယ်ကွာ",
    "အခုရောက်တယ်",
    "နောက်ကျသွားပြီ",
    "သေချာလား",
    "ဟုတ်မဟုတ်မသိ",
    "အဲ့ဒါကြည့်",
    "ဘာတွေဖြစ်နေကြတာလဲ",
    "ငါလဲလိုက်မယ်",
    "ယူလိုက်ပါလား",
    "မယူဘူးလို့",
    "မယူရင်ထားလိုက်",
    "တော်ပြီ",
    "ပြီးပြီလေ",
]

# =========================
# SHORT - 50
# =========================

SHORT = [
    "အင်း",
    "ဟုတ်",
    "အေး",
    "ဟာ",
    "အို",
    "အဲ့",
    "ဘာ",
    "ဘယ်လို",
    "တကယ်",
    "ဟုတ်လား",
    "အေးပါ",
    "ရတယ်",
    "မရဘူး",
    "လာ",
    "ပြော",
    "ဆက်",
    "အခု",
    "နောက်မှ",
    "ဟုတ်တယ်",
    "မဟုတ်ဘူး",
    "အဲ့ဒါပဲ",
    "ဘာလဲ",
    "မသိဘူး",
    "အိုကေ",
    "ထား",
    "ဟုတ်ကဲ့",
    "အင်းဟ",
    "အေးဟ",
    "ဟုတ်ဟ",
    "ဘာဖြစ်",
    "ဘာလို့",
    "ဘယ်သူ",
    "ဘယ်မှာ",
    "ဘယ်တော့",
    "ပြောဦး",
    "လာဦး",
    "နေဦး",
    "ကြည့်",
    "မေး",
    "ရပြီ",
    "ပြီးပြီ",
    "မပြီးသေး",
    "ရှိတယ်",
    "မရှိဘူး",
    "သိတယ်",
    "မသိဘူး",
    "မှန်တယ်",
    "မမှန်ဘူး",
    "အေးဆေး",
    "တော်ပြီ",
]

# =========================
# GREETING - 50
# =========================

GREETING = [
    "လာပြီလား",
    "အခုမှလာတာလား",
    "လာပါ",
    "ကြိုဆိုပါတယ်",
    "အေး လာ",
    "ဘယ်ပျောက်နေတာလဲ",
    "အခုမှတွေ့တာ",
    "လာပြီဟ",
    "ဝင်လာပါ",
    "စကားဝင်ပြောပါ",
    "မပျင်းရအောင်စကားလေးဝင်ပြောနော်",
    "အချောလေးရေ စကားဝင်ပြော စေတနာရှိရင်လူလေးထည့်ပေးနော်",
    "ဟယ်လို",
    "ဟလို",
    "မင်္ဂလာပါ",
    "ဘယ်ကလာတာလဲ",
    "ရောက်လာပြီလား",
    "ဝင်လာပြီလား",
    "ဒီမှာလာပြီ",
    "အခုမှရောက်တာလား",
    "မတွေ့တာကြာပြီ",
    "ဘယ်တွေသွားနေတာလဲ",
    "လာပြီဆိုပြောလေ",
    "ဝင်လာပြီးငြိမ်မနေနဲ့",
    "စကားလေးပြောပါဦး",
    "ဒီမှာရှိတယ်",
    "လာလာ",
    "ဝင်ခဲ့",
    "ရောက်လာတာကောင်းတယ်",
    "အခုမှတွေ့တာပဲ",
    "လာရင်စကားပြောဦး",
    "မင်္ဂလာညပါ",
    "မင်္ဂလာနေ့ပါ",
    "မနက်ခင်းပါ",
    "ညနေခင်းပါ",
    "ညဘက်လာပြီလား",
    "မနက်ကတည်းကမတွေ့ဘူး",
    "ဘယ်လိုလဲ",
    "အဆင်ပြေလား",
    "နေကောင်းလား",
    "လာပါဦး",
    "ဝင်ပါဦး",
    "စကားဝင်ပါဦး",
    "အခုမှရောက်တာ",
    "လာပြီဆိုရင်ပြော",
    "မင်းလဲလာပြီပဲ",
    "အားလုံးလာပြီလား",
    "ဘယ်သူလာတာလဲ",
    "ရောက်နေပြီလား",
    "ဒီမှာပဲရှိတယ်",
]

# =========================
# QUESTION - 50
# =========================

QUESTION = [
    "ဘာမေးတာလဲ",
    "မသိဘူးဟ",
    "မေးကြည့်လေ",
    "အဲ့ဒါကိုမေးတာလား",
    "ဘယ်လိုသိမလဲ",
    "မင်းပဲသိမှာပါ",
    "အဖြေကတော့မသိဘူး",
    "စဉ်းစားနေတယ်",
    "ခဏနေပြောမယ်",
    "အဲ့ဒါကတော့ခက်တယ်",
    "မေးခွန်းကကြီးတယ်",
    "တကယ်မသိဘူး",
    "ဘယ်လိုလုပ်ရမလဲ",
    "မင်းကဘယ်လိုထင်လဲ",
    "ငါ့ကိုမေးတာလား",
    "ဘာကြောင့်လဲ",
    "ဘယ်သူသိမလဲ",
    "ဘယ်မှာလဲ",
    "ဘယ်တော့လဲ",
    "ဘာဖြစ်တာလဲ",
    "ဘာလိုချင်တာလဲ",
    "ဘာပြောတာလဲ",
    "ဘာကိုဆိုလိုတာလဲ",
    "အဲ့ဒါသေချာလား",
    "တကယ်မေးတာလား",
    "မေးလေ",
    "နောက်တစ်ခါပြောဦး",
    "နားမလည်ဘူး",
    "ပြန်မေးပါ",
    "ငါလဲမသိဘူး",
    "မေးရင်ဖြေမယ်",
    "အဲ့ဒါဘယ်လိုဖြစ်တာလဲ",
    "ဘယ်ကရတာလဲ",
    "ဘယ်သူလုပ်တာလဲ",
    "ဘယ်သူပြောတာလဲ",
    "ဘာလို့ဒီလိုဖြစ်တာလဲ",
    "ဘာကြောင့်ဒီလိုပြောတာလဲ",
    "အဖြေလိုချင်တာလား",
    "ငါ့ကိုမေးနေတာလား",
    "မင်းသိလား",
    "မင်းကရောသိလား",
    "အဲ့တာဟုတ်လား",
    "မဟုတ်ဘူးလား",
    "ဘာထင်လဲ",
    "ဘယ်လိုထင်လဲ",
    "အခုဘာလုပ်မလဲ",
    "နောက်ဘာဖြစ်မလဲ",
    "အဲ့ဒါနောက်ကဘာလဲ",
    "ဘာကိုရှာနေတာလဲ",
    "ဘာဖြစ်ချင်တာလဲ",
]

# =========================
# TEASE - 50
# =========================

TEASE = [
    "မင်းကလဲ",
    "သူခိုးကတော့သူခိုးပဲ",
    "တော်ပါတော့",
    "အရမ်းတတ်နေတယ်",
    "အဲ့လိုကြီးမလုပ်နဲ့",
    "ဘာတွေကြံနေတာလဲ",
    "သိနေတယ်နော်",
    "မလိမ်နဲ့",
    "မင်းကိုသိတယ်",
    "ဟုတ်ချင်ယောင်ဆောင်နေတာ",
    "အဲ့ဒါမယုံဘူး",
    "အရမ်းရမ်းနေတယ်",
    "ငြိမ်ငြိမ်နေ",
    "မင်းကတော့ဟာ",
    "တော်ပြီနော်",
    "အရမ်းတတ်တယ်",
    "မင်းပဲလေ",
    "မလိမ်နဲ့ကွာ",
    "သိပါတယ်",
    "မင်းလုပ်တာမဟုတ်လား",
    "မင်းပဲစတာ",
    "အခုမှရိုးသားပြနေတယ်",
    "အရမ်းအေးဆေးနေတာပဲ",
    "ဟန်ဆောင်မနေနဲ့",
    "ငါသိတယ်နော်",
    "မင်းကိုမယုံဘူး",
    "အဲ့လိုမပြောနဲ့",
    "ဘာတွေပြောနေတာလဲ",
    "ရမ်းနေပြန်ပြီ",
    "မင်းကတော်တော်လေး",
    "အရမ်းလည်တယ်",
    "လိမ္မာလိုက်တာ",
    "တော်တော်တတ်တယ်",
    "မင်းနဲ့တော့ခက်တယ်",
    "မင်းကိုတော့မနိုင်ဘူး",
    "ပြောလေ အမှန်ပြော",
    "မဖုံးနဲ့",
    "ဖော်ပြလိုက်",
    "သိနေတယ်လို့",
    "မင်းအကြောင်းသိတယ်",
    "အဲ့ဒါမျိုးမလုပ်နဲ့",
    "တော်တော့ကွာ",
    "မရမ်းနဲ့",
    "အေးအေးဆေးဆေးနေ",
    "ဘာတွေကြံနေတာလဲဟ",
    "မင်းကလဲအရမ်းပဲ",
    "ရယ်ရတယ်ကွာ",
    "မင်းကိုကြည့်ရတာ",
    "တော်ပြီဟ",
]

# =========================
# NOE - 50
# =========================

NOE = [
    "ဘာလဲ",
    "ခေါ်တာလား",
    "နိုးရှိတယ်",
    "ဘာပြောမလို့လဲ",
    "နိုးကိုခေါ်တာလား",
    "ပြောလေ",
    "ကြားတယ်",
    "ရှိတယ်ဟ",
    "ဘာလိုချင်တာလဲ",
    "လာပြီ",
    "နိုးဒီမှာပါ",
    "ဘာဖြစ်တာလဲ",
    "ဘာပြောမလို့လဲ",
    "နိုးနားထောင်နေတယ်",
    "ပြောကြည့်",
    "ခေါ်လိုက်တာလား",
    "နိုးရှိနေတယ်",
    "အင်း ဘာလဲ",
    "ပြောပါ",
    "နိုးကိုခေါ်ရင်လာတယ်",
    "ရှိပါတယ်",
    "နိုးကဒီမှာ",
    "ဘာလိုလဲ",
    "ဘာမေးမလို့လဲ",
    "မေးလေ",
    "ပြောလေကွာ",
    "နိုးကြားတယ်",
    "အခုရောက်ပြီ",
    "နိုးလာပြီ",
    "နိုးမအိပ်သေးဘူး",
    "နိုးဒီမှာရှိတယ်",
    "ခေါ်နေတာကြားတယ်",
    "ဘာဖြစ်လို့ခေါ်တာလဲ",
    "နိုးကိုပြောတာလား",
    "နိုးနားထောင်မယ်",
    "ဘာပြောမလို့လဲပြော",
    "ပြောပါဦး",
    "နိုးအဆင်သင့်ပဲ",
    "ဘာလုပ်ပေးရမလဲ",
    "နိုးကိုလိုတာလား",
    "လာခဲ့ပြီ",
    "နိုးပြန်လာပြီ",
    "ခေါ်တာနဲ့လာပြီ",
    "ဘာတွေဖြစ်နေတာလဲ",
    "နိုးမသိသေးဘူး",
    "နိုးလဲသိချင်တယ်",
    "ပြောရင်နားထောင်မယ်",
    "နိုးရှိနေပါတယ်",
    "အင်း နိုးပါ",
]

# =========================
# JSON
# =========================

def load_json(filename, default):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("SAVE ERROR:", e)


stickers = load_json(STICKER_FILE, [])
custom_replies = load_json(CUSTOM_FILE, {})

# =========================
# PICK REPLY
# =========================

def pick(items, chat_id):
    if not items:
        return "အင်း"

    old = last_reply_text.get(chat_id)

    choices = [x for x in items if x != old]

    if not choices:
        choices = items

    result = random.choice(choices)
    last_reply_text[chat_id] = result

    return result

# =========================
# MAKE REPLY
# =========================

def make_reply(text, chat_id):
    t = text.lower().strip()

    # Custom reply
    for key, value in custom_replies.items():
        if key.lower() in t:
            if isinstance(value, list) and value:
                return pick(value, chat_id)

            if isinstance(value, str):
                return value

    # Greeting
    greeting_words = [
        "ဟယ်လို",
        "ဟလို",
        "hello",
        "hi",
        "မင်္ဂလာပါ",
        "မနက်ခင်း",
        "ညနေခင်း",
    ]

    if any(word in t for word in greeting_words):
        return pick(GREETING, chat_id)

    # Noe
    if "နိုး" in t or "noe" in t:
        return pick(NOE, chat_id)

    # Question
    if (
        "?" in text
        or "လား" in t
        or "ဘာ" in t
        or "ဘယ်လို" in t
        or "ဘယ်မှာ" in t
        or "ဘယ်သူ" in t
    ):
        return pick(QUESTION, chat_id)

    # Tease
    tease_words = [
        "သူခိုး",
        "စပ့",
        "သေ",
        "ရမ်း",
        "အရူး",
        "ငတုံး",
        "မင်းက",
        "မလိမ်",
    ]

    if any(word in t for word in tease_words):
        return pick(TEASE, chat_id)

    # Short
    if len(text) <= 4:
        return pick(SHORT, chat_id)

    # Normal
    return pick(NORMAL, chat_id)

# =========================
# STICKER
# =========================

async def handle_sticker(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    global stickers

    message = update.effective_message

    if not message or not message.sticker:
        return

    if message.from_user and message.from_user.is_bot:
        return

    incoming = message.sticker.file_id
    chat_id = message.chat.id

    # သိမ်း
    if incoming not in stickers:
        stickers.append(incoming)

    if len(stickers) > STICKER_LIMIT:
        stickers = stickers[-STICKER_LIMIT:]

    save_json(STICKER_FILE, stickers)

    # မတူတဲ့ sticker ရွေး
    choices = [
        item
        for item in stickers
        if item != incoming
        and item != last_sticker.get(chat_id)
    ]

    # တခြား sticker မရှိသေးရင် incoming မဟုတ်တာရွေး
    if not choices:
        choices = [
            item
            for item in stickers
            if item != incoming
        ]

    if not choices:
        return

    sticker = random.choice(choices)
    last_sticker[chat_id] = sticker

    try:
        await message.reply_sticker(sticker)
    except Exception as e:
        print("STICKER ERROR:", e)

# =========================
# TEXT MESSAGE
# =========================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = update.effective_message

    if not message or not message.text:
        return

    user = update.effective_user

    if user and user.is_bot:
        return

    chat = update.effective_chat

    if not chat:
        return

    if chat.type not in ("group", "supergroup"):
        return

    text = message.text.strip()

    if not text:
        return

    if text.startswith("/"):
        return

    chat_id = chat.id
    user_id = user.id if user else 0
    now = time.time()

    # Cooldown
    if now - last_reply_time.get(chat_id, 0) < REPLY_COOLDOWN:
        return

    # တစ်ယောက်တည်းကို အမြဲမပြန်
    if last_user.get(chat_id) == user_id:
        if random.random() < 0.35:
            return

    # အမြဲမပြန်
    if random.random() > REPLY_CHANCE:
        return

    last_reply_time[chat_id] = now
    last_user[chat_id] = user_id

    # History
    history = chat_history.setdefault(chat_id, [])
    history.append(text)

    if len(history) > 20:
        del history[:-20]

    reply = make_reply(text, chat_id)

    try:
        await message.reply_text(reply)
    except Exception as e:
        print("REPLY ERROR:", e)

# =========================
# COMMANDS
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "နိုး Bot အလုပ်လုပ်နေပါပြီ။"
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "/start - Bot စမ်းရန်\n"
        "/help - Help\n"
        "/status - Status\n"
        "/listreply - Custom reply ကြည့်ရန်\n"
        "/setreply စာ - Reply ထည့်ရန်\n"
        "/delreply စာ - Reply ဖျက်ရန်"
    )


async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "NOE BOT\n"
        "Status: Online\n"
        f"Stored stickers: {len(stickers)}"
    )


async def list_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not custom_replies:
        await update.message.reply_text(
            "Custom reply မရှိသေးပါ။"
        )
        return

    lines = ["Custom replies:"]

    for key in list(custom_replies.keys())[:30]:
        lines.append("- " + key)

    await update.message.reply_text(
        "\n".join(lines)
    )


async def set_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not context.args:
        await update.message.reply_text(
            "အသုံးပြုပုံ:\n"
            "/setreply hello ဟယ်လို"
        )
        return

    key = context.args[0]

    if len(context.args) < 2:
        await update.message.reply_text(
            "ပြန်မယ့်စာ ထည့်ပါ။"
        )
        return

    value = " ".join(context.args[1:])

    custom_replies[key] = value
    save_json(CUSTOM_FILE, custom_replies)

    await update.message.reply_text(
        "Reply ထည့်ပြီးပါပြီ။"
    )


async def del_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not context.args:
        await update.message.reply_text(
            "ဖျက်မယ့် keyword ထည့်ပါ။"
        )
        return

    key = context.args[0]

    if key not in custom_replies:
        await update.message.reply_text(
            "အဲဒီ reply မရှိပါဘူး။"
        )
        return

    del custom_replies[key]
    save_json(CUSTOM_FILE, custom_replies)

    await update.message.reply_text(
        "Reply ဖျက်ပြီးပါပြီ။"
    )

# =========================
# ERROR
# =========================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):
    print("BOT ERROR:", context.error)

# =========================
# MAIN
# =========================

def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    app.add_handler(
        CommandHandler("status", status)
    )

    app.add_handler(
        CommandHandler("listreply", list_reply)
    )

    app.add_handler(
        CommandHandler("setreply", set_reply)
    )

    app.add_handler(
        CommandHandler("delreply", del_reply)
    )

    # Sticker
    app.add_handler(
        MessageHandler(
            filters.Sticker.ALL,
            handle_sticker
        )
    )

    # Text
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    app.add_error_handler(error_handler)

    print("NOE BOT STARTED")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
