from flask import Flask, render_template, request, jsonify, abort
import base64
import requests
import json
from typing import Dict, Any
import os
import pytesseract
from PIL import Image
import io
import re

app = Flask(__name__, 
    static_folder='static',    # Explicitly set static folder
    template_folder='templates' # Explicitly set template folder
)

# Chatbot Configuration
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
MAX_IMAGE_SIZE = 10 * 1024 * 1024
MODEL_NAME = "llama3.2-vision:latest"
REQUEST_TIMEOUT = 60

# Initialize conversation history
history: list = []

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Error rendering template: {str(e)}")
        abort(500)

@app.route("/get", methods=["POST"])
def chat():
    try:
        msg = request.form.get("msg", "").strip()
        image = request.files.get("image")
        pasted_image_data = request.form.get("pasted_image")
        
        prompt_data = {
            "model": MODEL_NAME,
            "prompt": msg,
            "stream": False
        }
        
        has_image = bool(pasted_image_data or image)
        
        if pasted_image_data:
            app.logger.debug("Processing pasted image data.")
            image_data = re.sub('^data:image/.+;base64,', '', pasted_image_data)
            image_bytes = base64.b64decode(image_data)
            
            if len(image_bytes) > MAX_IMAGE_SIZE:
                return jsonify("Image size too large. Please upload an image smaller than 10MB")
            
            image_pil = Image.open(io.BytesIO(image_bytes))
            extracted_text = pytesseract.image_to_string(image_pil)
            app.logger.debug(f"Extracted text from pasted image: {extracted_text}")
            
            # Check for "delta p", "delta f", and "delta c" in the extracted text
            extracted_text_lower = extracted_text.lower()
            if "delta p" in extracted_text_lower or "deltap" in extracted_text_lower:
                return jsonify("perfume")
            elif "delta f" in extracted_text_lower or "deltaf" in extracted_text_lower:
                return jsonify("flower")
            elif "delta c" in extracted_text_lower or "deltac" in extracted_text_lower:
                return jsonify("coffee")
            
            prompt_data["prompt"] += f"\nExtracted Text: {extracted_text}"
            prompt_data["images"] = [image_data]
            
        elif image:
            app.logger.debug("Processing uploaded image file.")
            image.seek(0, 2)
            size = image.tell()
            if size > MAX_IMAGE_SIZE:
                return jsonify("Image size too large. Please upload an image smaller than 10MB")
            
            image.seek(0)
            
            if not image.content_type.startswith('image/'):
                return jsonify("Invalid file type. Please upload an image file")
            
            # Convert image to text using OCR
            image_data = image.read()
            image_pil = Image.open(io.BytesIO(image_data))
            extracted_text = pytesseract.image_to_string(image_pil)
            app.logger.debug(f"Extracted text from uploaded image: {extracted_text}")
            
            # Check for "delta p", "delta f", and "delta c" in the extracted text
            extracted_text_lower = extracted_text.lower()
            if "delta p" in extracted_text_lower or "deltap" in extracted_text_lower:
                return jsonify("perfume")
            elif "delta f" in extracted_text_lower or "deltaf" in extracted_text_lower:
                return jsonify("flower")
            elif "delta c" in extracted_text_lower or "deltac" in extracted_text_lower:
                return jsonify("coffee")
            
            # Add extracted text to prompt data
            prompt_data["prompt"] += f"\nExtracted Text: {extracted_text}"
            prompt_data["images"] = [base64.b64encode(image_data).decode('utf-8')]

        return jsonify(get_chat_response(prompt_data, has_image))

    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify("An error occurred while processing your request")

def get_chat_response(prompt_data: Dict[str, Any], has_image: bool) -> str:
    try:
        # Determine the system prompt based on the presence of an image
        if has_image:
            system_prompt = (
                "You are DST Bot, a helpful assistant. "
                "You will be given either an image to analyze. "
                "Always look for the letter near delta. "
                "If that letter is P, respond with 'perfume'. "
                "If the letter is F, respond with 'flower'. "
                "If the letter is C, respond with 'coffee'. "
            )
        else:
            system_prompt = (
                "You are DST Bot, a customer chatbot for Digital Scent Technology.\n"
                "User question: "
            )
        
        prompt_data['prompt'] = system_prompt + prompt_data['prompt']
        
        response = requests.post(
            OLLAMA_ENDPOINT, 
            json=prompt_data,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code != 200:
            app.logger.error(f"Ollama error: {response.text}")
            return "Error: Unable to get response from Ollama. Please try again."

        response_data = response.json()
        ai_response = response_data.get('response', 'Sorry, I could not process that.')
        
        history.append({
            "user": prompt_data['prompt'],
            "ai": ai_response
        })
        
        return ai_response

    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama. Please make sure it's running."
    except requests.exceptions.Timeout:
        return "Error: The request took too long to process. Please try with a smaller image or try again."
    except Exception as e:
        app.logger.error(f"Unexpected error in get_chat_response: {str(e)}")
        return "An unexpected error occurred. Please try again."

# Add error handlers
@app.errorhandler(403)
def forbidden_error(error):
    app.logger.error(f"403 error: {error}")
    return render_template('index.html'), 403

@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f"404 error: {error}")
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"500 error: {error}")
    return render_template('index.html'), 500

if __name__ == '__main__':
    # Enable debug logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Check if Ollama is installed
    if os.system("which ollama >/dev/null 2>&1") != 0:
        app.logger.warning("Ollama is not installed. Please install it first.")
        app.logger.warning("You can install it using: curl https://ollama.ai/install.sh | sh")
    
    # Verify template and static directories exist
    if not os.path.exists('templates'):
        app.logger.error("Templates directory not found!")
        exit(1)
    if not os.path.exists('static'):
        app.logger.error("Static directory not found!")
        exit(1)
        
    app.run(debug=True, port=5000)
