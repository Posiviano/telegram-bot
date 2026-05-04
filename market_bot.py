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
        "Befehle:\n"
        "/verkaufen - Angebot erstellen\n"
        "/suche - Suche im Marketplace\n"
        "/abbrechen - Vorgang abbrechen"
    )


async def verkaufen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        username = context.bot.username
        await update.message.reply_text(
            f"📩 Bitte schreib mir privat:\n👉 @{username}\n\n"
            "Dort kannst du dein Angebot erstellen."
        )
        return ConversationHandler.END

    context.user_data.clear()
    await update.message.reply_text(
        "🎨 Verkauf starten!\n\n"
        "Schreib den Titel deines Angebots:"
    )
    return TITEL


async def titel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["titel"] = update.message.text
    await update.message.reply_text("💰 Preis?")
    return PREIS


async def preis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["preis"] = update.message.text
    await update.message.reply_text("📝 Beschreibung?")
    return BESCHREIBUNG


async def beschreibung(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["beschreibung"] = update.message.text
    await update.message.reply_text("📬 Kontakt / Instagram / Website?")
    return KONTAKT


async def kontakt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["kontakt"] = update.message.text
    await update.message.reply_text("🖼 Bild senden oder `skip` schreiben.")
    return BILD


async def bild(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data["photo"] = update.message.photo[-1].file_id
    elif update.message.text and update.message.text.lower() == "skip":
        context.user_data["photo"] = None
    else:
        await update.message.reply_text("Bitte Bild senden oder `skip` schreiben.")
        return BILD

    await update.message.reply_text(
        "🔥 Featured?\n\n"
        "1 = Normal\n"
        "2 = Featured"
    )
    return FEATURED


async def featured(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()

    title = context.user_data.get("titel", "")
    price = context.user_data.get("preis", "")
    desc = context.user_data.get("beschreibung", "")
    contact = context.user_data.get("kontakt", "")
    photo = context.user_data.get("photo")

    if choice == "2":
        status = "🔥 FEATURED ANGEBOT"
        note = "\n\n💎 Featured gewählt: Bitte Admin für Zahlung kontaktieren."
    else:
        status = "🎨 ANGEBOT"
        note = ""

    post = (
        f"{status}\n\n"
        f"🖼 Titel: {title}\n"
        f"💰 Preis: {price}\n"
        f"📝 Beschreibung: {desc}\n"
        f"📬 Kontakt / Link: {contact}\n\n"
        f"🔐 Hinweis: Private Abwicklung möglich. Sichere Abwicklung über das Team optional."
        f"{note}\n\n"
        f"#kunst #ndegroundart #market"
    )

    try:
        if photo:
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo,
                caption=post,
            )
        else:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=post,
            )

        await update.message.reply_text("✅ Dein Angebot wurde im Marketplace-Kanal gepostet.")

    except Exception as e:
        await update.message.reply_text(
            "❌ Fehler beim Posten in den Kanal.\n\n"
            "Prüfe:\n"
            "1. Bot ist Admin im Kanal\n"
            "2. Bot darf Nachrichten senden\n"
            "3. CHANNEL_ID stimmt"
        )
        print(f"Fehler beim Posten: {e}")

    context.user_data.clear()
    return ConversationHandler.END


async def suche(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "🔍 Für die Suche bitte privat schreiben.\n"
            "Marketplace-Suche kommt bald."
        )
        return

    await update.message.reply_text(
        "🔍 Suche kommt bald.\n\n"
        "Aktuell kannst du den Marketplace-Kanal direkt durchsuchen."
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
        "/suche"
    )


def main():
    if not TOKEN:
        raise RuntimeError("TOKEN fehlt. Setze TOKEN in Render Environment Variables.")

    app = ApplicationBuilder().token(TOKEN).build()

    verkaufen_handler = ConversationHandler(
        entry_points=[CommandHandler("verkaufen", verkaufen)],
        states={
            TITEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, titel)],
            PREIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, preis)],
            BESCHREIBUNG: [MessageHandler(filters.TEXT & ~filters.COMMAND, beschreibung)],
            KONTAKT: [MessageHandler(filters.TEXT & ~filters.COMMAND, kontakt)],
            BILD: [MessageHandler((filters.PHOTO | filters.TEXT) & ~filters.COMMAND, bild)],
            FEATURED: [MessageHandler(filters.TEXT & ~filters.COMMAND, featured)],
        },
        fallbacks=[CommandHandler("abbrechen", abbrechen)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("suche", suche))
    app.add_handler(CommandHandler("abbrechen", abbrechen))
    app.add_handler(verkaufen_handler)
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print("Market Bot läuft...")
    app.run_polling()


if __name__ == "__main__":
    main()
