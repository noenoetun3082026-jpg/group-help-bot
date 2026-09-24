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
    ChatMemberHandler,
    ContextTypes,
    filters,
)

# =========================
# NOE BOT
# =========================

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0"))

REPLIES_FILE = "replies.json"
GROUPS_FILE = "groups.json"
STICKERS_FILE = "stickers.json"

# =========================
# SETTINGS
# =========================

REPLY_COOLDOWN = 1.2
SPONTANEOUS_CHANCE = 0.30

# =========================
# JSON FUNCTIONS
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
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )
    except Exception as e:
        print("SAVE ERROR:", repr(e))


replies = load_json(REPLIES_FILE, {})
groups = load_json(GROUPS_FILE, {})
stickers = load_json(STICKERS_FILE, [])

# =========================
# MEMORY
# =========================

CHAT_HISTORY = defaultdict(
    lambda: deque(maxlen=12)
)

LAST_REPLY = {}
LAST_STICKER = {}

# =========================
# NOE REPLY STYLE
# =========================

SHORT_REPLIES = [
    "အင်း",
    "ဘာလဲ",
    "ပြောလေ",
    "လာပြီလေ",
    "ဟုတ်",
    "အေး",
    "ဆက်ပြော",
    "ငါလည်းရှိတယ်",
    "ဘာတွေပြောနေတာလဲ",
    "မပျင်းအောင်ပြောလေ",
    "ဒီမှာရှိတယ်",
]

NORMAL_REPLIES = [
    "အင်း နားထောင်နေတယ်",
    "ပြောလေ",
    "ဘာဖြစ်တာလဲ",
    "အေးပါ",
    "မပျင်းအောင် စကားလေးပြောကြ",
    "ငါလည်း ဝင်ပြောမယ်",
    "ဘာတွေဖြစ်နေကြတာလဲ",
    "ဆက်ပြောကြ",
    "ငြိမ်မနေနဲ့",
    "ဒီမှာရှိတယ်",
    "ပြောနေကြတာ နားထောင်နေတာ",
]

TEASE_REPLIES = [
    "ရမ်းနေပြန်ပြီ",
    "မင်းကလည်း",
    "အေးပါကွာ",
    "ဟာ မင်းနဲ့တော့",
    "တော်တော့",
    "ဘာလို့အဲ့လောက်ရမ်းနေတာလဲ",
    "ငါ့ကိုလာမစနဲ့",
]

QUESTION_REPLIES = [
    "ဘာလဲ",
    "ပြောလေ",
    "ဘာမေးတာလဲ",
    "အင်း ပြော",
    "နားထောင်နေတယ်",
]

COMMAND_REPLIES = [
    "ရပြီ",
    "လာပြီလေ",
    "အင်း",
    "ဘာလိုချင်တာလဲ",
    "ဆက်လုပ်လေ",
]

# =========================
# RANDOM CHOICE
# =========================

def choose_reply(items, chat_id):
    if not items:
        return None

    old = LAST_REPLY.get(chat_id)

    choices = [
        item for item in items
        if item != old
    ]

    if not choices:
        choices = items

    result = random.choice(choices)

    LAST_REPLY[chat_id] = result

    return result


# =========================
# MAKE NOE RESPONSE
# =========================

def make_response(text, chat_id):
    text = text.strip()
    lowered = text.lower()

    # Question
    if any(word in lowered for word in [
        "ဘာလဲ",
        "ဘယ်လို",
        "ဘယ်မှာ",
        "ဘယ်သူ",
        "ဘာလုပ်",
    ]):
        return choose_reply(
            QUESTION_REPLIES,
            chat_id
        )

    # Greeting
    if any(word in lowered for word in [
        "ဟယ်လို",
        "ဟလို",
        "မင်္ဂလာပါ",
        "hello",
        "hi",
    ]):
        return choose_reply(
            [
                "ဟယ်လို",
                "လာပြီလေ",
                "အင်း ဘာပြောမလို့လဲ",
                "ပြောလေ",
            ],
            chat_id
        )

    # Noe
    if any(word in lowered for word in [
        "နိုး",
        "noe",
    ]):
        return choose_reply(
            [
                "ဘာလဲ",
                "ခေါ်တာလား",
                "အင်း",
                "ပြောလေ",
            ],
            chat_id
        )

    # New
    if "နယူး" in lowered:
        return choose_reply(
            [
                "မပျင်းအောင် စကားလေးဝင်ပြောနော်",
                "စကားဝင်ပြောလေ",
                "ဒီမှာရှိတယ်",
            ],
            chat_id
        )

    # Take / give
    if any(word in lowered for word in [
        "ယူလိုက်ပါလား",
        "ယူမလား",
        "ယူလိုက်",
    ]):
        return choose_reply(
            [
                "မယူဘူးလို့",
                "မယူဘူး",
                "မလိုဘူး",
                "ထားလိုက်ပါ",
            ],
            chat_id
        )

    # Short messages
    if len(text) <= 2:
        return choose_reply(
            SHORT_REPLIES,
            chat_id
        )

    # Dot commands
    if text.startswith("."):
        return choose_reply(
            COMMAND_REPLIES,
            chat_id
        )

    # Teasing
    if any(word in lowered for word in [
        "ရမ်း",
        "စတာ",
        "စ",
        "ဟာ",
        "ဟေ့",
        "အမယ်",
    ]):
        if random.random() < 0.75:
            return choose_reply(
                TEASE_REPLIES,
                chat_id
            )

    # Normal conversation
    if random.random() < SPONTANEOUS_CHANCE:
        return choose_reply(
            NORMAL_REPLIES,
            chat_id
        )

    return None


# =========================
# OWNER
# =========================

def is_owner(update):
    user = update.effective_user

    return bool(
        user and
        user.id == OWNER_ID
    )


# =========================
# ADMIN
# =========================

async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user:
        return False

    if chat.type == "private":
        return True

    try:
        member = await context.bot.get_chat_member(
            chat.id,
            user.id
        )

        return member.status in (
            "administrator",
            "creator"
        )

    except Exception:
        return False


# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "နိုး အလုပ်လုပ်နေပါပြီ။"
    )


# =========================
# HELP
# =========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "/start - Bot စတင်ရန်\n"
        "/help - အကူအညီ\n"
        "/status - အခြေအနေ\n"
        "/register - Group မှတ်ရန်\n"
        "/groups - Group စာရင်း\n"
        "/listreply - Reply စာရင်း\n"
        "/setreply - Reply ထည့်ရန်\n"
        "/delreply - Reply ဖျက်ရန်\n"
        "/clearreply - Reply အားလုံးဖျက်ရန်\n"
        "/send - Group များသို့ပို့ရန်"
    )


# =========================
# STATUS
# =========================

async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "Noe Status\n"
        f"Groups: {len(groups)}\n"
        f"Stickers: {len(stickers)}\n"
        "Auto Reply: ON\n"
        "Sticker Reply: ON"
    )


# =========================
# REGISTER GROUP
# =========================

async def register_group(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    chat = update.effective_chat

    if not chat:
        return

    if not await is_admin(
        update,
        context
    ):
        return

    groups[str(chat.id)] = {
        "id": chat.id,
        "title": chat.title or "",
        "username": chat.username or "",
    }

    save_json(
        GROUPS_FILE,
        groups
    )

    await update.message.reply_text(
        "ဒီ Group ကို မှတ်ထားလိုက်ပြီ။"
    )


# =========================
# GROUPS
# =========================

async def groups_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not groups:
        await update.message.reply_text(
            "Group မရှိသေးဘူး။"
        )
        return

    lines = ["Groups:"]

    for data in groups.values():

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
                f"{title} @{username}"
            )
        else:
            lines.append(title)

    await update.message.reply_text(
        "\n".join(lines)
    )


# =========================
# LIST REPLY
# =========================

async def list_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not replies:
        await update.message.reply_text(
            "Reply မရှိသေးဘူး။"
        )
        return

    lines = ["Reply List:"]

    for key, value in replies.items():
        lines.append(
            f"{key} -> {value}"
        )

    await update.message.reply_text(
        "\n".join(lines)
    )


# =========================
# SET REPLY
# =========================

async def set_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await is_admin(
        update,
        context
    ):
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "/setreply keyword | reply"
        )
        return

    keyword = context.args[0]

    response = " ".join(
        context.args[1:]
    )

    replies[keyword] = response

    save_json(
        REPLIES_FILE,
        replies
    )

    await update.message.reply_text(
        "Reply ထည့်ပြီးပြီ။"
    )


# =========================
# DELETE REPLY
# =========================

async def del_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await is_admin(
        update,
        context
    ):
        return

    if not context.args:
        return

    key = context.args[0]

    if key in replies:

        del replies[key]

        save_json(
            REPLIES_FILE,
            replies
        )

        await update.message.reply_text(
            "ဖျက်ပြီးပြီ။"
        )


# =========================
# CLEAR REPLIES
# =========================

async def clear_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await is_admin(
        update,
        context
    ):
        return

    replies.clear()

    save_json(
        REPLIES_FILE,
        replies
    )

    await update.message.reply_text(
        "Reply အားလုံးဖျက်ပြီးပြီ။"
    )


# =========================
# GROUP TRACKING
# =========================

async def track_group(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    chat = update.effective_chat

    if not chat:
        return

    member = update.my_chat_member

    if not member:
        return

    status = member.new_chat_member.status

    if status in (
        "member",
        "administrator"
    ):

        groups[str(chat.id)] = {
            "id": chat.id,
            "title": chat.title or "",
            "username": chat.username or "",
        }

        save_json(
            GROUPS_FILE,
            groups
        )

        print(
            "GROUP ADDED:",
            chat.id,
            chat.title
        )

    elif status in (
        "left",
        "kicked"
    ):

        groups.pop(
            str(chat.id),
            None
        )

        save_json(
            GROUPS_FILE,
            groups
        )

        print(
            "GROUP REMOVED:",
            chat.id
        )


# =========================
# WELCOME
# =========================

async def welcome(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = update.effective_message

    if not message:
        return

    user = update.effective_user

    if user:
        await message.reply_text(
            f"{user.first_name} လာပြီလား။"
        )


# =========================
# GOODBYE
# =========================

async def goodbye(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = update.effective_message

    if not message:
        return

    user = update.effective_user

    if user:
        await message.reply_text(
            f"{user.first_name} ပြန်သွားပြီ။"
        )


# =========================
# STICKER REPLY
# =========================

async def check_sticker(
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

    if chat.type not in (
        "group",
        "supergroup"
    ):
        return

    if not message.sticker:
        return

    incoming = message.sticker.file_id

    # Sticker ကိုသိမ်း
    if incoming not in stickers:

        stickers.append(incoming)

        if len(stickers) > 100:
            del stickers[:-100]

        save_json(
            STICKERS_FILE,
            stickers
        )

    # လက်ရှိ Sticker နဲ့မတူတာရွေး
    choices = [
        item
        for item in stickers
        if item != incoming
        and item != LAST_STICKER.get(chat.id)
    ]

    # တခြား sticker မရှိသေးရင် မပြန်
    if not choices:
        return

    selected = random.choice(
        choices
    )

    LAST_STICKER[chat.id] = selected

    try:

        await message.reply_sticker(
            sticker=selected
        )

        print(
            "NOE STICKER REPLY:",
            chat.id
        )

    except Exception as e:

        print(
            "STICKER ERROR:",
            repr(e)
        )


# =========================
# TEXT REPLY
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

    if user.is_bot:
        return

    if chat.type not in (
        "group",
        "supergroup"
    ):
        return

    text = message.text or ""

    if not text.strip():
        return

    # Slash commands မပြန်
    if text.startswith("/"):
        return

    # Chat history သိမ်း
    CHAT_HISTORY[chat.id].append({
        "user": user.first_name or "",
        "text": text,
    })

    # Cooldown
    now = time.monotonic()

    last = LAST_REPLY.get(
        chat.id,
        0
    )

    if now - last < REPLY_COOLDOWN:
        return

    response = make_response(
        text,
        chat.id
    )

    if not response:
        return

    try:

        await message.reply_text(
            response
        )

        LAST_REPLY[chat.id] = now

        print(
            "NOE REPLY:",
            user.first_name,
            "->",
            text,
            "=>",
            response
        )

    except Exception as e:

        print(
            "REPLY ERROR:",
            repr(e)
        )


# =========================
# SEND / BROADCAST
# =========================

async def send_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not is_owner(update):
        return

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "ပို့ချင်တဲ့ message ကို reply လုပ်ပြီး /send သုံးပါ။"
        )

        return

    success = 0

    for data in groups.values():

        chat_id = data.get("id")

        try:

            await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=update.effective_chat.id,
                message_id=(
                    update.message
                    .reply_to_message
                    .message_id
                ),
            )

            success += 1

        except Exception as e:

            print(
                "SEND ERROR:",
                chat_id,
                repr(e)
            )

    await update.message.reply_text(
        f"ပို့ပြီးပြီ။ {success} groups"
    )


# =========================
# MAIN
# =========================

def main():

    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN မတွေ့ပါ။"
        )

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    # Commands
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    app.add_handler(
        CommandHandler(
            "status",
            status_command
        )
    )

    app.add_handler(
        CommandHandler(
            "register",
            register_group
        )
    )

    app.add_handler(
        CommandHandler(
            "groups",
            groups_command
        )
    )

    app.add_handler(
        CommandHandler(
            "listreply",
            list_reply
        )
    )

    app.add_handler(
        CommandHandler(
            "setreply",
            set_reply
        )
    )

    app.add_handler(
        CommandHandler(
            "delreply",
            del_reply
        )
    )

    app.add_handler(
        CommandHandler(
            "clearreply",
            clear_reply
        )
    )

    app.add_handler(
        CommandHandler(
            "send",
            send_command
        )
    )

    # Group tracking
    app.add_handler(
        ChatMemberHandler(
            track_group,
            ChatMemberHandler.MY_CHAT_MEMBER
        )
    )

    # Welcome
    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome
        )
    )

    # Goodbye
    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.LEFT_CHAT_MEMBER,
            goodbye
        )
    )

    # Sticker
    app.add_handler(
        MessageHandler(
            filters.Sticker.ALL,
            check_sticker
        )
    )

    # Normal text
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            check_message
        )
    )

    print("NOE BOT STARTED")
    print("AUTO REPLY: ON")
    print("STICKER REPLY: ON")
    print("EMOJI: OFF")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
