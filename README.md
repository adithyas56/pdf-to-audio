# 📚 PDF to Audio

A free, open-source web app that converts any PDF book into audio — no API keys, no cost, completely free.

🔗 **Live Demo:** https://pdf-to-audio-8q5u.onrender.com

## Features
- 📤 Upload any PDF book
- 🔊 Text-to-speech using browser's built-in voice engine
- 📑 Auto chapter detection
- 🔖 Bookmark your position
- 📝 Add notes while listening
- ⚡ Speed control (0.5x to 2x)
- 💾 Library saves all your books

## Tech Stack
- **Backend:** Python, FastAPI
- **Database:** SQLite
- **TTS:** Web Speech API (free, built into browser)
- **PDF Processing:** PyMuPDF
- **Hosting:** Render.com (free tier)

## Run Locally
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
Then open http://localhost:8000

## Deploy
Deployed on Render.com — [Live Demo](https://pdf-to-audio-8q5u.onrender.com)
