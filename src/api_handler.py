# api_handler.py
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate_nft():
    prompt = request.json.get('prompt')
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    
    # URL for your Hugging Face Space
    space_url = "YOUR_HUGGING_FACE_SPACE_URL/generate"  # e.g., 'https://finitoshi-chibi-bfl-flux-1-schnell.hf.space/generate'
    
    # Make a request to the Hugging Face Space
    response = requests.post(space_url, json={'prompt': prompt})
    
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to generate NFT"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Port should match what Render.com expects
