import os
import json
from pathlib import Path

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")
WARN_LIMIT = int(os.getenv("WARN_LIMIT", "3"))
LOG_CHAT_ID = os.getenv("LOG_CHAT_ID")

WARN_FILE = Path("warnings.json")
USER_FILE = Path("user_names.json")

BLOCKED_WORDS = [
    # Deutsch
    "sex",
    "porno",
    "porn",
    "nude",
    "nackt",
    "nakt",
    "nacktbilder",
    "ficken",
    "fick",
    "fotze",
    "schlampe",
    "nutte",
    "hure",
    "hurensohn",
    "arsch",
    "arschloch",
    "wichser",
    "wixer",
    "wixen",
    "missgeburt",
    "spast",
    "behindert",
    "idiot",
    "opfer",
    "bastard",
    "schwuchtel",
    "verpiss",
    "halt die fresse",
    "fresse",
    "huso",
    "mongo",
    "knecht",
    "dummkopf",

    # Gewalt
    "gewalt",
    "kill",
    "mord",
    "sterben",
    "umbringen",
    "erschiessen",
    "waffe",

    # Drogen
    "droge",
    "drogen",
    "kokain",
    "cocaine",
    "heroin",
    "meth",
    "lsd",
    "weed",
    "cannabis",
    "hass",
    "ecstasy",
    "mdma",

    # Englisch
    "bitch",
    "fuck",
    "fucking",
    "asshole",
    "slut",
    "whore",
    "niga",
    "nigga",
    "nigger",
    "negger",
    "neg4",
]


def load_json(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_json(path: Path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id):
    try:
        chat_id = update.effective_chat.id
        member = await context.bot.get_chat_member(chat_id, user_id)

        return member.status in ["administrator", "creator"]

    except Exception as e:
        print(f"Admin Check Fehler: {e}")
        return False


def contains_blocked_word(text: str):
    text_lower = text.lower()

    for word in BLOCKED_WORDS:
        if word.lower() in text_lower:
            return word

    return None


async def send_log(context: ContextTypes.DEFAULT_TYPE, text: str):
    if not LOG_CHAT_ID:
        return

    try:
        await context.bot.send_message(
            chat_id=int(LOG_CHAT_ID),
            text=text
        )

    except Exception as e:
        print(f"Log Fehler: {e}")


async def check_name_change(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.message or update.edited_message

    if not message or not message.from_user:
        return

    user = message.from_user

    chat_id = str(update.effective_chat.id)
    user_id = str(user.id)

    current_name = user.full_name or "kein Name"
    current_username = f"@{user.username}" if user.username else "kein Username"

    data = load_json(USER_FILE)

    data.setdefault(chat_id, {})

    old_data = data[chat_id].get(user_id)

    if old_data:

        old_name = old_data.get("name", "kein Name")
        old_username = old_data.get("username", "kein Username")

        name_changed = old_name != current_name
        username_changed = old_username != current_username

        if name_changed or username_changed:

            parts = []

            if name_changed:
                parts.append(
                    f"🔄 Name geändert:\n{old_name} ➜ {current_name}"
                )

            if username_changed:
                parts.append(
                    f"👤 Username geändert:\n{old_username} ➜ {current_username}"
                )

            text = "\n\n".join(parts)

            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text
                )

            except Exception as e:
                print(f"Namensänderung konnte nicht gesendet werden: {e}")

            await send_log(context, text)

    data[chat_id][user_id] = {
        "name": current_name,
        "username": current_username,
    }

    save_json(USER_FILE, data)


async def moderate_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.message or update.edited_message

    if not message:
        return

    await check_name_change(update, context)

    if not message.text:
        return

    user = message.from_user

    if not user:
        return

    if await is_admin(update, context, user.id):
        return

    found_word = contains_blocked_word(message.text)

    if not found_word:
        return

    try:
        await message.delete()

    except Exception as e:
        print(f"Nachricht konnte nicht gelöscht werden: {e}")

    warnings = load_json(WARN_FILE)

    chat_id = str(update.effective_chat.id)
    user_id = str(user.id)

    warnings.setdefault(chat_id, {})
    warnings[chat_id].setdefault(user_id, 0)

    warnings[chat_id][user_id] += 1

    count = warnings[chat_id][user_id]

    save_json(WARN_FILE, warnings)

    name = user.full_name
    username = f"@{user.username}" if user.username else "kein Username"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            f"⚠️ Verwarnung für {name} ({username})\n\n"
            f"Grund: Gesperrtes Wort erkannt\n"
            f"Treffer: {found_word}\n"
            f"Verwarnung: {count}/{WARN_LIMIT}\n\n"
            f"Bitte beachte die Gruppenregeln."
        ),
    )

    await send_log(
        context,
        (
            "🛡️ ModBot Aktion\n\n"
            f"User: {name} ({username})\n"
            f"User ID: {user.id}\n"
            f"Chat ID: {update.effective_chat.id}\n"
            f"Treffer: {found_word}\n"
            f"Verwarnungen: {count}/{WARN_LIMIT}"
        ),
    )

    if count >= WARN_LIMIT:

        try:

            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user.id
            )

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    f"🚫 {name} wurde nach "
                    f"{WARN_LIMIT} Verwarnungen gebannt."
                )
            )

            await send_log(
                context,
                (
                    "🚫 User gebannt\n\n"
                    f"User: {name} ({username})\n"
                    f"User ID: {user.id}\n"
                    f"Chat ID: {update.effective_chat.id}\n"
                    f"Grund: {WARN_LIMIT} Verwarnungen erreicht"
                ),
            )

        except Exception as e:
            print(f"User konnte nicht gebannt werden: {e}")


def main():

    if not TOKEN:
        raise RuntimeError(
            "TOKEN fehlt. Setze TOKEN in Render Environment Variables."
        )

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            moderate_message
        )
    )

    print("NdeGroundArt ModBot läuft 24/7 auf Render...")

    app.run_polling()


if __name__ == "__main__":
    main()
