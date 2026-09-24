import os
import json

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
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = int(
    os.getenv("BOT_OWNER_ID", "0")
)

REPLIES_FILE = "replies.json"
GROUPS_FILE = "groups.json"


# =========================
# FILE HELPERS
# =========================

def load_json(filename):
    if not os.path.exists(filename):
        return {}

    try:
        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    except Exception as e:
        print("LOAD ERROR:", filename, repr(e))
        return {}


def save_json(filename, data):
    try:
        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

        print("SAVED:", filename)

    except Exception as e:
        print("SAVE ERROR:", filename, repr(e))


replies = load_json(REPLIES_FILE)
groups = load_json(GROUPS_FILE)


# =========================
# OWNER CHECK
# =========================

def is_owner(update):
    user = update.effective_user

    if not user:
        return False

    return (
        OWNER_ID != 0
        and user.id == OWNER_ID
    )


# =========================
# ADMIN CHECK
# =========================

async def is_admin(update, context):

    user = update.effective_user
    chat = update.effective_chat

    if not user or not chat:
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

    except Exception as e:

        print(
            "ADMIN CHECK ERROR:",
            repr(e)
        )

        return False


# =========================
# START
# =========================

async def start(update, context):

    if not update.message:
        return

    await update.message.reply_text(
        "Group Reply Bot အလုပ်လုပ်နေပါပြီ။\n\n"
        "/help နဲ့ command တွေကြည့်နိုင်ပါတယ်။"
    )


# =========================
# HELP
# =========================

async def help_command(update, context):

    if not update.message:
        return

    await update.message.reply_text(
        "📚 Group Reply Bot\n\n"

        "Reply Commands\n"
        "/setreply စာ | ပြန်စာ\n"
        "/listreply\n"
        "/delreply စာ\n"
        "/clearreply\n\n"

        "Broadcast Commands\n"
        "/groups\n"
        "/send\n\n"

        "ဥပမာ:\n"
        "/setreply မင်္ဂလာပါ | မင်္ဂလာပါ ❤️"
    )


# =========================
# AUTO SAVE GROUP
# =========================

async def track_group(update, context):

    member_update = update.my_chat_member

    if not member_update:
        return

    chat = member_update.chat

    if chat.type not in (
        "group",
        "supergroup"
    ):
        return

    status = member_update.new_chat_member.status

    chat_id = str(chat.id)

    # Bot added
    if status in (
        "member",
        "administrator"
    ):

        groups[chat_id] = {
            "id": chat.id,
            "title": chat.title or "Unknown Group",
            "username": chat.username or ""
        }

        save_json(
            GROUPS_FILE,
            groups
        )

        print(
            "GROUP ADDED:",
            chat.title,
            chat.id
        )

    # Bot removed
    elif status in (
        "left",
        "kicked"
    ):

        if chat_id in groups:

            del groups[chat_id]

            save_json(
                GROUPS_FILE,
                groups
            )

        print(
            "GROUP REMOVED:",
            chat.title,
            chat.id
        )


# =========================
# SET REPLY
# =========================

async def set_reply(update, context):

    if not update.message:
        return

    if not update.effective_chat:
        return

    if not await is_admin(
        update,
        context
    ):

        await update.message.reply_text(
            "❌ Admin ပဲ သုံးနိုင်ပါတယ်။"
        )

        return

    text = update.message.text or ""

    content = text[
        len("/setreply"):
    ].strip()

    if "|" not in content:

        await update.message.reply_text(
            "ပုံစံမှားနေပါတယ်။\n\n"
            "/setreply စာ | ပြန်စာ\n\n"
            "ဥပမာ:\n"
            "/setreply ဟယ်လို | ဟယ်လိုပါ ❤️"
        )

        return

    trigger, response = content.split(
        "|",
        1
    )

    trigger = trigger.strip()
    response = response.strip()

    if not trigger or not response:

        await update.message.reply_text(
            "စာနဲ့ ပြန်စာ နှစ်ခုလုံးထည့်ပါ။"
        )

        return

    chat_id = str(
        update.effective_chat.id
    )

    if chat_id not in replies:
        replies[chat_id] = {}

    replies[chat_id][trigger.lower()] = {
        "trigger": trigger,
        "response": response
    }

    save_json(
        REPLIES_FILE,
        replies
    )

    await update.message.reply_text(
        "✅ Reply သတ်မှတ်ပြီးပါပြီ။\n\n"
        f"စာ: {trigger}\n"
        f"ပြန်စာ: {response}"
    )


# =========================
# LIST REPLY
# =========================

async def list_reply(update, context):

    if not update.message:
        return

    if not update.effective_chat:
        return

    chat_id = str(
        update.effective_chat.id
    )

    data = replies.get(
        chat_id,
        {}
    )

    if not data:

        await update.message.reply_text(
            "ဒီ GP မှာ Reply မရှိသေးပါ။"
        )

        return

    lines = [
        "📋 သတ်မှတ်ထားတဲ့ Reply များ\n"
    ]

    number = 1

    for item in data.values():

        lines.append(
            f"{number}. "
            f"{item['trigger']} → "
            f"{item['response']}"
        )

        number += 1

    await update.message.reply_text(
        "\n".join(lines)
    )


# =========================
# DELETE REPLY
# =========================

async def delete_reply(update, context):

    if not update.message:
        return

    if not update.effective_chat:
        return

    if not await is_admin(
        update,
        context
    ):

        await update.message.reply_text(
            "❌ Admin ပဲ သုံးနိုင်ပါတယ်။"
        )

        return

    text = update.message.text or ""

    trigger = text[
        len("/delreply"):
    ].strip()

    if not trigger:

        await update.message.reply_text(
            "/delreply ဟယ်လို"
        )

        return

    chat_id = str(
        update.effective_chat.id
    )

    data = replies.get(
        chat_id,
        {}
    )

    key = trigger.lower()

    if key not in data:

        await update.message.reply_text(
            f"❌ \"{trigger}\" မတွေ့ပါ။"
        )

        return

    del data[key]

    save_json(
        REPLIES_FILE,
        replies
    )

    await update.message.reply_text(
        f"✅ \"{trigger}\" ကို ဖျက်ပြီးပါပြီ။"
    )


# =========================
# CLEAR REPLY
# =========================

async def clear_reply(update, context):

    if not update.message:
        return

    if not update.effective_chat:
        return

    if not await is_admin(
        update,
        context
    ):

        await update.message.reply_text(
            "❌ Admin ပဲ သုံးနိုင်ပါတယ်။"
        )

        return

    chat_id = str(
        update.effective_chat.id
    )

    if not replies.get(chat_id):

        await update.message.reply_text(
            "ဖျက်စရာ Reply မရှိပါ။"
        )

        return

    replies[chat_id] = {}

    save_json(
        REPLIES_FILE,
        replies
    )

    await update.message.reply_text(
        "✅ ဒီ GP ရဲ့ Reply အားလုံး ဖျက်ပြီးပါပြီ။"
    )


# =========================
# SHOW GROUPS
# =========================

async def list_groups(update, context):

    if not update.message:
        return

    if not is_owner(update):

        await update.message.reply_text(
            "❌ Owner ပဲ သုံးနိုင်ပါတယ်။"
        )

        return

    if not groups:

        await update.message.reply_text(
            "Bot ထည့်ထားတဲ့ GP မရှိသေးပါ။"
        )

        return

    lines = [
        "📋 Bot ထည့်ထားတဲ့ GP များ\n"
    ]

    number = 1

    for item in groups.values():

        title = item.get(
            "title",
            "Unknown"
        )

        username = item.get(
            "username",
            ""
        )

        if username:

            lines.append(
                f"{number}. "
                f"{title} "
                f"(@{username})"
            )

        else:

            lines.append(
                f"{number}. {title}"
            )

        number += 1

    await update.message.reply_text(
        "\n".join(lines)
    )


# =========================
# SEND TO ALL GROUPS
# =========================

async def broadcast(update, context):

    if not update.message:
        return

    if not is_owner(update):

        await update.message.reply_text(
            "❌ Owner ပဲ သုံးနိုင်ပါတယ်။"
        )

        return

    source = update.message.reply_to_message

    if not source:

        await update.message.reply_text(
            "ပို့ချင်တဲ့ စာ/ပုံကို အရင်ပို့ပါ။\n\n"
            "ပြီးရင် အဲ့ဒီ message ကို Reply လုပ်ပြီး\n"
            "/send ရိုက်ပါ။"
        )

        return

    if not groups:

        await update.message.reply_text(
            "Bot ထည့်ထားတဲ့ GP မရှိသေးပါ။"
        )

        return

    success = 0
    failed = 0

    for chat_id in list(groups.keys()):

        try:

            await context.bot.copy_message(
                chat_id=int(chat_id),
                from_chat_id=source.chat.id,
                message_id=source.message_id
            )

            success += 1

        except Exception as e:

            failed += 1

            print(
                "BROADCAST ERROR:",
                chat_id,
                repr(e)
            )

    await update.message.reply_text(
        "📢 ပို့ပြီးပါပြီ။\n\n"
        f"✅ အောင်မြင်: {success}\n"
        f"❌ မအောင်မြင်: {failed}"
    )


# =========================
# NORMAL MESSAGE REPLY
# =========================

async def check_message(update, context):

    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not message:
        return

    if not user:
        return

    if not chat:
        return

    if user.is_bot:
        return

    text = message.text or ""

    if not text.strip():
        return

    chat_id = str(chat.id)

    data = replies.get(
        chat_id,
        {}
    )

    if not data:
        return

    key = text.strip().lower()

    if key not in data:
        return

    response = data[key]["response"]

    try:

        await message.reply_text(
            response
        )

        print(
            "REPLY SENT:",
            text,
            "->",
            response
        )

    except Exception as e:

        print(
            "REPLY ERROR:",
            repr(e)
        )


# =========================
# ERROR HANDLER
# =========================

async def error_handler(update, context):

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

    if OWNER_ID == 0:

        raise RuntimeError(
            "BOT_OWNER_ID မတွေ့ပါ"
        )

    print("BOT TOKEN: OK")
    print("OWNER ID: OK")
    print("AI: DISABLED")
    print("GROUP REPLY: ON")
    print("BROADCAST: ON")
    print("BOT IS RUNNING...")

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
            "setreply",
            set_reply
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
            "delreply",
            delete_reply
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
            "groups",
            list_groups
        )
    )

    app.add_handler(
        CommandHandler(
            "send",
            broadcast
        )
    )

    # Track bot added/removed
    app.add_handler(
        ChatMemberHandler(
            track_group,
            ChatMemberHandler.MY_CHAT_MEMBER
        )
    )

    # Normal text
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            check_message
        )
    )

    app.add_error_handler(
        error_handler
    )

    app.run_polling(
        drop_pending_updates=True
    )


# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()
