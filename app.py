import os
import re
from flask import Flask, request, render_template
from youtube_transcript_api import YouTubeTranscriptApi

import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

def extract_video_id(url: str) -> str:
    patterns = [r"v=([^&]+)", r"youtu\.be/([^?&]+)"]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    raise ValueError("url invalid...")

def fetch_transcript(video_id: str) -> str:
    segments = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
    return " ".join(seg["text"] for seg in segments)

def chunk_text(text: str, max_chars: int = 3000) -> list[str]:  
    sentences = re.split(r'(?<=[\.!?])\s+', text)  
    chunks, current = [], ""
    for s in sentences:
        if len(current) + len(s) + 1 > max_chars:  
            chunks.append(current.strip())
            current = s
        else:
            current += " " + s
    if current:
        chunks.append(current.strip())
    return chunks  

def summarize_recipe(transcript: str) -> str:
    chunks = chunk_text(transcript)
    full_recipe = ""
    for i, chunk in enumerate(chunks):
        if i == 0:
            prompt = (
                " You are a cooking assistant. From the following cooking video transcript, extract a clear recipe:\n\n"
                f"{chunk}\n\n"
                "## Ingredients\n- ...\n\n## Steps\n1. ...")
        else:
            prompt = (
                "Continue refining the same recipe using this transcript chunk—"
                "add any new ingredients or steps without repeating:\n\n"
                f"{chunk}"
            )
        
        resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        full_recipe += resp.choices[0].message.content.strip() + "\n\n"

    return full_recipe.strip()

@app.route("/", methods=["GET", "POST"])
def index():
    recipe = None
    error = None
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        try:
            vid = extract_video_id(url)
            transcript = fetch_transcript(vid)
            recipe = summarize_recipe(transcript)
        except Exception as e:
            error = str(e)
    return render_template("index.html", recipe=recipe, error=error)

if __name__ == "__main__":
    app.run(debug=True)
