# src/main.py

import os
from fastapi import FastAPI, Request
from config import HF_TOKEN, MONGO_URI, PORT, HUGGINGFACE_SPACE_URL
from .database import connect_to_mongo, store_image
from .gradio_handler import setup_gradio_client, generate_image

app = FastAPI()

# Connect to our digital art gallery
mongo_client = connect_to_mongo(MONGO_URI)

# Fire up the image wizard
gradio_client = setup_gradio_client(HUGGINGFACE_SPACE_URL.split('/')[-1], HF_TOKEN)  # Use the name from the URL

@app.post("/generate_image")
async def generate_image_endpoint(request: Request):
    try:
        data = await request.json()
        prompt = data.get("prompt")
        if not prompt:
            return {"status": "error", "message": "No prompt provided, what are we supposed to do, draw blank pages?"}

        # Go fetch that image from the magic land of AI
        image_data = generate_image(gradio_client, prompt)
        
        # Store it for posterity or until the next server restart, whichever comes first
        store_image(mongo_client, prompt, image_data)

        return {"status": "success", "message": "Boom! Image generated and stored like a boss."}

    except Exception as e:
        # Log the error because we're not about to let this fly under the radar
        print(f"Error in our grand image generation plan: {str(e)}")
        return {"status": "error", "message": f"Failed to generate image. AI took a nap: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)  # Let's start this party on all interfaces, why not?
