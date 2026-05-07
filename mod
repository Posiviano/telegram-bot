import os
import json
from pathlib import Path
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")
WARN_LIMIT = int(os.getenv("WARN_LIMIT", "3"))
LOG_CHAT_ID = os.getenv("LOG_CHAT_ID")
WARN_FILE = Path("warnings.json")

BLOCKED_WORDS = [
    "sex",
    "porno",
    "porn",
    "nude",
    "nackt",
    "nacktbilder",
    "gewalt",
    "kill",
    "mord",
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
    "beleidigung",
]


def load_warnings():
    if WARN_FILE.exists():
        try:
            return json.loads(WARN_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_warnings(data):
    WARN_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
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


async def moderate_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message or update.edited_message

    if not message or not message.text:
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
        print(f"Nachricht konnte nicht geloescht werden: {e}")

    warnings = load_warnings()
    chat_id = str(update.effective_chat.id)
    user_id = str(user.id)

    warnings.setdefault(chat_id, {})
    warnings[chat_id].setdefault(user_id, 0)
    warnings[chat_id][user_id] += 1
    count = warnings[chat_id][user_id]

    save_warnings(warnings)

    name = user.full_name
    username = f"@{user.username}" if user.username else "kein Username"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            f"⚠️ Verwarnung fuer {name} ({username})\n\n"
            f"Grund: Unerlaubter Inhalt / gesperrtes Wort\n"
            f"Verwarnung: {count}/{WARN_LIMIT}\n\n"
            "Bitte beachte die Gruppenregeln."
        ),
    )

    await send_log(
        context,
        (
            "🛡 ModBot Aktion\n\n"
            f"User: {name} ({username})\n"
            f"User ID: {user.id}\n"
            f"Chat ID: {update.effective_chat.id}\n"
            f"Grund: gesperrtes Wort erkannt\n"
            f"Treffer: {found_word}\n"
            f"Warnungen: {count}/{WARN_LIMIT}"
        ),
    )

    if count >= WARN_LIMIT:
        try:
            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user.id,
            )

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🚫 {name} wurde nach {WARN_LIMIT} Verwarnungen gebannt.",
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


async def name_change_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = update.chat_member

    if not chat_member:
        return

    old_user = chat_member.old_chat_member.user
    new_user = chat_member.new_chat_member.user

    old_name = old_user.full_name
    new_name = new_user.full_name

    old_username = old_user.username or "kein Username"
    new_username = new_user.username or "kein Username"

    if old_name != new_name or old_username != new_username:
        text = (
            "🔄 Mitgliedsdaten geaendert\n\n"
            f"Alter Name: {old_name}\n"
            f"Neuer Name: {new_name}\n\n"
            f"Alter Username: @{old_username}\n"
            f"Neuer Username: @{new_username}"
        )

        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
            )
        except Exception as e:
            print(f"Name Change Nachricht Fehler: {e}")

        await send_log(context, text)


def main():
    if not TOKEN:
        raise RuntimeError(
            "TOKEN fehlt. Setze TOKEN in Render Environment Variables."
        )

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            moderate_message
        )
    )

    app.add_handler(
        MessageHandler(
            filters.UpdateType.EDITED_MESSAGE,
            moderate_message
        )
    )

    app.add_handler(
        ChatMemberHandler(
            name_change_log,
            ChatMemberHandler.CHAT_MEMBER
        )
    )

    print("NdeGroundArt ModBot laeuft 24/7 auf Render...")
    app.run_polling()


if __name__ == "__main__":
    main()
