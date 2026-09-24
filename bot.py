import os
import json
import random
import time
from collections import defaultdict, deque

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================================================
# CONFIG
# =========================================================

TOKEN = os.environ.get("BOT_TOKEN", "").strip()

OWNER_ID = 0

REPLIES_FILE = "replies.json"
GROUPS_FILE = "groups.json"
STICKERS_FILE = "stickers.json"

# Reply ပိုများအောင်
SPONTANEOUS_CHANCE = 0.75

# တစ် group ထဲ reply နှစ်ခါဆက်တိုက် မဖြစ်အောင်
REPLY_COOLDOWN = 0.8

# History
HISTORY_SIZE = 20


# =========================================================
# TOKEN CHECK
# =========================================================

if not TOKEN:
    print("================================")
    print("ERROR: BOT_TOKEN IS MISSING")
    print("Please add BOT_TOKEN in Environment Variables")
    print("================================")
    raise SystemExit(1)


# =========================================================
# JSON FUNCTIONS
# =========================================================

def load_json(filename, default):
    try:
        if not os.path.exists(filename):
            return default

        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    except Exception as e:
        print("LOAD ERROR:", filename, e)
        return default


def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:
        print("SAVE ERROR:", filename, e)


# =========================================================
# DATA
# =========================================================

replies = load_json(
    REPLIES_FILE,
    {}
)

groups = load_json(
    GROUPS_FILE,
    {}
)

stickers = load_json(
    STICKERS_FILE,
    []
)

if not isinstance(replies, dict):
    replies = {}

if not isinstance(groups, dict):
    groups = {}

if not isinstance(stickers, list):
    stickers = []


# =========================================================
# MEMORY
# =========================================================

CHAT_HISTORY = defaultdict(
    lambda: deque(
        maxlen=HISTORY_SIZE
    )
)

LAST_REPLY = {}

LAST_USER = {}

LAST_STICKER = {}

LAST_REPLY_TIME = {}


# =========================================================
# NORMAL REPLIES
# =========================================================

NORMAL_REPLIES = [

    "အင်း",
    "ဟုတ်",
    "အေး",
    "ဟုတ်တယ်",
    "ဟုတ်ပါ့",
    "ရတယ်",
    "အိုကေ",
    "သိပြီ",
    "ကြားတယ်",
    "ပြောလေ",
    "ဆက်ပြော",
    "ဘာဖြစ်တာလဲ",
    "ဘာလုပ်နေတာလဲ",
    "အဲ့လိုလား",
    "အင်းပါ",
    "အေးဆေး",
    "ရပါတယ်",
    "မသိဘူး",
    "မသိသေးဘူး",
    "ဟာ",
    "ဟေ့",
    "အမယ်",
    "ဟုတ်လား",
    "ဘာပြောတာ",
    "ဘာလဲ",
    "ဘယ်လိုဖြစ်တာလဲ",
    "အဲ့တာတော့မသိ",
    "မင်းကလဲ",
    "တော်တော့",
    "အင်းနော်",
    "အေးပါကွာ",
    "ကောင်းပြီ",
    "ရပြီ",
    "ရပြီလေ",
    "လာပြီ",
    "လာပြီလေ",
    "နားထောင်နေတယ်",
    "စကားဝင်ပြောလေ",
    "ပြောပါဦး",
    "ဘာဖြစ်ကြတာလဲ",
    "ငြိမ်နေပါဦး",
    "မပျင်းနဲ့",
    "အဲ့တာဘာလဲ",
    "ဘယ်သူလဲ",
    "ဘယ်ကလာတာလဲ",
    "အဲ့လိုကြီးလား",
    "အေးကွာ",
    "အင်းကွာ",
    "ဟုတ်ကဲ့",
    "ဟုတ်ပါတယ်",
    "အိုကေပါ",
    "ရပါတယ်ကွာ",
    "မင်းပြောတာကြားတယ်",
    "အေး နားလည်တယ်",
    "သိပါတယ်",
    "သိပြီလို့",
    "ပြောနေတာပဲ",
    "ဘာဖြစ်လို့လဲ",
    "အခုမှလား",
    "အရင်ကတည်းကလေ",
    "အဲ့တာပဲ",
    "အဲ့လိုပဲ",
    "ဟုတ်မဟုတ်တော့မသိ",
    "မေးကြည့်လေ",
    "ပြောကြည့်",
    "လုပ်ကြည့်လေ",
    "စောင့်ဦး",
    "ခဏလေး",
    "အေးအေး",
    "မမြန်နဲ့",
    "ဘာမှမဖြစ်ဘူး",
    "ရပါတယ် မပူနဲ့",
    "အေးဆေးလုပ်",
    "အဆင်ပြေတယ်",
    "အဆင်ပြေပါတယ်",
    "ကောင်းတယ်",
    "မဆိုးဘူး",
    "အဲ့တာကောင်းတယ်",
    "ဟုတ်သားပဲ",
    "အဲ့တာတော့ဟုတ်တယ်",
    "မဟုတ်လောက်ဘူး",
    "မဟုတ်ဘူးထင်တယ်",
    "ထင်တာပဲ",
    "မသေချာဘူး",
    "နောက်မှပြော",
    "အခုမပြောသေးဘူး",
    "နားမလည်ဘူး",
    "ရှင်းပြလေ",
    "ထပ်ပြော",
    "တစ်ခါထပ်ပြော",
    "ကြားမိတယ်",
    "မြင်တယ်",
    "တွေ့တယ်",
    "အဲ့တာနဲ့လား",
    "ဘာဆိုင်လို့လဲ",
    "ဘာတွေဖြစ်နေတာလဲ",
    "အေးဟုတ်တယ်",
    "ဟုတ်တာပေါ့",
    "အင်းဟုတ်",
    "အဲ့လိုပဲနော်",
    "ကဲ ပြော",
]


# =========================================================
# SHORT REPLIES
# =========================================================

SHORT_REPLIES = [

    "ဟာ",
    "အင်း",
    "အေး",
    "ဟုတ်",
    "ရပြီ",
    "လာ",
    "ပြော",
    "ဘာ",
    "အယ်",
    "ဟေ့",
    "ဟုတ်လား",
    "အင်းလေ",
    "အေးလေ",
    "ကဲ",
    "အို",
    "ဟာကွာ",
    "အမယ်",
    "အဲ့",
    "ဘာလဲ",
    "သေပြီ",
    "မဟုတ်",
    "ဟုတ်တယ်",
    "အေးပါ",
    "ရတယ်",
    "ရပြီလေ",
    "လာပြီ",
    "စီ",
    "A",
    "B",
    "C",
    "D",
    "Z",
    "နယူး",
    "ဆွေ",
    "နိုး",
    "ဟမ်",
    "အယ်လေ",
    "ဟာဟ",
    "အင်းဟ",
    "အေးဟ",
    "ပြောလေ",
    "ဆက်",
    "ဘာဖြစ်",
    "ဘယ်လို",
    "အဲ့လို",
    "မသိ",
    "သိပြီ",
    "ကောင်း",
    "အိုကေ",
]


# =========================================================
# TEASE REPLIES
# =========================================================

TEASE_REPLIES = [

    "စတာ",
    "နောက်တာ",
    "မရမ်းနဲ့",
    "ရမ်းနေပြန်ပြီ",
    "ဟာ မင်းကလဲ",
    "တော်တော့",
    "အေးပါ မင်းကလဲ",
    "ဘာတွေပြောနေတာလဲ",
    "မင်းတော်တော်ရမ်းတာပဲ",
    "စကားကတော့မနည်းဘူး",
    "လာပြန်ပြီ",
    "အဲ့တာဘာလုပ်တာလဲ",
    "မလုပ်နဲ့လေ",
    "ရမ်းမနေနဲ့",
    "အဲ့လိုမပြောနဲ့",
    "ဟာကွာ",
    "မင်းကိုပြောနေတာ",
    "မင်းကစတာနော်",
    "စပြီးရမ်းနေပြီ",
    "အခုမှစတာလား",
    "ငါသိတယ်",
    "မင်းနောက်တာသိတယ်",
    "အဲ့လိုလား",
    "အမယ် မင်းက",
    "အေးဆေးပါ",
    "မရမ်းနဲ့လို့",
    "မင်းပဲစတာ",
    "မင်းပဲအရင်ပြောတာ",
    "ငါဘာမှမလုပ်ဘူး",
    "ငါကကြည့်နေတာ",
    "ဘာတွေဖြစ်နေကြတာလဲ",
    "အဲ့တာတော့ရယ်ရတယ်",
    "တော်တော်စတာပဲ",
    "မင်းလဲမနည်းဘူး",
    "အဲ့လိုကြီးတော့မလုပ်နဲ့",
    "နောက်တာလား",
    "စတာမဟုတ်လား",
    "သိသာတယ်",
    "ငါမယုံဘူး",
    "အဲ့တာတော့မရဘူး",
    "မင်းကတော့",
    "ဟာ မင်းကလဲကွာ",
    "မနေနိုင်ဘူးလား",
    "ငြိမ်ငြိမ်နေ",
    "ဘာလို့ရမ်းတာလဲ",
    "အေးပါကွာ",
    "တော်ပြီ",
    "မပြောတော့ဘူး",
    "ငါတော့ရယ်နေပြီ",
    "အဲ့လိုပဲလုပ်နေ",
]


# =========================================================
# QUESTION REPLIES
# =========================================================

QUESTION_REPLIES = [

    "ဘာလဲ",
    "ဘာဖြစ်တာလဲ",
    "ဘာလို့လဲ",
    "ဘယ်လိုလဲ",
    "ဘယ်မှာလဲ",
    "ဘယ်သူလဲ",
    "မသိဘူး",
    "မသိသေးဘူး",
    "မေးကြည့်လေ",
    "ပြောကြည့်",
    "ရှင်းပြလေ",
    "အဲ့တာဘာလဲ",
    "ဟုတ်လား",
    "တကယ်လား",
    "သေချာလား",
    "ဘယ်လိုဖြစ်တာလဲ",
    "ဘာကြောင့်လဲ",
    "ဘာလုပ်မှာလဲ",
    "ဘယ်ကိုသွားမှာလဲ",
    "ဘယ်သူပြောတာလဲ",
    "ဘယ်ကသိတာလဲ",
    "အဲ့တာဘယ်လိုလုပ်တာလဲ",
    "မသိဘူးနော်",
    "ငါလဲမသိဘူး",
    "သိရင်ပြောမယ်",
    "နောက်မှသိမယ်",
    "မေးကြည့်ပါ",
    "ဘာကိုမေးတာလဲ",
    "မေးတာနားမလည်ဘူး",
    "ထပ်မေး",
    "နည်းနည်းရှင်းပြ",
    "အဲ့လိုလား",
    "အင်း ဟုတ်လား",
    "အဲ့တာသေချာလား",
    "ဘယ်တုန်းကလဲ",
    "ဘယ်သူနဲ့လဲ",
    "ဘာတွေဖြစ်နေတာလဲ",
    "ဘာကြီးလဲ",
    "အခုလား",
    "ဘယ်အချိန်လဲ",
]


# =========================================================
# COMMAND REPLIES
# =========================================================

COMMAND_REPLIES = [

    "လာပြီ",
    "ရပြီ",
    "အိုကေ",
    "လုပ်မယ်",
    "ခဏ",
    "စောင့်ဦး",
    "ပြောလေ",
    "ဘာ command လဲ",
    "သိပြီ",
    "ရတယ်",
    "အဆင်ပြေတယ်",
    "လုပ်ကြည့်",
    "ထပ်လုပ်",
    "မရသေးဘူး",
    "ရပြီလေ",
    "လာပြီလို့",
    "အေး",
    "ဟုတ်",
    "အဲ့တာလုပ်မယ်",
    "နောက်မှလုပ်",
    "ခဏစောင့်",
    "ကဲလုပ်",
    "ရတယ် လုပ်",
    "အိုကေ လာ",
    "သိပြီနော်",
    "ရပြီ",
    "လုပ်ကြည့်လေ",
    "စမ်းကြည့်",
    "မေးလေ",
    "ပြောလေ",
]


# =========================================================
# GREETING
# =========================================================

GREETING_REPLIES = [

    "ဟယ်လို",
    "ဟလို",
    "အင်း ဘာလဲ",
    "လာပြီ",
    "ပြောလေ",
    "ဟုတ် မင်္ဂလာပါ",
    "ဟလို ဘာဖြစ်",
    "အင်း ကြားတယ်",
    "ဟုတ် ဘာပြောမလို့လဲ",
    "လာပြီနော်",
    "ပြောပါ",
    "ဘာလုပ်နေကြတာလဲ",
    "အေး ဟလို",
    "ဟုတ်တယ် ပြော",
    "အင်း လာ",
]


# =========================================================
# TAKE REPLIES
# =========================================================

TAKE_REPLIES = [

    "ယူလိုက်ပါလား",
    "ယူမလား",
    "ယူလိုက်",
    "ယူပါ",
    "ယူလေ",
    "မယူဘူးလား",
    "ယူလိုက်တော့",
    "ယူကြည့်",
    "အဲ့တာယူ",
    "မယူနဲ့လား",
    "ယူမှာလား",
    "ဘယ်သူယူမလဲ",
    "ငါတော့မယူဘူး",
    "ယူလိုက်ပါ",
    "သွားယူလေ",
]


# =========================================================
# NOE REPLIES
# =========================================================

NOE_REPLIES = [

    "ဘာလဲ",
    "ခေါ်တာလား",
    "အင်း ငါရှိတယ်",
    "ဘာပြောမလို့လဲ",
    "လာပြီ",
    "ဟုတ် ပြော",
    "ဘာဖြစ်တာလဲ",
    "ငါ့ကိုခေါ်တာလား",
    "အင်း ကြားတယ်",
    "ပြောလေ",
    "ဘာလုပ်ရမလဲ",
    "အေး ငါရှိတယ်",
    "ခေါ်ရင်လာတယ်",
    "အင်း နိုးရှိတယ်",
    "ဘာကိစ္စလဲ",
]


# =========================================================
# SELECT REPLY
# =========================================================

def choose_reply(items, chat_id):

    if not items:
        return None

    previous = LAST_REPLY.get(chat_id)

    choices = [
        item
        for item in items
        if item != previous
    ]

    if not choices:
        choices = items

    selected = random.choice(choices)

    LAST_REPLY[chat_id] = selected

    return selected


# =========================================================
# CUSTOM REPLY
# =========================================================

def custom_response(text, chat_id):

    if not replies:
        return None

    lower = text.lower().strip()

    for key, value in replies.items():

        if key.lower() in lower:

            if isinstance(value, list):
                return choose_reply(
                    value,
                    chat_id
                )

            if isinstance(value, str):
                return value

    return None


# =========================================================
# MAKE RESPONSE
# =========================================================

def make_response(text, chat_id):

    lower = text.lower().strip()

    # Custom
    result = custom_response(
        text,
        chat_id
    )

    if result:
        return result

    # Greeting
    if any(
        x in lower
        for x in [
            "ဟယ်လို",
            "ဟလို",
            "မင်္ဂလာပါ",
            "hello",
            "hi",
        ]
    ):
        return choose_reply(
            GREETING_REPLIES,
            chat_id
        )

    # Noe
    if (
        "နိုး" in lower
        or "noe" in lower
    ):
        return choose_reply(
            NOE_REPLIES,
            chat_id
        )

    # Take
    if any(
        x in lower
        for x in [
            "ယူလိုက်ပါလား",
            "ယူမလား",
            "ယူလိုက်",
            "ယူပါ",
            "ယူလေ",
        ]
    ):
        return choose_reply(
            TAKE_REPLIES,
            chat_id
        )

    # Question
    if any(
        x in lower
        for x in [
            "ဘာလဲ",
            "ဘာလို့",
            "ဘယ်လို",
            "ဘယ်မှာ",
            "ဘယ်သူ",
            "ဘာလုပ်",
            "ဘာဖြစ်",
            "?",
            "လား",
        ]
    ):
        return choose_reply(
            QUESTION_REPLIES,
            chat_id
        )

    # Tease
    if any(
        x in lower
        for x in [
            "ရမ်း",
            "စတာ",
            "စ",
            "ဟာ",
            "ဟေ့",
            "အမယ်",
            "နောက်တာ",
        ]
    ):
        return choose_reply(
            TEASE_REPLIES,
            chat_id
        )

    # Short
    if len(text) <= 2:
        return choose_reply(
            SHORT_REPLIES,
            chat_id
        )

    # Normal random
    if random.random() <= SPONTANEOUS_CHANCE:
        return choose_reply(
            NORMAL_REPLIES,
            chat_id
        )

    return None


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    await update.message.reply_text(
        "နိုး အလုပ်လုပ်နေပါပြီ။"
    )


# =========================================================
# HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    await update.message.reply_text(
        "/start\n"
        "/help\n"
        "/status\n"
        "/register\n"
        "/groups\n"
        "/listreply\n"
        "/setreply စာ - ပြန်စာ\n"
        "/delreply စာ\n"
        "/clearreply\n"
        "/send စာ"
    )


# =========================================================
# STATUS
# =========================================================

async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    await update.message.reply_text(

        "NOE BOT STATUS\n\n"

        f"Groups: {len(groups)}\n"

        f"Custom replies: {len(replies)}\n"

        f"Stickers: {len(stickers)}\n"

        "Auto Reply: ON\n"

        "Sticker Reply: ON\n"

        "Emoji: OFF"
    )


# =========================================================
# REGISTER GROUP
# =========================================================

async def register(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    chat = update.effective_chat

    if chat.type not in [
        "group",
        "supergroup"
    ]:
        await update.message.reply_text(
            "Group ထဲမှာသုံးပါ။"
        )
        return

    groups[str(chat.id)] = {

        "title":
            chat.title or "",

        "username":
            chat.username or "",
    }

    save_json(
        GROUPS_FILE,
        groups
    )

    await update.message.reply_text(
        "ဒီ group ကို register လုပ်ပြီးပါပြီ။"
    )


# =========================================================
# GROUPS
# =========================================================

async def groups_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not groups:
        await update.message.reply_text(
            "Register လုပ်ထားတဲ့ group မရှိသေးပါ။"
        )
        return

    lines = [
        "REGISTERED GROUPS"
    ]

    for gid, data in groups.items():

        title = data.get(
            "title",
            ""
        )

        username = data.get(
            "username",
            ""
        )

        if username:

            lines.append(
                f"{title} @{username}\n{gid}"
            )

        else:

            lines.append(
                f"{title}\n{gid}"
            )

    await update.message.reply_text(
        "\n\n".join(lines)
    )


# =========================================================
# LIST REPLY
# =========================================================

async def list_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not replies:

        await update.message.reply_text(
            "Custom reply မရှိသေးပါ။"
        )

        return

    lines = [
        "CUSTOM REPLIES"
    ]

    for key, value in replies.items():

        if isinstance(value, list):

            value = " / ".join(
                value[:5]
            )

        lines.append(
            f"{key} -> {value}"
        )

    await update.message.reply_text(
        "\n".join(lines)
    )


# =========================================================
# SET REPLY
# =========================================================

async def set_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = update.message.text or ""

    parts = text.split(
        " ",
        2
    )

    if len(parts) < 3:

        await update.message.reply_text(
            "/setreply စာ ပြန်စာ"
        )

        return

    key = parts[1].strip()

    value = parts[2].strip()

    if not key or not value:

        await update.message.reply_text(
            "စာနဲ့ ပြန်စာ နှစ်ခုလုံးထည့်ပါ။"
        )

        return

    replies[key] = value

    save_json(
        REPLIES_FILE,
        replies
    )

    await update.message.reply_text(
        "Reply ထည့်ပြီးပါပြီ။"
    )


# =========================================================
# DELETE REPLY
# =========================================================

async def del_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not context.args:

        await update.message.reply_text(
            "/delreply စာ"
        )

        return

    key = " ".join(
        context.args
    )

    if key not in replies:

        await update.message.reply_text(
            "အဲ့ဒီ reply မရှိပါ။"
        )

        return

    del replies[key]

    save_json(
        REPLIES_FILE,
        replies
    )

    await update.message.reply_text(
        "ဖျက်ပြီးပါပြီ။"
    )


# =========================================================
# CLEAR REPLIES
# =========================================================

async def clear_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    replies.clear()

    save_json(
        REPLIES_FILE,
        replies
    )

    await update.message.reply_text(
        "Custom replies အားလုံးဖျက်ပြီးပါပြီ။"
    )


# =========================================================
# SEND
# =========================================================

async def send_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if OWNER_ID != 0:

        user = update.effective_user

        if not user or user.id != OWNER_ID:

            await update.message.reply_text(
                "Owner ပဲသုံးလို့ရပါတယ်။"
            )

            return

    if not context.args:

        await update.message.reply_text(
            "/send စာ"
        )

        return

    text = " ".join(
        context.args
    )

    count = 0

    for gid in list(groups.keys()):

        try:

            await context.bot.send_message(
                chat_id=int(gid),
                text=text
            )

            count += 1

        except Exception as e:

            print(
                "SEND ERROR:",
                e
            )

    await update.message.reply_text(
        f"ပို့ပြီးပါပြီ။ Groups: {count}"
    )


# =========================================================
# STICKER REPLY
# =========================================================

async def sticker_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        message = update.message

        if not message:
            return

        if message.chat.type not in [
            "group",
            "supergroup"
        ]:
            return

        if not message.sticker:
            return

        incoming = (
            message.sticker.file_id
        )

        # သိမ်း
        if incoming not in stickers:

            stickers.append(
                incoming
            )

            # အများဆုံး 150
            if len(stickers) > 150:

                del stickers[:-150]

            save_json(
                STICKERS_FILE,
                stickers
            )

        # မတူတဲ့ sticker ရွေး
        choices = [

            item

            for item in stickers

            if item != incoming

            and item != LAST_STICKER.get(
                message.chat.id
    )
