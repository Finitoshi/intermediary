# src/main.py

import os
import logging
from fastapi import FastAPI, Request
from gradio_client import Client
from pymongo import MongoClient
from io import BytesIO
import base64
import datetime
from contextlib import contextmanager

# Setup logging - because if a tree falls in a forest and no one logs it, did it really fall?
logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Directly access environment variables - because we're not playing the guessing game with secrets
HF_TOKEN = os.getenv("HF_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 8000))  # Default to 8000 if PORT is not set, 'cause we're flexible like that
HUGGINGFACE_SPACE_URL = os.getenv("HUGGINGFACE_SPACE_URL")

# Connect to MongoDB - let's hope the connection doesn't go on a coffee break
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['bot_db']
image_collection = db['images']

# Setup Gradio client - time to see if this AI can draw better than a stick figure
space_name = HUGGINGFACE_SPACE_URL.split('/')[-2] + '/' + HUGGINGFACE_SPACE_URL.split('/')[-1]
gradio_client = Client(space_name, hf_token=HF_TOKEN)

@contextmanager
def log_time(message):
    start = datetime.datetime.now()
    try:
        yield
    finally:
        end = datetime.datetime.now()
        duration = end - start
        logger.info(f"{message} took {duration.total_seconds():.2f} seconds")

@app.post("/generate_image")
async def generate_image_endpoint(request: Request):
    try:
        data = await request.json()
        prompt = data.get("prompt")
        if not prompt:
            logger.warning("No prompt provided. What are we supposed to do, draw blank pages?")
            return {"status": "error", "message": "No prompt provided"}

        logger.info(f"Generating image with prompt: {prompt}")
        
        with log_time("Image generation process"):
            # Generate image - hold on to your pixels, folks!
            job = gradio_client.submit(prompt, api_name="/generate")
            while not job.done():
                pass  # Wait for job to complete - patience, young grasshopper
            result = job.result()

        # Convert image to base64 for storage - because databases love text more than binary, apparently
        if hasattr(result, 'save'):  # If result is an image that can be saved
            logger.debug("Converting image to base64")
            buffered = BytesIO()
            result.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
        elif isinstance(result, str):  # If result is already a base64 string or URL
            logger.debug("Result is already a string, probably base64 or URL")
            img_str = result
        else:
            raise ValueError("Unexpected result format from Gradio")

        # Store in MongoDB - because we want to keep our art history for the digital age
        with log_time("MongoDB insertion"):
            image_collection.insert_one({
                "prompt": prompt,
                "image": img_str,
                "timestamp": datetime.datetime.utcnow()
            })

        logger.info("Image successfully generated and stored. We're on a roll here!")
        return {"status": "success", "message": "Boom! Image generated and stored like a boss."}

    except Exception as e:
        logger.error(f"Error in our grand image generation plan: {str(e)}")
        return {"status": "error", "message": f"Failed to generate image. AI took a nap: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on port {PORT}. Let's hope this goes better than the last time!")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
