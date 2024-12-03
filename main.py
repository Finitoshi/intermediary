# src/main.py

import os
from fastapi import FastAPI, Request
from gradio_client import Client
from pymongo import MongoClient
from io import BytesIO
import base64
import datetime

app = FastAPI()

# Directly access environment variables
HF_TOKEN = os.getenv("HF_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 8000))  # Default to 8000 if PORT is not set
HUGGINGFACE_SPACE_URL = os.getenv("HUGGINGFACE_SPACE_URL")

# Connect to MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['bot_db']
image_collection = db['images']

# Setup Gradio client
gradio_client = Client(HUGGINGFACE_SPACE_URL.split('/')[-1], hf_token=HF_TOKEN)

@app.post("/generate_image")
async def generate_image_endpoint(request: Request):
    try:
        data = await request.json()
        prompt = data.get("prompt")
        if not prompt:
            return {"status": "error", "message": "No prompt provided, what are we supposed to do, draw blank pages?"}

        # Generate image
        job = gradio_client.submit(prompt, api_name="/generate")
        while not job.done():
            pass  # Wait for job to complete
        result = job.result()

        # Convert image to base64 for storage
        if hasattr(result, 'save'):  # If result is an image that can be saved
            buffered = BytesIO()
            result.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
        elif isinstance(result, str):  # If result is already a base64 string or URL
            img_str = result
        else:
            raise ValueError("Unexpected result format from Gradio")

        # Store in MongoDB
        image_collection.insert_one({
            "prompt": prompt,
            "image": img_str,
            "timestamp": datetime.datetime.utcnow()
        })

        return {"status": "success", "message": "Boom! Image generated and stored like a boss."}

    except Exception as e:
        print(f"Error in our grand image generation plan: {str(e)}")
        return {"status": "error", "message": f"Failed to generate image. AI took a nap: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
