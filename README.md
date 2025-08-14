# Gemini Voice TTS Web App

A modern web application that generates creative scripts using Google's Gemini AI and converts them to speech with real-time audio playback.

## Features

🎤 **AI-Powered Script Generation**: Generate creative, funny 30-second reel scripts
🔊 **Text-to-Speech**: Convert scripts to high-quality audio using Gemini TTS
🎯 **Keyword Extraction**: Automatically extract important keywords from generated content
🎨 **Modern UI**: Beautiful, responsive web interface with real-time audio controls
📱 **Mobile Friendly**: Works seamlessly on desktop and mobile devices

## Content Types

- **Random & Surprising Facts**: Historical, science-based, or internet trends
- **Humorous Mini-Stories**: Short, quirky fictional stories
- **Light Current Events**: Friendly takes on recent news or geopolitical events

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Key (Recommended)

For security, set your Gemini API key as an environment variable:

**Windows:**
```cmd
set GEMINI_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY=your_api_key_here
```

Alternatively, you can edit the API key directly in `app.py` (line 15).

### 3. Run the Application

```bash
python app.py
```

The app will be available at `http://localhost:5000`

## File Structure

```
gemini voice/
├── app.py                 # Flask backend server
├── TTS.py                 # Original TTS script (standalone)
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Web frontend
├── static/
│   └── audio/            # Generated audio files (created automatically)
└── README.md             # This file
```

## How It Works

1. **Script Generation**: Select a content type and click "Generate Script"
2. **AI Processing**: Gemini AI creates a creative script with stage directions and sound effects
3. **Keyword Extraction**: Important keywords are automatically extracted from the script
4. **Text-to-Speech**: The script is converted to audio using Gemini's TTS model
5. **Real-time Playback**: Listen to the generated audio with custom controls

## Features

- **Custom Audio Controls**: Play/pause, progress bar, time display
- **Responsive Design**: Works on all screen sizes
- **Error Handling**: User-friendly error messages
- **Loading States**: Visual feedback during generation
- **Keyword Tags**: Visual representation of important topics

## Technical Details

- **Backend**: Flask with Google Gemini AI API
- **Frontend**: Modern HTML5/CSS3/JavaScript
- **Audio**: WAV format, 24kHz sample rate
- **Voice**: Kore voice model from Gemini TTS
- **Security**: API key can be stored as environment variable

## API Endpoints

- `GET /` - Serves the main web interface
- `POST /generate` - Generates script, keywords, and audio
- `GET /static/audio/<filename>` - Serves generated audio files

Enjoy creating amazing voice content with AI! 🎉
