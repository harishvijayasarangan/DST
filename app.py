from flask import Flask, render_template, request, jsonify, abort
import json
from typing import Dict, Any
import os
import logging
from groq import query_groq

app = Flask(__name__, 
    static_folder='static',   
    template_folder='templates' 
)


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
        groq_model = request.form.get("groq_model", "gemma2-9b-it").strip()  # Default to gemma2-9b-it
        return jsonify(get_groq_response(msg, groq_model))
    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify("An error occurred while processing your request")

def get_groq_response(prompt: str, model: str = "gemma2-9b-it") -> str:
    try:
        # Use the system prompt for DST Bot
        system_prompt = "You are DST Bot, a customer chatbot for Digital Scent Technology.\nUser question: "
        full_prompt = system_prompt + prompt
        
        # Call the Groq API using the imported function
        ai_response = query_groq(full_prompt, model)
        
        history.append({
            "user": prompt,
            "ai": ai_response,
            "model": f"Groq ({model})"
        })
        
        return ai_response
    except Exception as e:
        app.logger.error(f"Error in Groq API call: {str(e)}")
        return "An error occurred with the Groq API. Please try again."

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
    logging.basicConfig(level=logging.DEBUG)
    
    # Verify template and static directories exist
    if not os.path.exists('templates'):
        app.logger.error("Templates directory not found!")
        exit(1)
    if not os.path.exists('static'):
        app.logger.error("Static directory not found!")
        exit(1)
        
    # Use port 7860 for Hugging Face Spaces compatibility
    app.run(host='0.0.0.0', port=7860, debug=False)
