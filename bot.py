from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8739274946:AAEFC70TMIRSyI65kslyHjo_3wLSu_zqBzw"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎨 Willkommen bei NdeGroundArt!\n\n"
        "Hier treffen sich Künstler, Sammler und Kunstbegeisterte aus der Schweiz, Deutschland und Österreich.\n\n"
        "Befehle:\n"
        "/regeln\n"
        "/vorstellen"
    )


async def regeln(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Regeln bei NdeGroundArt:\n\n"
        "1. Respektvoller Umgang ist Pflicht.\n"
        "2. Keine Beleidigungen, kein Hass, kein Spam.\n"
        "3. Nur echte Kunst, ehrliche Angebote und seriöser Austausch.\n"
        "4. Künstler, Sammler und Kunstbegeisterte sind willkommen.\n"
        "5. Neue Mitglieder sollen die Regeln lesen und sich kurz vorstellen.\n\n"
        "Danke, dass du Teil der Community bist. 🎨"
    )


async def vorstellen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎨 Vorlage für deine Vorstellung:\n\n"
        "Künstlername / Name:\n"
        "Land / Region:\n"
        "Kunstrichtung:\n"
        "Instagram / Website:\n"
        "Was macht deine Kunst oder dein Interesse an Kunst aus?\n\n"
        "Kopiere die Vorlage und fülle sie aus."
    )


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        await update.message.reply_text(
            f"👋 Willkommen {user.first_name} bei NdeGroundArt!\n\n"
            "🎨 Wo Künstler, Sammler und Kunstbegeisterte zusammenfinden.\n\n"
            "📌 Wichtig:\n"
            "Bitte lies zuerst die Regeln: /regeln\n"
            "Stell dich danach kurz vor: /vorstellen\n\n"
            "💬 Alle Befehle einfach unten im Chat eingeben.\n\n"
            "Viel Spass und willkommen in der Community! 🔥"
        )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("regeln", regeln))
    app.add_handler(CommandHandler("vorstellen", vorstellen))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    print("Community Bot läuft...")
    app.run_polling()


if __name__ == "__main__":
    main()