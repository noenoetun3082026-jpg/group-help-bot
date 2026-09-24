import os
import json

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "replies.json"


def load_replies():
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("LOAD ERROR:", repr(e))
        return {}


replies = load_replies()


def save_replies():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(
                replies,
                f,
                ensure_ascii=False,
                indent=2
            )

        print("REPLIES SAVED")

    except Exception as e:
        print("SAVE ERROR:", repr(e))


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
        print("ADMIN CHECK ERROR:", repr(e))
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await update.message.reply_text(
        "Group Reply Bot အလုပ်လုပ်နေပါပြီ။\n\n"
        "/help နဲ့ command တွေကြည့်နိုင်ပါတယ်။"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await update.message.reply_text(
        "Group Reply Bot Commands\n\n"
        "/setreply စာ | ပြန်စာ\n"
        "ဥပမာ:\n"
        "/setreply မင်္ဂလာပါ | မင်္ဂလာပါဗျာ\n\n"
        "/listreply\n"
        "သတ်မှတ်ထားတဲ့ reply တွေကြည့်ရန်\n\n"
        "/delreply စာ\n"
        "Reply တစ်ခုဖျက်ရန်\n\n"
        "/clearreply\n"
        "ဒီ GP ရဲ့ reply အားလုံးဖျက်ရန်"
    )


async def set_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not update.effective_chat:
        return

    if not await is_admin(update, context):
        await update.message.reply_text(
            "ဒီ command ကို Admin ပဲသုံးလို့ရပါတယ်။"
        )
        return

    text = update.message.text or ""

    content = text[len("/setreply"):].strip()

    if "|" not in content:
        await update.message.reply_text(
            "ပုံစံမှားနေပါတယ်။\n\n"
            "ဥပမာ:\n"
            "/setreply မင်္ဂလာပါ | မင်္ဂလာပါဗျာ"
        )
        return

    trigger, response = content.split("|", 1)

    trigger = trigger.strip()
    response = response.strip()

    if not trigger or not response:
        await update.message.reply_text(
            "စာနဲ့ ပြန်စာ နှစ်ခုလုံးထည့်ပေးပါ။"
        )
        return

    chat_id = str(update.effective_chat.id)

    if chat_id not in replies:
        replies[chat_id] = {}

    replies[chat_id][trigger.lower()] = {
        "trigger": trigger,
        "response": response
    }

    save_replies()

    await update.message.reply_text(
        f"Reply သတ်မှတ်ပြီးပါပြီ။\n\n"
        f"စာ: {trigger}\n"
        f"ပြန်စာ: {response}"
    )

    print(
        f"SET REPLY: "
        f"{chat_id} | {trigger} -> {response}"
    )


async def list_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not update.effective_chat:
        return

    chat_id = str(update.effective_chat.id)

    group_replies = replies.get(chat_id, {})

    if not group_replies:
        await update.message.reply_text(
            "ဒီ GP မှာ reply သတ်မှတ်ထားတာ မရှိသေးပါ။"
        )
        return

    lines = ["သတ်မှတ်ထားတဲ့ Reply များ:\n"]

    number = 1

    for item in group_replies.values():
        trigger = item["trigger"]
        response = item["response"]

        lines.append(
            f"{number}. {trigger} → {response}"
        )

        number += 1

    await update.message.reply_text(
        "\n".join(lines)
    )


async def delete_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not update.effective_chat:
        return

    if not await is_admin(update, context):
        await update.message.reply_text(
            "ဒီ command ကို Admin ပဲသုံးလို့ရပါတယ်။"
        )
        return

    text = update.message.text or ""

    trigger = text[len("/delreply"):].strip()

    if not trigger:
        await update.message.reply_text(
            "ဥပမာ:\n"
            "/delreply မင်္ဂလာပါ"
        )
        return

    chat_id = str(update.effective_chat.id)

    group_replies = replies.get(chat_id, {})

    key = trigger.lower()

    if key not in group_replies:
        await update.message.reply_text(
            f"\"{trigger}\" အတွက် reply မတွေ့ပါ။"
        )
        return

    del group_replies[key]

    save_replies()

    await update.message.reply_text(
        f"\"{trigger}\" reply ကို ဖျက်ပြီးပါပြီ။"
    )


async def clear_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not update.effective_chat:
        return

    if not await is_admin(update, context):
        await update.message.reply_text(
            "ဒီ command ကို Admin ပဲသုံးလို့ရပါတယ်။"
        )
        return

    chat_id = str(update.effective_chat.id)

    if chat_id not in replies or not replies[chat_id]:
        await update.message.reply_text(
            "ဖျက်စရာ reply မရှိပါ။"
        )
        return

    replies[chat_id] = {}

    save_replies()

    await update.message.reply_text(
        "ဒီ GP ရဲ့ reply အားလုံး ဖျက်ပြီးပါပြီ။"
    )


async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    chat_id = str(chat.id)

    group_replies = replies.get(chat_id, {})

    if not group_replies:
        return

    key = text.strip().lower()

    if key not in group_replies:
        return

    response = group_replies[key]["response"]

    try:
        await message.reply_text(response)

        print(
            f"REPLY SENT: "
            f"{text} -> {response}"
        )

    except Exception as e:
        print("REPLY ERROR:", repr(e))


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(
        "TELEGRAM ERROR:",
        repr(context.error)
    )


def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN မတွေ့ပါ"
        )

    print("BOT TOKEN: OK")
    print("AI REPLY: DISABLED")
    print("GROUP REPLY BOT STARTED")

    app = (
        Application
        .builder()
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
        CommandHandler("setreply", set_reply)
    )

    app.add_handler(
        CommandHandler("listreply", list_reply)
    )

    app.add_handler(
        CommandHandler("delreply", delete_reply)
    )

    app.add_handler(
        CommandHandler("clearreply", clear_reply)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            check_message
        )
    )

    app.add_error_handler(error_handler)

    print("BOT IS RUNNING...")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
