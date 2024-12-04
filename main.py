# intermediary/main.py

import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # Added for CORS handling
from gradio_client import Client
from pymongo import MongoClient
from io import BytesIO
import base64
import datetime
from contextlib import contextmanager
import json

# Configure logging - because if it's not logged, did it really happen?
logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS middleware - to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You might want to restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables - 'cause we like to keep secrets secret
HF_TOKEN = os.getenv("HF_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
HUGGINGFACE_SPACE_URL = os.getenv("HUGGINGFACE_SPACE_URL")
HF_INTERMEDIARY_TOKEN = os.getenv("HF_INTERMEDIARY_TOKEN")

# ... other code ...

# Setup Gradio client
space_name = HUGGINGFACE_SPACE_URL.split('/')[-2] + '/' + HUGGINGFACE_SPACE_URL.split('/')[-1]
gradio_client = Client(space_name, hf_token=HF_INTERMEDIARY_TOKEN)

# Log environment variable status
logger.info(f"Environment variables loaded: HF_TOKEN={HF_TOKEN is not None}, MONGO_URI={MONGO_URI is not None}, HUGGINGFACE_SPACE_URL={HUGGINGFACE_SPACE_URL is not None}")

# Connect to MongoDB - may the database be with you
mongo_client = MongoClient(MONGO_URI)
try:
    mongo_client.admin.command('ping')
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")

db = mongo_client['bot_db']
image_collection = db['images']

# Setup Gradio client
space_name = HUGGINGFACE_SPACE_URL.split('/')[-2] + '/' + HUGGINGFACE_SPACE_URL.split('/')[-1]
gradio_client = Client(space_name, hf_token=HF_INTERMEDIARY_TOKEN)

# Here's a little time tracker - because even AI needs performance reviews
@contextmanager
def log_time(message):
    start = datetime.datetime.now()
    try:
        yield
    finally:
        end = datetime.datetime.now()
        duration = end - start
        logger.info(f"{message} took {duration.total_seconds():.2f} seconds. That's like, what, a blink in internet time?")

# Update this endpoint to match Gradio's expected API
@app.post("/predict")
async def predict_endpoint(request: Request):
    try:
        # Log request details
        logger.debug(f"Received request: {request.method} {request.url}")
        
        # Checkin' the vibes for what we're about to create
        data = await request.json()
        logger.debug(f"Request body: {json.dumps(data)}")
        prompt = data.get("prompt")
        if not prompt:
            logger.warning("No prompt provided. We can't make art from nothing, you know.")
            return JSONResponse(content={"status": "error", "message": "No prompt provided"}, status_code=400)

        logger.info(f"Generating image with prompt: {prompt}. Let's see if AI can be the next Picasso.")
        
        with log_time("Image generation process"):
            # Generate image - let's hope AI got its art degree
            job = gradio_client.submit(prompt, api_name="/predict")
            while not job.done():
                pass  # Wait for job to complete - patience is a virtue
            result = job.result()
        
        # Log Gradio job status
        logger.debug(f"Gradio job status: {job.status()}")

        # Convert image to base64 for storage - because we love text more than binary in databases
        if hasattr(result, 'save'):  # If result is an image that can be saved
            logger.debug("Converting image to base64. Here comes the digital magic!")
            buffered = BytesIO()
            result.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
        elif isinstance(result, str):  # If result is already a base64 string or URL
            logger.debug("Result is already a string, probably base64 or URL. AI, you've made my job easier!")
            img_str = result
        else:
            logger.error("Unexpected result format from Gradio. Did AI forget how to draw?")
            raise ValueError("Unexpected result format from Gradio")

        # Store in MongoDB - because we want to remember our masterpieces
        with log_time("MongoDB insertion"):
            result = image_collection.insert_one({
                "prompt": prompt,
                "image": img_str,
                "timestamp": datetime.datetime.utcnow()
            })
            logger.info(f"Inserted document with ID: {result.inserted_id}")

        logger.info("Image successfully generated and stored. Art for the future!")
        return JSONResponse(content={"status": "success", "message": "Image generated and stored", "image": img_str}, status_code=200)

    except Exception as e:
        import traceback
        logger.error(f"Error in our grand image generation plan: {str(e)}. AI, you've let us down!")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return JSONResponse(content={"status": "error", "message": f"Failed to generate image: {str(e)}"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Default to 8000 if PORT is not set, 'cause we're flexible like that
    logger.info(f"Starting server on port {port}. Let's see some art!")
    uvicorn.run(app, host="0.0.0.0", port=port)
