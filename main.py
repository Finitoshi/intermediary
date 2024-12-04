# Filename: main.py

import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from gradio_client import Client
from pymongo import MongoClient
from io import BytesIO
import base64
import datetime
from contextlib import contextmanager
import json

# Configure logging - because if it ain't logged, it's like it never happened, right?
logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS middleware - because we're not trying to gatekeep your requests (but really, lock this down in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change this to specific origins you trust
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables - because secrets are meant to be kept, not shared at the dinner table
HF_TOKEN = os.getenv("HF_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
HUGGINGFACE_SPACE_URL = os.getenv("HUGGINGFACE_SPACE_URL")
HF_INTERMEDIARY_TOKEN = os.getenv("HF_INTERMEDIARY_TOKEN")

# Log environment variable status - because it's nice to know what's up before you get ghosted
logger.info(f"Environment variables loaded: HF_TOKEN={HF_TOKEN is not None}, MONGO_URI={MONGO_URI is not None}, HUGGINGFACE_SPACE_URL={HUGGINGFACE_SPACE_URL is not None}")

# Connect to MongoDB - may the database be with you, or else we're all in for a bad time
mongo_client = MongoClient(MONGO_URI)
try:
    mongo_client.admin.command('ping')
    logger.info("Successfully connected to MongoDB. We're in the matrix now.")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}. Someone's pulled the plug on our reality!")

db = mongo_client['bot_db']
image_collection = db['images']

# Setup Gradio client - let's hope this AI isn't just a bunch of hype
space_name = HUGGINGFACE_SPACE_URL.split('/')[-2] + '/' + HUGGINGFACE_SPACE_URL.split('/')[-1]
gradio_client = Client(space_name, hf_token=HF_INTERMEDIARY_TOKEN)

# Here's a little time tracker - because even AI needs to clock in
@contextmanager
def log_time(message):
    start = datetime.datetime.now()
    try:
        yield
    finally:
        end = datetime.datetime.now()
        duration = end - start
        logger.info(f"{message} took {duration.total_seconds():.2f} seconds. That's like, what, a blink in internet time?")

# Update this endpoint to match Gradio's vibe - or else, no art for you
@app.post("/predict")
async def predict_endpoint(request: Request):
    try:
        # Log request details - because we're nosy about what's coming our way
        logger.debug(f"Received request: {request.method} {request.url}")
        
        # Checkin' the vibes for what we're about to create - can't do art without a prompt, duh
        data = await request.json()
        logger.debug(f"Request body: {json.dumps(data)}")
        prompt = data.get("prompt")
        if not prompt:
            logger.warning("No prompt provided. We can't pull art out of thin air.")
            return JSONResponse(content={"status": "error", "message": "No prompt provided"}, status_code=400)

        logger.info(f"Generating image with prompt: {prompt}. Better be good, AI.")
        
        with log_time("Image generation process"):
            # Generate image - here's hoping the AI didn't skip art class
            logger.debug(f"Headers sent: {gradio_client.headers}")
            job = gradio_client.submit(prompt, api_name="/predict")
            while not job.done():
                pass  # Wait for job to complete - patience isn't just a virtue, it's a necessity
            result = job.result()
        
        # Log Gradio job status - because we're all about transparency, or at least, pretending to be
        logger.debug(f"Gradio job status: {job.status()}")

        # Convert image to base64 for storage - text over binary, because we're edgy like that
        if hasattr(result, 'save'):  # If result is an image that can be saved
            logger.debug("Converting image to base64. Time for some digital alchemy.")
            buffered = BytesIO()
            result.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
        elif isinstance(result, str):  # If result is already a base64 string or URL
            logger.debug("Result is already a string, probably base64 or URL. AI, you've saved us some steps.")
            img_str = result
        else:
            logger.error("Unexpected result format from Gradio. Did AI drop the ball?")
            raise ValueError("Unexpected result format from Gradio")

        # Store in MongoDB - because we like to keep our art in the cloud, not on cave walls
        with log_time("MongoDB insertion"):
            result = image_collection.insert_one({
                "prompt": prompt,
                "image": img_str,
                "timestamp": datetime.datetime.utcnow()
            })
            logger.info(f"Inserted document with ID: {result.inserted_id}. We're archiving our digital art.")

        logger.info("Image successfully generated and stored. Art for the future, or at least until the apocalypse.")
        return JSONResponse(content={
            "status": "success", 
            "message": "Image generated and stored", 
            "image": f"data:image/png;base64,{img_str}"
        }, status_code=200)

    except Exception as e:
        import traceback
        logger.error(f"Error in our grand image generation scheme: {str(e)}. AI, you've disappointed us!")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return JSONResponse(content={
            "status": "error", 
            "message": f"Image generation failed: {str(e)}. Maybe try a less ambitious prompt?"
        }, status_code=500)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Default to 8000 if PORT is not set, because we're cool with defaults
    logger.info(f"Starting server on port {port}. Let's see some art, or at least some errors!")
    uvicorn.run(app, host="0.0.0.0", port=port)
