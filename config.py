# src/config.py

import os

# Load all the cool secrets from the environment - because we're not about to spill the beans here
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROK_API_KEY = os.getenv("GROK_API_KEY")
GROK_API_URL = os.getenv("GROK_API_URL")
JWK_PATH = os.getenv("JWK_PATH")
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
HUGGINGFACE_SPACE_URL = os.getenv("HUGGINGFACE_SPACE_URL")
RENDER_INTERMEDIARY_URL = os.getenv("RENDER_INTERMEDIARY_URL")
RENDER_TG_BOT_WEBHOOK_URL = os.getenv("RENDER_TG_BOT_WEBHOOK_URL")
MONGO_URI = os.getenv("MONGO_URI")
CHIBI_TG_KEY_GROK = os.getenv("CHIBI_TG_KEY_GROK")
PORT = int(os.getenv("PORT", 8000))  # Default to 8000 if you forgot to set it, because YOLO

