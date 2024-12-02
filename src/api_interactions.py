import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

# Step 4: API interactions - 'cause we're all about that efficiency, no buffering

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))  # Retry 3 times with 2-second wait
async def query_grok(message):
    cached_response = cache_collection.find_one({
        "message": message,
        "cached_at": {"$gte": datetime.utcnow() - timedelta(seconds=60)}
    })

    if cached_response:
        logger.info("Returning cached response. We're all about that low-latency life.")
        return cached_response['response']

    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {"role": "system", "content": "You are Grok, a chatbot inspired by the Hitchhiker's Guide to the Galaxy."},
            {"role": "user", "content": message}
        ],
        "model": "grok-beta",
        "stream": False,
        "temperature": 0
    }
    logger.info(f"Sending to Grok API: {payload}. Let's see if Grok's feeling chatty today.")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:  # Give Grok a full minute to respond, patience is key
            response = await client.post(GROK_API_URL, headers=headers, json=payload)
            logger.info(f"Received response from Grok API: Status code {response.status_code}")
            
            response.raise_for_status()  # This will raise an error for HTTP errors
            response_data = response.json()
            
            grok_response = response_data.get('choices', [{}])[0].get('message', {}).get('content', "Grok did not respond properly. Guess AI has its off days too.")
            
            # Cache the response
            cache_data = {
                "message": message,
                "response": grok_response,
                "cached_at": datetime.utcnow()
            }
            cache_collection.insert_one(cache_data)
            return grok_response
    except httpx.HTTPStatusError as e:
        logger.error(f"Grok API HTTP error: Status code {e.response.status_code}, Response: {e.response.text}. That's not very Grok of you!")
        return "An error occurred while querying Grok. #AIProblems"
    except httpx.ReadTimeout:
        logger.error("Grok API request timed out. Grok must be on a coffee break.")
        return "Sorry, I'm taking longer than usual to respond. Try again in a bit?"
    except Exception as e:
        logger.error(f"Unexpected error with Grok API: {e}. Grok's gone rogue!")
        return "An unexpected error occurred. Grok's taking a nap, I guess."

async def query_grok_vision(message):
    # Setup for vision model - similar to query_grok but for vision capabilities
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {"role": "system", "content": "You are Grok with vision capabilities."},
            {"role": "user", "content": message}
        ],
        "model": "grok-vision-beta",
        # Add any vision-specific parameters here
    }
    # Implement the rest similar to query_grok
    # ...
