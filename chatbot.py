from flask import Blueprint, jsonify, request
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Blueprint
chat = Blueprint('chat', __name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Define travel assistant context and sample responses
SAMPLE_RESPONSES = {
    'greetings': 'Hello! I am your Travel Assistant. How can I help you today?',
    'default': 'I understand you need help with travel planning. Could you please provide more specific details about what you need assistance with? I can help with trip planning, destinations, travel tips, or expense management.',
    'error': 'I apologize, but I am currently operating in a limited capacity. However, I can still provide basic travel assistance and information.',
    'expense': 'I can help you manage your travel expenses. You can add expenses, view your spending history, and manage group expenses through our platform.',
    'trip': 'Let me help you plan your trip. I can assist with destination recommendations, itinerary planning, and travel tips.',
    'help': 'I can help you with: \n1. Travel expense management\n2. Trip planning\n3. Group expense sharing\n4. Travel recommendations'
}

def get_gemini_response(message):
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            'contents': [{
                'parts': [{
                    'text': message
                }]
            }]
        }
        
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result:
                return result['candidates'][0]['content']['parts'][0]['text']
        return SAMPLE_RESPONSES['error']
    except Exception as e:
        print(f"Gemini API error: {str(e)}")
        return SAMPLE_RESPONSES['error']

@chat.route('/chat', methods=['POST'])
def handle_chat():
    try:
        # Validate request data
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        user_message = request.json.get('message')
        if not user_message or not isinstance(user_message, str):
            return jsonify({'error': 'Please provide a valid message'}), 400

        if len(user_message.strip()) == 0:
            return jsonify({'error': 'Message cannot be empty'}), 400

        # Get response from Gemini API
        response = get_gemini_response(user_message)

        return jsonify({
            'response': response
        })

    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred. Please try again later.'
        }), 500