# src/database.py

from pymongo import MongoClient
from datetime import datetime
import base64
from io import BytesIO

# Connect to MongoDB - because we need somewhere to dump all this digital art
def connect_to_mongo(uri):
    client = MongoClient(uri)
    return client['bot_db']

# Store that sweet, sweet image data
def store_image(client, prompt, image):
    db = client['bot_db']
    image_collection = db['images']
    image_collection.insert_one({
        "prompt": prompt,
        "image": image,  # Assuming image is already base64 encoded string
        "timestamp": datetime.utcnow()
    })
