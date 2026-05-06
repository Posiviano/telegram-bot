import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")


WELCOME_TEXT = (
    "🎨 Willkommen bei NdeGroundArt!\n\n"
    "Hier treffen sich Künstler, Sammler und Kunstbegeisterte aus der Schweiz, "
    "Deutschland, Österreich und darüber hinaus.\n\n"
    "NdeGroundArt soll Künstler und Sammler verbinden, Austausch ermöglichen "
    "und Raum für Kunst, Erfahrungen, Angebote und neue Kontakte schaffen.\n\n"
    "📌 Wichtig:\n"
    "Unsere Gruppe befindet sich noch im Aufbau. Regeln, Abläufe, Funktionen "
    "und einzelne Bereiche können sich noch ändern oder erweitert werden.\n\n"
    "Bitte lies zuerst die Regeln:\n"
    "/regeln\n\n"
    "Und stelle dich gerne kurz vor:\n"
    "/vorstellen\n\n"
    "Schön bist du Teil der Community. 🖤🎨"
)


RULES_TEXT = (
    "📌 Regeln bei NdeGroundArt:\n\n"
    "1. Respektvoller Umgang ist Pflicht.\n"
    "2. Keine Beleidigungen, kein Hass, kein Spam.\n"
    "3. Nur echte Kunst, ehrliche Angebote und seriöser Austausch.\n"
    "4. Künstler, Sammler und Kunstbegeisterte sind willkommen.\n"
    "5. Neue Mitglieder sollen die Regeln lesen und sich kurz vorstellen.\n"
    "6. Kauf, Verkauf oder Austausch erfolgen fair und transparent.\n"
    "7. Bei Unsicherheiten kann das Team/Admin helfen.\n\n"
    "⚠️ Hinweis:\n"
    "Die Gruppe befindet sich noch im Aufbau. Regeln, Funktionen und Abläufe "
    "können sich noch ändern oder erweitert werden.\n\n"
    "Danke, dass du Teil der Community bist. 🎨"
)


INTRO_TEXT = (
    "🎨 Vorlage für deine Vorstellung:\n\n"
    "Künstlername / Name:\n"
    "Land / Region:\n"
    "Kunstrichtung:\n"
    "Instagram / Webseite:\n"
    "Was macht deine Kunst oder dein Interesse an Kunst aus?\n\n"
    "Kopiere die Vorlage und fülle sie aus."
)


HELP_TEXT = (
    "🖤 NdeGroundArt Bot Hilfe\n\n"
    "Befehle:\n"
    "/start - Willkommensnachricht anzeigen\n"
    "/regeln - Gruppenregeln anzeigen\n"
    "/vorstellen - Vorlage für Vorstellung anzeigen\n"
    "/hilfe - Hilfe anzeigen\n\n"
    "⚠️ Hinweis:\n"
    "Der Bot und die Gruppe befinden sich noch im Aufbau. Funktionen und Texte "
    "können sich noch ändern."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT)


async def regeln(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(RULES_TEXT)


async def vorstellen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(INTRO_TEXT)


async def hilfe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)


async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members:
        return

    for member in update.message.new_chat_members:
        if member.is_bot:
            continue

        await update.message.reply_text(
            f"🎨 Willkommen bei NdeGroundArt, {member.first_name}!\n\n"
            "Schön bist du Teil unserer Community.\n\n"
            "Bitte lies zuerst die Regeln:\n"
            "/regeln\n\n"
            "Und stelle dich gerne kurz vor:\n"
            "/vorstellen\n\n"
            "⚠️ Hinweis:\n"
            "Die Gruppe befindet sich noch im Aufbau. Regeln, Abläufe und Funktionen "
            "können sich noch ändern oder erweitert werden.\n\n"
            "Viel Freude beim Austausch mit Künstlern, Sammlern und Kunstbegeisterten. 🖤"
        )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ Befehl nicht erkannt.\n\n"
        "Nutze:\n"
        "/start\n"
        "/regeln\n"
        "/vorstellen\n"
        "/hilfe"
    )


def main():
    if not TOKEN:
        raise RuntimeError(
            "TOKEN fehlt. Setze TOKEN in Render Environment Variables."
        )

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("regeln", regeln))
    app.add_handler(CommandHandler("vorstellen", vorstellen))
    app.add_handler(CommandHandler("hilfe", hilfe))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))

    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print("NdeGroundArt Gruppenbot läuft...")
    app.run_polling()


if __name__ == "__main__":
    main()
