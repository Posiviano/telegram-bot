import os
import json
from pathlib import Path
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
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "").replace("@", "").strip()

OFFERS_FILE = Path("offers.json")

TITEL, PREIS, BESCHREIBUNG, KONTAKT, HASHTAGS, BILD, FEATURED = range(7)


def load_offers():
    if OFFERS_FILE.exists():
        try:
            with open(OFFERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []


def save_offers(data):
    with open(OFFERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def make_link(message_id):
    if CHANNEL_USERNAME:
        return f"https://t.me/{CHANNEL_USERNAME}/{message_id}"

    clean_id = str(CHANNEL_ID).replace("-100", "")
    return f"https://t.me/c/{clean_id}/{message_id}"


def normalize_tags(text):
    tags = []

    for word in text.split():
        word = word.strip()

        if not word:
            continue

        if not word.startswith("#"):
            word = "#" + word

        tags.append(word)

    return tags


async def verkaufen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        username = context.bot.username

        await update.message.reply_text(
            f"📩 Bitte schreibe dem Bot privat:\n👉 @{username}"
        )

        return ConversationHandler.END

    context.user_data.clear()

    await update.message.reply_text(
        "🎨 Willkommen beim NdeGroundArt Marketplace!\n\n"
        "🖼 Titel deines Angebots?"
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

    await update.message.reply_text("📱 Kontakt / Instagram / Webseite?")
    return KONTAKT


async def kontakt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["kontakt"] = update.message.text

    await update.message.reply_text(
        "🏷 Hashtags senden\n\n"
        "Beispiele:\n"
        "#Acryl #Leinwand #Abstract\n"
        "#DigitalArt #Fotografie"
    )

    return HASHTAGS


async def hashtags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["hashtags"] = normalize_tags(update.message.text)

    await update.message.reply_text(
        "🖼 Bild senden oder 'skip' schreiben."
    )

    return BILD


async def bild(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data["bild"] = update.message.photo[-1].file_id

    elif update.message.text and update.message.text.lower() == "skip":
        context.user_data["bild"] = None

    else:
        await update.message.reply_text(
            "Bitte Bild senden oder 'skip' schreiben."
        )
        return BILD

    await update.message.reply_text(
        "⭐ Featured Post?\nJa oder Nein"
    )

    return FEATURED


async def featured(update: Update, context: ContextTypes.DEFAULT_TYPE):
    featured_text = update.message.text

    titel_text = context.user_data["titel"]
    preis_text = context.user_data["preis"]
    beschreibung_text = context.user_data["beschreibung"]
    kontakt_text = context.user_data["kontakt"]
    hashtags = context.user_data["hashtags"]
    bild_file = context.user_data["bild"]

    hashtag_text = " ".join(hashtags)

    post_text = (
        f"🎨 KUNSTANGEBOT\n\n"
        f"🖼 Titel:\n{titel_text}\n\n"
        f"💰 Preis:\n{preis_text}\n\n"
        f"📝 Beschreibung:\n{beschreibung_text}\n\n"
        f"📱 Kontakt:\n{kontakt_text}\n\n"
        f"⭐ Featured:\n{featured_text}\n\n"
        f"{hashtag_text}\n"
        f"#NdeGroundArt #Marketplace"
    )

    try:
        if bild_file:
            sent = await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=bild_file,
                caption=post_text
            )
        else:
            sent = await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=post_text
            )

        link = make_link(sent.message_id)

        offers = load_offers()

        offers.append({
            "titel": titel_text,
            "preis": preis_text,
            "hashtags": hashtags,
            "beschreibung": beschreibung_text,
            "link": link
        })

        save_offers(offers)

        await update.message.reply_text(
            f"✅ Angebot veröffentlicht!\n\n🔗 {link}"
        )

    except Exception as e:
        print(e)

        await update.message.reply_text(
            "❌ Fehler beim Veröffentlichen."
        )

    context.user_data.clear()

    return ConversationHandler.END


async def suche(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🔍 Suche Beispiele:\n\n"
            "/suche Acryl\n"
            "/suche Leinwand\n"
            "/suche Abstract\n"
            "/suche Fotografie"
        )
        return

    search = " ".join(context.args).lower()

    if not search.startswith("#"):
        search = "#" + search

    offers = load_offers()

    found = []

    for offer in offers:
        tags = [x.lower() for x in offer.get("hashtags", [])]

        if search in tags:
            found.append(offer)

    if not found:
        await update.message.reply_text(
            "❌ Keine Angebote gefunden."
        )
        return

    text = f"🔍 Ergebnisse für {search}\n\n"

    for offer in found[:10]:
        text += (
            f"🎨 {offer['titel']}\n"
            f"💰 {offer['preis']}\n"
            f"👉 {offer['link']}\n\n"
        )

    await update.message.reply_text(text)


async def abbrechen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text("❌ Abgebrochen.")

    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conversation = ConversationHandler(
        entry_points=[
            CommandHandler("verkaufen", verkaufen)
        ],

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

            HASHTAGS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, hashtags)
            ],

            BILD: [
                MessageHandler(
                    (filters.TEXT | filters.PHOTO) & ~filters.COMMAND,
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

    app.add_handler(conversation)

    app.add_handler(
        CommandHandler("suche", suche)
    )

    app.add_handler(
        CommandHandler("abbrechen", abbrechen)
    )

    print("NdeGroundArt MarketBot läuft...")

    app.run_polling()


if __name__ == "__main__":
    main()
