from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'response': 'Please enter a message.'}), 400
    
    try:
        # Call the local API for LLaMA-3
        response = requests.post('http://127.0.0.1:5000/generate', json={'message': user_message})
        response_json = response.json()
        
        if response.status_code != 200 or 'response' not in response_json:
            raise ValueError(f"Unexpected response: {response.text}")
        
        bot_response = response_json.get('response', 'Sorry, I did not understand that.')
    except Exception as e:
        bot_response = f"Error: {str(e)}"
    
    return jsonify({'response': bot_response})

if __name__ == '__main__':
    app.run(debug=True)
