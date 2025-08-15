# 🎙️ Gemini TTS Generator

A Flask web application that generates creative Instagram reel scripts using Google's Gemini AI and converts them to speech using text-to-speech technology.

## Features

- 🎵 Generate TTS audio from AI-generated scripts
- 📝 Extract keywords from generated content
- ⬇️ Real-time audio download
- 🎧 Built-in audio player
- 📁 File management for generated audio
- 📱 Responsive, modern UI

## Deployment on Render

### Prerequisites
- A Render account (free tier available)
- Google Gemini API key

### Deployment Steps

1. **Fork/Clone this repository** to your GitHub account

2. **Connect to Render:**
   - Log in to [Render](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

3. **Configure the deployment:**
   - **Name:** `gemini-tts-app` (or your preferred name)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT app:app`

4. **Set Environment Variables:**
   - In the Render dashboard, go to your service settings
   - Add environment variable:
     - **Key:** `GEMINI_API_KEY`
     - **Value:** Your Google Gemini API key

5. **Deploy:**
   - Click "Create Web Service"
   - Render will automatically deploy your app

### Getting Your Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Create a new API key
4. Copy the API key and add it to your Render environment variables

## Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API key** (optional for local dev - it's hardcoded for testing):
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Open your browser:**
   ```
   http://localhost:5000
   ```

## File Structure

```
gemini-voice/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── render.yaml        # Render deployment config
├── templates/
│   └── index.html     # Web interface
├── TTS.py            # Original TTS script (reference)
└── README.md         # This file
```

## API Endpoints

- `GET /` - Main web interface
- `POST /generate` - Generate new TTS audio
- `GET /download/<filename>` - Download audio file
- `GET /files` - List all generated files

## Notes

- Generated audio files are stored temporarily and may be cleaned up periodically on Render's free tier
- The application uses Google's Gemini AI for script generation and TTS
- Audio files are generated in WAV format

## Support

If you encounter any issues during deployment, check:
1. Your Gemini API key is correctly set in environment variables
2. All dependencies are properly installed
3. The Render logs for any error messages
