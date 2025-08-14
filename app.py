from flask import Flask, render_template, request, jsonify, send_file
from google import genai
from google.genai import types
import wave
import re
import os
import uuid
import json
from collections import Counter
from flask_cors import CORS
import tempfile
import base64

app = Flask(__name__)
CORS(app)

# Initialize Gemini client
# Move your API key to environment variable for security
API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyBMi7RqQdtvSjqGJFKePfEuAmbojFksIcc')
client = genai.Client(api_key=API_KEY)

def extract_keywords(text, top_n=10):
    """Extract the most important keywords from the generated text"""
    cleaned_text = text.lower()
    
    # Remove content in parentheses (stage directions)
    cleaned_text = re.sub(r'\([^)]*\)', '', cleaned_text)
    
    # Remove content in square brackets (sound effects)
    cleaned_text = re.sub(r'\[[^\]]*\]', '', cleaned_text)
    
    # Remove common phrases from the prompt
    stop_phrases = ['speech speed should be 5x', 'voiceover:', 'generate', 'script']
    for phrase in stop_phrases:
        cleaned_text = cleaned_text.replace(phrase, '')
    
    # Split into words and filter
    words = re.findall(r'\b[a-zA-Z]{3,}\b', cleaned_text)
    
    # Common stop words to exclude
    stop_words = {
        'the', 'and', 'you', 'that', 'was', 'for', 'are', 'with', 'his', 'they',
        'this', 'have', 'from', 'one', 'had', 'word', 'but', 'not', 'what',
        'all', 'were', 'when', 'your', 'can', 'said', 'there', 'each', 'which',
        'she', 'how', 'will', 'about', 'out', 'many', 'then', 'them', 'these',
        'has', 'her', 'would', 'make', 'like', 'him', 'into', 'time', 'two',
        'more', 'very', 'after', 'words', 'long', 'than', 'way', 'been',
        'its', 'who', 'did', 'get', 'may', 'day', 'use', 'man', 'new', 'now',
        'old', 'see', 'come', 'could', 'people', 'just', 'know', 'take', 'year'
    }
    
    # Filter out stop words and count frequency
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
    word_counts = Counter(filtered_words)
    
    # Get top keywords
    keywords = [word for word, count in word_counts.most_common(top_n)]
    
    return keywords

def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    """Save PCM data as WAV file"""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_content():
    """Generate script, keywords, and audio"""
    try:
        data = request.get_json()
        topic_type = data.get('topic', 'random_facts')
        
        # Customize the prompt based on topic selection
        topic_prompts = {
            'random_facts': 'A list of random, surprising, or weird facts (could be historical, science-based, or internet trends).',
            'mini_story': 'A short, humorous and quirky fictional mini-story.',
            'geopolitical': 'A light, curious, and slightly funny take on a recent geopolitical event or news trend (must be non-offensive and friendly).'
        }
        
        selected_topic = topic_prompts.get(topic_type, topic_prompts['random_facts'])
        
        # Generate script content
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
Generate a short, creative, and funny 30-second reel script in a curious tone for speech generation for a fast-paced Instagram reel. 
add "Speech speed should be 5x" in every output.
The script must ONLY be about: {selected_topic}

The script should be formatted for a VOICEOVER with stage directions in parentheses (e.g., (soft laugh), (pause), (playful chuckle)) to indicate emotions, pauses, and tone shifts. 
Include SOUND EFFECT suggestions in ALL CAPS inside square brackets [e.g., [BEEP], [WAVES], [DRUM ROLL]] wherever relevant for comedic or dramatic effect.

Style rules:
- Humor should be light, friendly, and relatable—similar to casual Instagram reel background audio.
- Can reference recent internet memes, viral trends, or pop culture moments if relevant to the topic.
- Maintain natural pauses, laughter cues, and changes in tone.
- Keep it around 80–120 words so it fits in ~30 seconds.
- Always open with a hook that makes people curious.

Example:
(Playful chuckle)  
Voiceover: You know octopuses have three hearts… (pause) and two of them stop beating when they swim?  
[LITTLE SPLASH SOUND]  
Voiceover: Yeah… so basically, cardio day is a literal heartbreaker for them. (laugh)

Now, generate the script.
"""
        )
        
        generated_text = response.text
        keywords_list = extract_keywords(generated_text)
        
        # Generate audio from text
        audio_response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=generated_text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name='Kore',
                        )
                    )
                ),
            )
        )
        
        # Get audio data
        audio_data = audio_response.candidates[0].content.parts[0].inline_data.data
        
        # Generate unique filename
        audio_filename = f"audio_{uuid.uuid4().hex[:8]}.wav"
        audio_path = os.path.join('static', 'audio', audio_filename)
        
        # Ensure audio directory exists
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        
        # Save audio file
        wave_file(audio_path, audio_data)
        
        return jsonify({
            'success': True,
            'script': generated_text,
            'keywords': keywords_list,
            'audio_url': f'/static/audio/{audio_filename}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/static/audio/<filename>')
def serve_audio(filename):
    """Serve audio files"""
    return send_file(os.path.join('static', 'audio', filename))

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static/audio', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Use PORT environment variable for deployment compatibility
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(debug=debug, host='0.0.0.0', port=port)
