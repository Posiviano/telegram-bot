import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1003976150797"))

TITEL, PREIS, BESCHREIBUNG, KONTAKT, BILD, FEATURED = range(6)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛒 NdeGroundArt Marketplace\n\n"
        "Hier können Kunstwerke, Kunstangebote und kreative Arbeiten eingestellt werden.\n\n"
        "Befehle:\n"
        "/verkaufen - Kunstangebot erstellen\n"
        "/suche - Suche im Marketplace\n"
        "/abbrechen - Vorgang abbrechen"
    )


async def verkaufen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        username = context.bot.username
        await update.message.reply_text(
            f"📩 Bitte schreib mir privat:\n👉 @{username}\n\n"
            "Dort kannst du dein Kunstangebot erstellen."
        )
        return ConversationHandler.END

    context.user_data.clear()
    await update.message.reply_text(
        "🎨 Kunstangebot erstellen!\n\n"
        "Schreib den Titel deines Kunstwerks oder Angebots:"
    )
    return TITEL


async def titel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["titel"] = update.message.text
    await update.message.reply_text("💰 Preis oder Preisvorstellung?")
    return PREIS


async def preis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["preis"] = update.message.text
    await update.message.reply_text("📝 Beschreibung des Kunstwerks / Angebots?")
    return BESCHREIBUNG


async def beschreibung(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["beschreibung"] = update.message.text
    await update.message.reply_text("📱 Kontakt / Instagram / Webseite?")
    return KONTAKT


async def kontakt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["kontakt"] = update.message.text
    await update.message.reply_text("🖼 Bild senden oder 'skip' schreiben.")
    return BILD


async def bild(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text.lower() == "skip":
        context.user_data["bild"] = None
    elif update.message.photo:
        photo = update.message.photo[-1]
        context.user_data["bild"] = photo.file_id
    else:
        await update.message.reply_text("Bitte ein Bild senden oder 'skip' schreiben.")
        return BILD

    await update.message.reply_text(
        "⭐ Featured Post?\n\n"
        "Schreib: Ja oder Nein"
    )
    return FEATURED


async def featured(update: Update, context: ContextTypes.DEFAULT_TYPE):
    featured_text = update.message.text

    titel_text = context.user_data["titel"]
    preis_text = context.user_data["preis"]
    beschreibung_text = context.user_data["beschreibung"]
    kontakt_text = context.user_data["kontakt"]
    bild_file = context.user_data["bild"]

    text = (
        f"🎨 KUNSTANGEBOT\n\n"
        f"🖼 Titel: {titel_text}\n\n"
        f"💰 Preis: {preis_text}\n\n"
        f"📝 Beschreibung:\n{beschreibung_text}\n\n"
        f"📱 Kontakt / Link:\n{kontakt_text}\n\n"
        f"⭐ Featured: {featured_text}\n\n"
        f"#kunst #artist #ndegroundart #marketplace"
    )

    try:
        if bild_file:
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=bild_file,
                caption=text
            )
        else:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=text
            )

        await update.message.reply_text("✅ Dein Kunstangebot wurde veröffentlicht!")

    except Exception as e:
        await update.message.reply_text(
            "❌ Fehler beim Posten in den Kanal.\n\n"
            "Bitte prüfe:\n"
            "1. Bot ist Admin im Marketplace-Kanal\n"
            "2. Bot darf Nachrichten senden\n"
            "3. CHANNEL_ID stimmt in Render"
        )
        print(f"Fehler beim Posten: {e}")

    context.user_data.clear()
    return ConversationHandler.END


async def suche(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🔍 Beispiel:\n"
            "/suche Acryl\n"
            "/suche Leinwand\n"
            "/suche Skulptur\n"
            "/suche Fotografie"
        )
        return

    suchwort = " ".join(context.args)

    await update.message.reply_text(
        f"🔎 Suche nach: {suchwort}\n\n"
        "Die Marketplace-Suche kann später erweitert werden.\n"
        "Aktuell kannst du den Marketplace-Kanal direkt nach Kunstwerken durchsuchen."
    )


async def abbrechen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Vorgang abgebrochen.")
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ Befehl nicht erkannt.\n\n"
        "Nutze:\n"
        "/start\n"
        "/verkaufen\n"
        "/suche\n"
        "/abbrechen"
    )


def main():
    if not TOKEN:
        raise RuntimeError(
            "TOKEN fehlt. Setze TOKEN in Render Environment Variables."
        )

    app = ApplicationBuilder().token(TOKEN).build()

    verkaufen_handler = ConversationHandler(
        entry_points=[CommandHandler("verkaufen", verkaufen)],
        states={
            TITEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, titel)
            ],
            PREIS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, preis)
            ],
            BESCHREIBUNG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, beschreibung)
            ],
            KONTAKT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, kontakt)
            ],
            BILD: [
                MessageHandler(
                    (filters.PHOTO | filters.TEXT)
                    & ~filters.COMMAND,
                    bild
                )
            ],
            FEATURED: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, featured)
            ],
        },
        fallbacks=[
            CommandHandler("abbrechen", abbrechen)
        ],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(verkaufen_handler)
    app.add_handler(CommandHandler("suche", suche))
    app.add_handler(CommandHandler("abbrechen", abbrechen))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print("NdeGroundArt Market Bot läuft...")
    app.run_polling()


if __name__ == "__main__":
    main()
