# src/gradio_handler.py

from gradio_client import Client
import os

# Let's get the Gradio party started
def setup_gradio_client(space_name, hf_token):
    return Client(space_name, hf_token=hf_token)

# Generate the image - because who doesn't want to see their words come to life?
def generate_image(client, prompt):
    job = client.submit(prompt, api_name="/generate")
    while not job.done():
        # Waiting like we're on hold with customer service
        pass
    result = job.result()
    
    # Convert the image to something we can store - because pixels are hard to keep in a database
    if hasattr(result, 'save'):
        buffered = BytesIO()
        result.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    elif isinstance(result, str):  # Already base64 or URL
        return result
    else:
        raise ValueError("Image format from Gradio isn't what we expected!")
