# intermediary/main.py

import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # This is for those cross-origin vibes
from gradio_client import Client
from pymongo import MongoClient
from io import BytesIO
import base64
import datetime
from contextlib import contextmanager

# Logging setup - because if you didn't log it, did it even happen, fam?
logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS middleware - for when you're trying to vibe from different domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You might wanna lock this down in prod, unless you're super chill
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables - keep your secrets on fleek
HF_TOKEN = os.getenv("HF_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
HUGGINGFACE_SPACE_URL = os.getenv("HUGGINGFACE_SPACE_URL")

# MongoDB connection - may the database be with you, young padawan
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['bot_db']
image_collection = db['images']

# Gradio client setup - fingers crossed this AI isn't just coloring outside the lines
space_name = HUGGINGFACE_SPACE_URL.split('/')[-2] + '/' + HUGGINGFACE_SPACE_URL.split('/')[-1]
gradio_client = Client(space_name, hf_token=HF_TOKEN)

# Performance timer - because even AI needs to know if it's slacking
@contextmanager
def log_time(message):
    start = datetime.datetime.now()
    try:
        yield
    finally:
        end = datetime.datetime.now()
        duration = end - start
        logger.info(f"{message} took {duration.total_seconds():.2f} seconds. That's like, one TikTok video in real life!")

# The main event - where we turn prompts into digital art, hopefully
@app.post("/predict")
async def predict_endpoint(request: Request):
    try:
        # Checkin' the vibes for what we're about to create
        data = await request.json()
        prompt = data.get("prompt")
        if not prompt:
            logger.warning("No prompt? Dude, you can't just yeet art into existence.")
            return JSONResponse(content={"status": "error", "message": "No prompt provided"}, status_code=400)

        logger.info(f"Generating image with prompt: {prompt}. Let's see if AI can make this lit.")
        
        with log_time("Image gen process"):
            # AI's art class - did it pay attention?
            job = gradio_client.submit(prompt, api_name="/predict")
            while not job.done():
                pass  # Patience, young grasshopper
            result = job.result()

        # Convert to base64 - because we're all about that text life, not binary
        if hasattr(result, 'save'):  # If it's an image, time to do some magic
            logger.debug("Converting image to base64. Here comes the tech wizardry!")
            buffered = BytesIO()
            result.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
        elif isinstance(result, str):  # If it's already a string, let's roll with it
            logger.debug("Result's already a string, fam. Less work for us, more time for memes!")
            img_str = result
        else:
            logger.error("Unexpected result format from Gradio. AI must've taken a nap during art class.")
            raise ValueError("Unexpected result format from Gradio")

        # Storing our digital masterpiece in MongoDB - for when we need to flex later
        with log_time("MongoDB insertion"):
            image_collection.insert_one({
                "prompt": prompt,
                "image": img_str,
                "timestamp": datetime.datetime.utcnow()
            })

        logger.info("Image successfully generated and stored. We're basically digital Van Goghs now!")
        return JSONResponse(content={"status": "success", "message": "Image generated and stored", "image": img_str}, status_code=200)

    except Exception as e:
        logger.error(f"Error in our artistic journey: {str(e)}. AI, you've let the team down, man.")
        return JSONResponse(content={"status": "error", "message": f"Failed to generate image: {str(e)}"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Default to 8000, 'cause why not live on the edge?
    logger.info(f"Server's starting on port {port}. Let's get this art party started!")
    uvicorn.run(app, host="0.0.0.0", port=port)
