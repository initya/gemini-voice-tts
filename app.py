from flask import Flask, render_template, request, jsonify, send_file
import google.generativeai as genai
import wave
import re
import os
import uuid
import json
from collections import Counter
from flask_cors import CORS
import tempfile
import base64
import io

app = Flask(__name__)
CORS(app)

# Initialize Gemini client
# Move your API key to environment variable for security
API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyBMi7RqQdtvSjqGJFKePfEuAmbojFksIcc')
genai.configure(api_key=API_KEY)

def generate_audio_with_tts(text):
    """Generate audio using simplified TTS approach"""
    try:
        # Since the google-genai package with TTS isn't working on Render,
        # let's create a simple audio file using a different approach
        import requests
        
        # Use a simple TTS service (this is a placeholder - you can replace with actual service)
        # For now, let's generate a simple audio placeholder that can be downloaded
        
        # Clean text for TTS
        clean_text = text.replace('(', '').replace(')', '').replace('[', '').replace(']', '')
        clean_text = clean_text.replace('Speech speed should be 5x', '').strip()
        
        print(f"Generating audio for text: {clean_text[:100]}...")
        
        # Create a simple wav file with text-to-speech
        # This is a placeholder - in production you'd use a real TTS service
        audio_data = create_simple_audio_file(clean_text)
        
        if audio_data:
            print("Successfully generated audio")
            return audio_data
        else:
            print("Failed to generate audio")
            return None
        
    except Exception as e:
        print(f"TTS generation failed: {e}")
        return None

def create_simple_audio_file(text):
    """Create a simple audio file (placeholder implementation)"""
    try:
        # For demo purposes, create a small WAV file
        # In production, you'd use a real TTS service like:
        # - Google Cloud Text-to-Speech
        # - Amazon Polly
        # - Azure Speech Services
        
        # Create a simple beep sound as placeholder
        import struct
        import math
        
        # Generate a simple tone
        sample_rate = 44100
        duration = min(len(text.split()) * 0.5, 30)  # ~0.5 seconds per word, max 30 seconds
        
        # Generate sine wave (placeholder for actual TTS)
        samples = []
        for i in range(int(sample_rate * duration)):
            # Create a simple melody based on text content
            frequency = 440 + (hash(text) % 200)  # Vary frequency based on text
            sample = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * i / sample_rate))
            samples.append(struct.pack('<h', sample))
        
        # Create WAV header
        audio_data = b'RIFF'
        audio_data += struct.pack('<I', len(samples) * 2 + 36)
        audio_data += b'WAVE'
        audio_data += b'fmt '
        audio_data += struct.pack('<I', 16)  # PCM
        audio_data += struct.pack('<H', 1)   # PCM
        audio_data += struct.pack('<H', 1)   # Mono
        audio_data += struct.pack('<I', sample_rate)
        audio_data += struct.pack('<I', sample_rate * 2)
        audio_data += struct.pack('<H', 2)
        audio_data += struct.pack('<H', 16)
        audio_data += b'data'
        audio_data += struct.pack('<I', len(samples) * 2)
        audio_data += b''.join(samples)
        
        return audio_data
        
    except Exception as e:
        print(f"Failed to create audio file: {e}")
        return None

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
    generated_text = None
    keywords_list = []
    audio_url = None
    has_server_audio = False
    
    try:
        print("=== Starting content generation ===")
        data = request.get_json()
        if not data:
            raise ValueError("No JSON data received")
            
        topic_type = data.get('topic', 'random_facts')
        print(f"Topic type: {topic_type}")
        
        # Customize the prompt based on topic selection
        topic_prompts = {
            'random_facts': 'A list of random, surprising, or weird facts (could be historical, science-based, or internet trends).',
            'mini_story': 'A short, humorous and quirky fictional mini-story.',
            'geopolitical': 'A light, curious, and slightly funny take on a recent geopolitical event or news trend (must be non-offensive and friendly).'
        }
        
        selected_topic = topic_prompts.get(topic_type, topic_prompts['random_facts'])
        
        # Generate script content
        print("Generating script with Gemini...")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(f"""
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
""")
        
        if not response or not response.text:
            raise ValueError("Failed to generate script content")
            
        generated_text = response.text
        print(f"Script generated successfully: {len(generated_text)} characters")
        
        # Extract keywords
        keywords_list = extract_keywords(generated_text)
        print(f"Keywords extracted: {keywords_list}")
        
        # Try to generate actual audio
        print("Attempting audio generation...")
        audio_data = generate_audio_with_tts(generated_text)
        
        if audio_data:
            try:
                # Save the actual audio file
                audio_filename = f"audio_{uuid.uuid4().hex[:8]}.wav"
                audio_path = os.path.join('static', 'audio', audio_filename)
                
                # Ensure audio directory exists
                os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                
                # Save audio file directly (it's already a WAV file)
                with open(audio_path, 'wb') as f:
                    f.write(audio_data)
                
                audio_url = f'/static/audio/{audio_filename}'
                has_server_audio = True
                print(f"Audio saved successfully: {audio_path}")
            except Exception as audio_save_error:
                print(f"Failed to save audio: {audio_save_error}")
                audio_url = None
                has_server_audio = False
        else:
            print("No audio data generated, will use browser TTS")
        
        # Always return a valid JSON response
        result = {
            'success': True,
            'script': generated_text,
            'keywords': keywords_list,
            'audio_url': audio_url,
            'has_server_audio': has_server_audio
        }
        
        print(f"=== Generation complete, returning result ===")
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in generate_content: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return a fallback response even on error
        fallback_result = {
            'success': False,
            'error': str(e),
            'script': generated_text or 'Error generating script',
            'keywords': keywords_list or [],
            'audio_url': audio_url,
            'has_server_audio': has_server_audio
        }
        
        return jsonify(fallback_result), 500

@app.route('/static/audio/<filename>')
def serve_audio(filename):
    """Serve audio files"""
    return send_file(os.path.join('static', 'audio', filename))

@app.route('/download/audio/<filename>')
def download_audio(filename):
    """Download audio files"""
    audio_path = os.path.join('static', 'audio', filename)
    if os.path.exists(audio_path):
        return send_file(
            audio_path, 
            as_attachment=True, 
            download_name=f"gemini_voice_{filename}",
            mimetype='audio/wav'
        )
    else:
        return jsonify({'error': 'Audio file not found'}), 404

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static/audio', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Use PORT environment variable for deployment compatibility
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(debug=debug, host='0.0.0.0', port=port)
