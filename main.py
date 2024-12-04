# Filename: app.py

import logging
import sys
from gradio_client import Client
import os
import time
from typing import Any, Dict, Optional

# Configure logging to track the progress and any issues - because if it's not logged, did it even happen?
logging.basicConfig(
    level=logging.DEBUG,  # Set logging level to DEBUG for detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Print logs to console
        logging.FileHandler("gradio_client.log")  # Save logs to a file
    ]
)
logger = logging.getLogger(__name__)

def get_token() -> Optional[str]:
    """Retrieve the Hugging Face API token from environment variables."""
    token = os.getenv('HF_INTERMEDIARY_TOKEN')
    if not token:
        logger.error("HF_INTERMEDIARY_TOKEN is not set. Please set the environment variable in Space secrets.")
        sys.exit(1)  # Exit stage left—no token, no API calls!
    return token

def initialize_client(space_id: str, token: str) -> Client:
    """Initialize and return a Gradio Client instance."""
    try:
        logger.info(f"Initializing Gradio Client for space: {space_id}...")
        return Client(space_id, hf_token=token, timeout=60)  # Increased timeout for slower networks
    except Exception as e:
        logger.error(f"Failed to initialize Client: {e}")
        raise

def make_api_call(client: Client, endpoint: str, params: Dict[str, Any]) -> Any:
    """Make an API call using the Gradio Client."""
    try:
        logger.info(f"Making API call to {endpoint} endpoint with params: {params}")
        result = client.predict(**params)
        logger.info(f"API call successful. Result: {result}")
        return result
    except Exception as e:
        logger.error(f"API call failed: {e}")
        raise

def main():
    """Main function to run the Gradio client application."""
    logger.info("Starting Gradio Client application...")
    
    token = get_token()
    space_id = "Finitoshi/black-forest-labs-FLUX.1-schnell"
    endpoint = "/predict"
    params = {"param_0": "Hello!!"}  # Use a dictionary for parameters

    # Configuration for retry logic with exponential backoff - because we're not giving up that easily
    max_retries = 5  # Maximum attempts before throwing in the towel
    base_delay = 2  # Base delay in seconds for exponential backoff

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1} of {max_retries}...")
            client = initialize_client(space_id, token)
            result = make_api_call(client, endpoint, params)
            
            # Here's where we do something with the result - maybe save it, display it, or just celebrate
            if isinstance(result, dict) and 'image' in result:
                logger.info(f"Image URL or data: {result['image']}")
                # TODO: Implement saving or displaying the image here
            else:
                logger.info(f"Unexpected result format: {result}")
            
            break  # Success! Time for a break
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed after {max_retries} attempts. The API just doesn't like us today: {e}")
                raise
            delay = base_delay * (2 ** attempt)  # Exponential backoff
            logger.warning(f"Attempt {attempt + 1} failed. Retrying in {delay} seconds...")
            time.sleep(delay)

    logger.info("Gradio Client application ended. Now go grab a coffee, you've earned it!")

if __name__ == "__main__":
    main()
