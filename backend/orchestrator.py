"""
orchestrator.py · FastAPI backend for YouTube-AI dashboard
"""

from __future__ import annotations
import os, re, json, base64, io, asyncio
from datetime import datetime
from typing import Dict, Any

from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# ────── OpenAI (new SDK) ─────────────────────────────────────
from openai import AsyncOpenAI          # ✅ NEW import

# ────── Google Gemini (optional) & others ───────────────────
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# NLP & plotting
import nltk, matplotlib.pyplot as plt
from nltk.corpus import stopwords
from wordcloud import WordCloud

# ────── Env & keys ──────────────────────────────────────────
load_dotenv()
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)   # ✅ instantiate once

# ────── FastAPI setup & CORS ────────────────────────────────
app = FastAPI(title="Video-Analysis-API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # or ["http://localhost:3000"]
    allow_credentials=False,      # must be False with "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────── Ensure NLTK data ────────────────────────────────────
for pkg in ("punkt", "stopwords"):
    try:
        nltk.data.find(
            f"tokenizers/{pkg}" if pkg == "punkt" else f"corpora/{pkg}"
        )
    except LookupError:
        nltk.download(pkg, quiet=True)

# ────── Request models ──────────────────────────────────────
class SummaryReq(BaseModel):
    url: str

class QueryReq(BaseModel):
    transcript: str
    query: str

# ────── Helper: YouTube URL → ID ────────────────────────────
_ID_PAT = [
    r"(?:youtube\.com/watch\?v=)([\w\-]{11})",
    r"(?:youtu\.be/)([\w\-]{11})",
    r"(?:youtube\.com/embed/)([\w\-]{11})",
    r"(?:youtube\.com/v/)([\w\-]{11})",
]
def extract_video_id(url: str) -> str:
    for p in _ID_PAT:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise HTTPException(400, "Invalid YouTube URL")

# ────── Video metadata via YouTube Data API ─────────────────
def get_video_info(video_id: str) -> Dict[str, Any]:
    if not YOUTUBE_API_KEY:
        return {"title": f"Video {video_id}", "description": "YOUTUBE_API_KEY missing"}
    try:
        yt = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        res = yt.videos().list(part="snippet,statistics,contentDetails", id=video_id).execute()
        if not res["items"]:
            return {}
        it = res["items"][0]
        return {
            "title": it["snippet"]["title"],
            "channel": it["snippet"]["channelTitle"],
            "views": int(it["statistics"].get("viewCount", 0)),
            "likes": int(it["statistics"].get("likeCount", 0)),
            "published": it["snippet"]["publishedAt"],
            "duration": it["contentDetails"]["duration"],
            "description": it["snippet"]["description"][:500],
            "thumbnail": it["snippet"]["thumbnails"]["high"]["url"],
        }
    except HttpError:
        return {}

# ────── Transcript extraction / translation ────────────────
async def fetch_transcript(video_id: str) -> str:
    try:
        tl = YouTubeTranscriptApi.list_transcripts(video_id)
        for t in tl:                          # prefer English
            if t.language_code.startswith("en"):
                return " ".join(seg.text for seg in t.fetch())
        t = tl[0]                             # translate if possible
        if t.is_translatable:
            t = t.translate("en")
        return " ".join(seg.text for seg in t.fetch())
    except Exception:
        raise HTTPException(status_code=500, detail="Transcript unavailable")

# ────── OpenAI chat helper (new SDK) ────────────────────────
async def openai_chat(prompt: str, model="gpt-3.5-turbo", temp=0.5, max_tokens=350):
    resp = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temp,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()

# Sentiment / Themes / Summary prompts
async def analyze_sentiment(text: str):
    prompt = (
        "Analyze sentiment (positive / neutral / negative) and return JSON with "
        "keys overall, score (0-1), explanation.\n\n" + text[:3000]
    )
    raw = await openai_chat(prompt, temp=0.3, max_tokens=300)
    try:
        return json.loads(re.search(r"\{.*\}", raw, re.DOTALL)[0])
    except Exception:
        return {"overall": "neutral", "score": 0.5, "explanation": raw[:200]}

async def extract_themes(text: str):
    prompt = (
        "Identify 5 main themes (name, relevance 0-1, description) and 10 keywords. "
        "Return JSON with keys themes, keywords.\n\n" + text[:3000]
    )
    raw = await openai_chat(prompt, max_tokens=400)
    try:
        return json.loads(re.search(r"\{.*\}", raw, re.DOTALL)[0])
    except Exception:
        return {"themes": [], "keywords": []}

async def summarise_transcript(text: str):
    prompt = "Create a concise (~200 word) summary:\n\n" + text[:4000]
    return await openai_chat(prompt, max_tokens=350)

# ────── Word-cloud helper ───────────────────────────────────
def make_wordcloud(text: str) -> str:
    stop_words = set(stopwords.words("english"))
    wc = WordCloud(
        width=800, height=400, background_color="white",
        stopwords=stop_words, max_words=120, colormap="viridis"
    ).generate(text)
    fig, ax = plt.subplots(figsize=(10, 5)); ax.imshow(wc); ax.axis("off")
    buf = io.BytesIO(); plt.savefig(buf, format="png", bbox_inches="tight"); plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

# ────── /api/summary endpoint ───────────────────────────────
@app.post("/api/summary")
async def api_summary(req: SummaryReq):
    vid = extract_video_id(req.url)
    meta = get_video_info(vid)
    transcript = await fetch_transcript(vid)

    # run LLM tasks concurrently
    s_task = asyncio.create_task(summarise_transcript(transcript))
    p_task = asyncio.create_task(analyze_sentiment(transcript))
    t_task = asyncio.create_task(extract_themes(transcript))

    summary, sentiment, themes = await asyncio.gather(s_task, p_task, t_task)
    wc_b64 = make_wordcloud(transcript)

    return {
        "videoId": vid,
        "timestamp": datetime.utcnow().isoformat(),
        "meta": meta,
        "transcript": transcript,
        "summary": summary,
        "sentiment": sentiment,
        "themes": themes,
        "wordcloud_b64": wc_b64,
    }

# ────── /api/query endpoint ────────────────────────────────
@app.post("/api/query")
async def api_query(req: QueryReq):
    if not req.transcript.strip():
        raise HTTPException(400, "Transcript empty")

    prompt = (
        "You are a helpful assistant. Use ONLY the transcript below to answer the question.\n\n"
        "Transcript:\n" + req.transcript[:4000] + "\n\nQ: " + req.query + "\nA:"
    )
    answer = await openai_chat(prompt)
    return {"response": answer}



