import os
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CallbackQueryHandler
from . import utils, nft_checker, api_interactions, config

# Step 5: Initialize the Telegram bot application - let's get this party started
application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

# Simple state management - because we like to keep track of everything
user_wallets = {}

app = FastAPI()

# Step 6: FastAPI application with detailed lifecycle management - because we're fancy like that
@asynccontextmanager
async def lifespan(app: FastAPI):
    utils.logger.info("Initializing Telegram bot application... 🔥")
    await application.initialize()
    utils.logger.info("Telegram application initialized, all set to go! 🚀")
    utils.logger.info("Starting the Telegram bot application... 🚀")
    await application.start()  # Bot's ready to start flexing
    utils.logger.info("Telegram bot started, we are live! 🔥")
    yield
    utils.logger.info("Stopping Telegram bot application... 🚨")
    await application.stop()
    utils.logger.info("Telegram bot stopped successfully. 🛑")
    utils.logger.info("Shutting down Telegram bot application... 💤")
    await application.shutdown()
    utils.logger.info("Telegram bot shutdown complete. ✅")

app = FastAPI(lifespan=lifespan)

# Step 7: Health check route - just to make sure we're not dead yet
@app.get("/")
async def health_check():
    utils.logger.info("Health check endpoint accessed. Still alive, yo.")
    return {"status": "ok"}

# Step 8: Webhook handler for Telegram updates - where the magic happens
@app.post("/" + config.TELEGRAM_BOT_TOKEN)
async def handle_webhook(request: Request):
    update = await request.json()
    utils.logger.info(f"Received update: {update}")
    telegram_update = Update.de_json(update, application.bot)
    
    if telegram_update.message and telegram_update.message.text:
        message = telegram_update.message.text
        chat_id = telegram_update.message.chat_id
        wallet_address = user_wallets.get(chat_id)

        if not wallet_address:
            keyboard = [[InlineKeyboardButton("Connect Wallet", callback_data="connect_wallet")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await application.bot.send_message(chat_id=chat_id, text="Please connect your wallet to continue:", reply_markup=reply_markup)
            return {"status": "ok"}

        has_chibi = await nft_checker.check_nft_ownership(wallet_address, config.CHIBI_NFT_ADDRESS)
        has_bitty = await nft_checker.check_nft_ownership(wallet_address, config.BITTY_NFT_ADDRESS)

        if has_bitty:  # Tier 3 - Vision capabilities
            response = await api_interactions.query_grok_vision(message)
            await application.bot.send_message(chat_id=chat_id, text=response)
        elif has_chibi:  # Tier 2 - Full text conversation
            response = await api_interactions.query_grok(message)
            await application.bot.send_message(chat_id=chat_id, text=response)
        else:  # Tier 1 - Basic access
            await application.bot.send_message(chat_id=chat_id, text="You need a Chibi NFT for full access. Basic response here.")

    elif telegram_update.callback_query:
        query = telegram_update.callback_query
        await query.answer()

        if query.data == "connect_wallet":
            await query.edit_message_text(text="Please enter your Solana wallet address:")
            user_wallets[query.message.chat_id] = 'awaiting_address'

    return {"status": "ok"}

# Step 9: Ensure the application listens on the correct port - because we need to be heard
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Default to 8000 if PORT is not set, 'cause we're flexible like that
    uvicorn.run(app, host="0.0.0.0", port=port)
