from flask import Flask, render_template, request, jsonify, send_file
from google import genai
from google.genai import types
import wave
import re
from collections import Counter
import os
import datetime
import uuid

app = Flask(__name__)

# Gemini client
client = genai.Client(api_key="AIzaSyBMi7RqQdtvSjqGJFKePfEuAmbojFksIcc")

def extract_keywords(text, top_n=10):
    """
    Extract the most important keywords from the generated text
    """
    # Clean the text: remove stage directions, sound effects, and common words
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
    """Save PCM data to a wave file"""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def generate_tts_script_and_audio(topic_option=None, custom_prompt=None):
    """Generate TTS script and audio, return script, keywords, and filename"""
    
    # Base prompt for script generation
    base_prompt = """
Generate a short, creative, and funny 30-second reel script in a curious tone for speech generation for a fast-paced Instagram reel. 
add "Speech speed should be 5x" in every output.
The script must ONLY be about ONE of the following topics:
1. A list of random, surprising, or weird facts (could be historical, science-based, or internet trends).
2. A short, humorous and quirky fictional mini-story.
3. A light, curious, and slightly funny take on a recent geopolitical event or news trend (must be non-offensive and friendly).

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
    
    # Use custom prompt if provided, otherwise use base prompt
    prompt = custom_prompt if custom_prompt else base_prompt
    
    # Generate script
    script_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    generated_text = script_response.text
    keywords_list = extract_keywords(generated_text)
    
    # Generate TTS audio
    tts_response = client.models.generate_content(
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
    audio_data = tts_response.candidates[0].content.parts[0].inline_data.data
    
    # Create unique filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tts_audio_{timestamp}_{uuid.uuid4().hex[:8]}.wav"
    
    # Save audio file
    wave_file(filename, audio_data)
    
    return {
        'script': generated_text,
        'keywords': keywords_list,
        'filename': filename,
        'success': True
    }

@app.route('/')
def index():
    """Main page with TTS interface"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_audio():
    """Generate TTS audio and return details"""
    try:
        data = request.get_json()
        custom_prompt = data.get('custom_prompt', '')
        
        # Generate TTS
        result = generate_tts_script_and_audio(custom_prompt=custom_prompt if custom_prompt else None)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/download/<filename>')
def download_audio(filename):
    """Download the generated audio file"""
    try:
        if os.path.exists(filename):
            return send_file(filename, as_attachment=True, download_name=filename)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/files')
def list_files():
    """List all generated audio files"""
    try:
        audio_files = [f for f in os.listdir('.') if f.startswith('tts_audio_') and f.endswith('.wav')]
        audio_files.sort(reverse=True)  # Most recent first
        return jsonify({'files': audio_files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
