from __future__ import annotations
import os, re, json, base64, io, asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# OpenAI and other imports
from openai import AsyncOpenAI
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import nltk, matplotlib.pyplot as plt
from nltk.corpus import stopwords
from wordcloud import WordCloud

# Install additional required packages
# pip install youtube-transcript-api==0.6.1 pytube
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# FastAPI setup
app = FastAPI(title="Multilingual-Video-Analysis-API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NLTK setup
for pkg in ("punkt", "stopwords"):
    try:
        nltk.data.find(f"tokenizers/{pkg}" if pkg == "punkt" else f"corpora/{pkg}")
    except LookupError:
        nltk.download(pkg, quiet=True)

# ────── Language Configuration ─────────────────────────────
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native": "English", "flag": "🇺🇸"},
    "es": {"name": "Spanish", "native": "Español", "flag": "🇪🇸"},
    "fr": {"name": "French", "native": "Français", "flag": "🇫🇷"},
    "de": {"name": "German", "native": "Deutsch", "flag": "🇩🇪"},
    "it": {"name": "Italian", "native": "Italiano", "flag": "🇮🇹"},
    "pt": {"name": "Portuguese", "native": "Português", "flag": "🇧🇷"},
    "ru": {"name": "Russian", "native": "Русский", "flag": "🇷🇺"},
    "ja": {"name": "Japanese", "native": "日本語", "flag": "🇯🇵"},
    "ko": {"name": "Korean", "native": "한국어", "flag": "🇰🇷"},
    "zh": {"name": "Chinese", "native": "中文", "flag": "🇨🇳"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "flag": "🇮🇳"},
    "ar": {"name": "Arabic", "native": "العربية", "flag": "🇸🇦"},
    "nl": {"name": "Dutch", "native": "Nederlands", "flag": "🇳🇱"},
    "sv": {"name": "Swedish", "native": "Svenska", "flag": "🇸🇪"},
    "no": {"name": "Norwegian", "native": "Norsk", "flag": "🇳🇴"},
    "da": {"name": "Danish", "native": "Dansk", "flag": "🇩🇰"},
    "fi": {"name": "Finnish", "native": "Suomi", "flag": "🇫🇮"},
    "pl": {"name": "Polish", "native": "Polski", "flag": "🇵🇱"},
    "tr": {"name": "Turkish", "native": "Türkçe", "flag": "🇹🇷"},
    "th": {"name": "Thai", "native": "ไทย", "flag": "🇹🇭"},
    "vi": {"name": "Vietnamese", "native": "Tiếng Việt", "flag": "🇻🇳"},
    "he": {"name": "Hebrew", "native": "עברית", "flag": "🇮🇱"},
    "bn": {"name": "Bengali", "native": "বাংলা", "flag": "🇧🇩"},
    "ur": {"name": "Urdu", "native": "اردو", "flag": "🇵🇰"},
    "fa": {"name": "Persian", "native": "فارسی", "flag": "🇮🇷"},
}

# ────── Request Models ─────────────────────────────
class AdvancedSummaryReq(BaseModel):
    url: str
    output_language: str = "en"
    auto_detect_video_language: bool = True
    video_language_hint: Optional[str] = None
    
    class Config:
        # This helps with the OpenAPI documentation
        schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "output_language": "en",
                "auto_detect_video_language": True,
                "video_language_hint": None
            }
        }

class AdvancedQueryReq(BaseModel):
    transcript: str
    query: str
    output_language: str = "en"
    query_language: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "transcript": "This is a sample transcript...",
                "query": "What is this video about?",
                "output_language": "en",
                "query_language": None
            }
        }

# Backward compatibility models
class SummaryReq(BaseModel):
    url: str
    language: str = "en"

class QueryReq(BaseModel):
    transcript: str
    query: str
    language: str = "en"

# ────── Helper Functions ────────────────────────────────────
def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL"""
    patterns = [
        r"(?:youtube\.com/watch\?v=)([\w\-]{11})",
        r"(?:youtu\.be/)([\w\-]{11})",
        r"(?:youtube\.com/embed/)([\w\-]{11})",
        r"(?:youtube\.com/v/)([\w\-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise HTTPException(400, "Invalid YouTube URL")

def get_video_info(video_id: str) -> Dict[str, Any]:
    """Get video metadata via YouTube Data API"""
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

def make_wordcloud(text: str) -> str:
    """Create word cloud visualization"""
    try:
        stop_words = set(stopwords.words("english"))
        wc = WordCloud(
            width=800, height=400, background_color="white",
            stopwords=stop_words, max_words=120, colormap="viridis"
        ).generate(text)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wc)
        ax.axis("off")
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""

# ────── Enhanced Transcript Extraction ─────────────────────
async def fetch_transcript_advanced(video_id: str) -> tuple[str, str, str]:
    """Extract transcript and detect video language with robust error handling"""
    
    print(f"\n🔍 Attempting to extract transcript for video: {video_id}")
    
    try:
        # First, let's check if we can access the video at all
        from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
        
        print(f"📋 Listing available transcripts...")
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        available_transcripts = []
        for transcript in transcript_list:
            available_transcripts.append({
                'language': transcript.language,
                'language_code': transcript.language_code,
                'is_generated': transcript.is_generated,
                'is_translatable': transcript.is_translatable
            })
            print(f"   - {transcript.language} ({transcript.language_code}) [Generated: {transcript.is_generated}, Translatable: {transcript.is_translatable}]")
        
        if not available_transcripts:
            raise Exception("No transcripts found for this video")
        
        # Strategy 1: Try English transcripts first (both manual and auto-generated)
        print(f"🎯 Strategy 1: Looking for English transcripts...")
        for transcript in transcript_list:
            if transcript.language_code.lower() in ['en', 'en-us', 'en-gb', 'en-ca', 'en-au']:
                try:
                    print(f"   Trying English transcript: {transcript.language}")
                    data = transcript.fetch()
                    print(f"   Fetched data type: {type(data)}, length: {len(data) if data else 0}")
                    
                    if data:
                        # More robust text extraction
                        text_parts = []
                        for entry in data:
                            if isinstance(entry, dict) and 'text' in entry:
                                text_content = entry['text']
                                if text_content and isinstance(text_content, str):
                                    text_parts.append(text_content.strip())
                            elif isinstance(entry, str):
                                text_parts.append(entry.strip())
                        
                        text = " ".join(text_parts)
                        print(f"   Extracted text length: {len(text)}")
                        print(f"   First 100 chars: {repr(text[:100])}")
                        
                        if text and len(text.strip()) > 10:  # Make sure we got actual content
                            source_info = f"{'Auto-generated' if transcript.is_generated else 'Manual'} English transcript"
                            print(f"✅ Successfully extracted English transcript: {len(text)} characters")
                            return text.strip(), transcript.language_code, source_info
                        else:
                            print(f"   ❌ Text too short or empty: {len(text)} chars")
                            
                except Exception as e:
                    print(f"   ❌ Failed to fetch English transcript: {str(e)}")
                    import traceback
                    print(f"   Traceback: {traceback.format_exc()}")
                    continue
        
        # Strategy 2: Try any manually created transcript
        print(f"🎯 Strategy 2: Looking for manual transcripts in any language...")
        for transcript in transcript_list:
            if not transcript.is_generated:  # Manual transcripts are usually better
                try:
                    print(f"   Trying manual transcript: {transcript.language}")
                    data = transcript.fetch()
                    print(f"   Fetched data type: {type(data)}, length: {len(data) if data else 0}")
                    
                    if data:
                        # More robust text extraction
                        text_parts = []
                        for entry in data:
                            if isinstance(entry, dict) and 'text' in entry:
                                text_content = entry['text']
                                if text_content and isinstance(text_content, str):
                                    text_parts.append(text_content.strip())
                            elif isinstance(entry, str):
                                text_parts.append(entry.strip())
                        
                        text = " ".join(text_parts)
                        print(f"   Extracted text length: {len(text)}")
                        
                        if text and len(text.strip()) > 10:
                            source_info = f"Manual transcript in {transcript.language}"
                            print(f"✅ Successfully extracted manual transcript: {len(text)} characters")
                            return text.strip(), transcript.language_code, source_info
                        else:
                            print(f"   ❌ Text too short or empty: {len(text)} chars")
                            
                except Exception as e:
                    print(f"   ❌ Failed to fetch manual transcript: {str(e)}")
                    import traceback
                    print(f"   Traceback: {traceback.format_exc()}")
                    continue
        
        # Strategy 3: Try auto-generated transcripts
        print(f"🎯 Strategy 3: Looking for auto-generated transcripts...")
        for transcript in transcript_list:
            if transcript.is_generated:
                try:
                    print(f"   Trying auto-generated transcript: {transcript.language}")
                    data = transcript.fetch()
                    print(f"   Fetched data type: {type(data)}, length: {len(data) if data else 0}")
                    
                    if data:
                        # Debug: print first few entries
                        print(f"   First 3 entries: {data[:3] if len(data) >= 3 else data}")
                        
                        # More robust text extraction
                        text_parts = []
                        for i, entry in enumerate(data):
                            try:
                                if isinstance(entry, dict) and 'text' in entry:
                                    text_content = entry['text']
                                    if text_content and isinstance(text_content, str):
                                        text_parts.append(text_content.strip())
                                elif isinstance(entry, str):
                                    text_parts.append(entry.strip())
                                else:
                                    print(f"   Unexpected entry type at index {i}: {type(entry)} - {entry}")
                            except Exception as e:
                                print(f"   Error processing entry {i}: {e}")
                                continue
                        
                        text = " ".join(text_parts)
                        print(f"   Extracted text length: {len(text)}")
                        print(f"   First 200 chars: {repr(text[:200])}")
                        
                        if text and len(text.strip()) > 10:
                            source_info = f"Auto-generated transcript in {transcript.language}"
                            print(f"✅ Successfully extracted auto-generated transcript: {len(text)} characters")
                            return text.strip(), transcript.language_code, source_info
                        else:
                            print(f"   ❌ Text too short or empty: {len(text)} chars")
                            
                except Exception as e:
                    print(f"   ❌ Failed to fetch auto-generated transcript: {str(e)}")
                    import traceback
                    print(f"   Traceback: {traceback.format_exc()}")
                    continue
        
        # Strategy 4: Try translating available transcripts to English
        print(f"🎯 Strategy 4: Attempting translation to English...")
        for transcript in transcript_list:
            if transcript.is_translatable:
                try:
                    print(f"   Trying to translate {transcript.language} to English...")
                    translated = transcript.translate('en')
                    data = translated.fetch()
                    if data:
                        text = " ".join([entry['text'].strip() for entry in data if entry.get('text')])
                        if text and len(text) > 10:
                            source_info = f"Translated from {transcript.language} to English"
                            print(f"✅ Successfully translated transcript: {len(text)} characters")
                            return text.strip(), 'en', source_info
                except Exception as e:
                    print(f"   ❌ Failed to translate transcript: {str(e)}")
                    continue
        
        # If we get here, all strategies failed
        error_msg = f"Found {len(available_transcripts)} transcript(s) but couldn't extract any usable content"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)
        
    except TranscriptsDisabled:
        error_msg = "Transcripts are disabled for this video"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=404, detail=error_msg)
        
    except NoTranscriptFound:
        error_msg = "No transcripts found for this video"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=404, detail=error_msg)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Transcript extraction failed: {error_msg}")
        
        # Provide more helpful error messages
        if "private" in error_msg.lower():
            raise HTTPException(status_code=403, detail="This video is private and transcripts cannot be accessed")
        elif "unavailable" in error_msg.lower():
            raise HTTPException(status_code=404, detail="Video is unavailable or has been removed")
        elif "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail="Video not found or transcripts are not available")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to extract transcript: {error_msg}")

# ────── AI Processing Functions ─────────────────────────────
async def openai_chat_advanced(prompt: str, model="gpt-3.5-turbo", temp=0.5, max_tokens=350):
    """Enhanced OpenAI chat with better error handling"""
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temp,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API Error: {str(e)}")
        return f"AI analysis temporarily unavailable: {str(e)[:100]}"

async def cross_language_summary(
    transcript: str, 
    video_language: str, 
    output_language: str,
    video_info: dict = None
) -> str:
    """Generate summary in target language regardless of video language"""
    
    video_lang_name = SUPPORTED_LANGUAGES.get(video_language, {}).get("native", video_language)
    output_lang_name = SUPPORTED_LANGUAGES.get(output_language, {}).get("native", output_language)
    
    # Create context about the video
    context = ""
    if video_info:
        context = f"""
Video Context:
- Title: {video_info.get('title', 'Unknown')}
- Channel: {video_info.get('channel', 'Unknown')}
- Views: {video_info.get('views', 'Unknown')}
"""
    
    prompt = f"""You are an expert multilingual video analyst. Your task is to analyze this video transcript and provide a comprehensive summary.

{context}

IMPORTANT INSTRUCTIONS:
1. The video transcript is in {video_lang_name}
2. You must provide your ENTIRE response in {output_lang_name}
3. Create a detailed summary (200-250 words) covering:
   - Main topic and purpose of the video
   - Key points and arguments presented
   - Important examples or case studies mentioned
   - Conclusions or takeaways
   - Target audience and video style

4. Write EVERYTHING in {output_lang_name}, even if the original video is in a different language
5. Make the summary useful for someone who doesn't understand {video_lang_name}

Video Transcript:
{transcript[:4000]}

Please provide your complete analysis in {output_lang_name}:"""

    return await openai_chat_advanced(prompt, max_tokens=400)

async def cross_language_sentiment(
    transcript: str, 
    video_language: str, 
    output_language: str
) -> dict:
    """Analyze sentiment and explain in target language"""
    
    video_lang_name = SUPPORTED_LANGUAGES.get(video_language, {}).get("native", video_language)
    output_lang_name = SUPPORTED_LANGUAGES.get(output_language, {}).get("native", output_language)
    
    prompt = f"""Analyze the emotional tone and sentiment of this video transcript.

INSTRUCTIONS:
- The transcript is in {video_lang_name}
- Provide your analysis in {output_lang_name}
- Consider cultural context and language-specific expressions

Provide a JSON response with:
1. "overall": sentiment category (positive/negative/neutral)
2. "score": numerical score from 0.0 (very negative) to 1.0 (very positive)
3. "explanation": detailed explanation in {output_lang_name} about why this sentiment was detected
4. "confidence": confidence level (high/medium/low)

Example format:
{{
    "overall": "positive",
    "score": 0.75,
    "explanation": "[Detailed explanation in {output_lang_name}]",
    "confidence": "high"
}}

Transcript: {transcript[:3000]}

Respond with valid JSON in {output_lang_name}:"""

    raw = await openai_chat_advanced(prompt, temp=0.3, max_tokens=350)
    try:
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"JSON parsing error: {e}")
    
    # Fallback response
    return {
        "overall": "neutral",
        "score": 0.5,
        "explanation": raw[:200] if raw else f"Could not analyze sentiment. Response in {output_lang_name}",
        "confidence": "low"
    }

async def cross_language_themes(
    transcript: str, 
    video_language: str, 
    output_language: str
) -> dict:
    """Extract themes and keywords in target language"""
    
    video_lang_name = SUPPORTED_LANGUAGES.get(video_language, {}).get("native", video_language)
    output_lang_name = SUPPORTED_LANGUAGES.get(output_language, {}).get("native", output_language)
    
    prompt = f"""Analyze this video transcript to identify main themes and topics.

INSTRUCTIONS:
- The transcript is in {video_lang_name}
- Provide your analysis in {output_lang_name}
- Identify themes that would be meaningful to speakers of {output_lang_name}

Extract:
1. 5 main themes with:
   - theme name in {output_lang_name}
   - relevance score (0.0-1.0)
   - description in {output_lang_name}

2. 10 key terms/keywords translated to {output_lang_name}

Respond in JSON format:
{{
    "themes": [
        {{
            "theme": "Theme name in {output_lang_name}",
            "relevance": 0.9,
            "description": "Description in {output_lang_name}"
        }}
    ],
    "keywords": ["keyword1 in {output_lang_name}", "keyword2", ...]
}}

Transcript: {transcript[:3000]}

Provide JSON response in {output_lang_name}:"""

    raw = await openai_chat_advanced(prompt, max_tokens=450)
    try:
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"JSON parsing error: {e}")
    
    return {"themes": [], "keywords": []}

# ────── API Endpoints ───────────────────────────────────────
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "YouTube AI Dashboard API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/test-videos")
async def get_test_videos():
    """Get a list of test videos that should work"""
    test_videos = [
        {
            "title": "Never Gonna Give You Up",
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "video_id": "dQw4w9WgXcQ",
            "description": "Classic video with reliable captions"
        },
        {
            "title": "Gangnam Style",
            "url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
            "video_id": "9bZkp7q19f0", 
            "description": "Popular video with multiple language captions"
        },
        {
            "title": "Despacito",
            "url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
            "video_id": "kJQP7kiw5Fk",
            "description": "Spanish video with captions"
        },
        {
            "title": "Baby Shark",
            "url": "https://www.youtube.com/watch?v=XqZsoesa55w", 
            "video_id": "XqZsoesa55w",
            "description": "Simple English video with captions"
        }
    ]
    return {"test_videos": test_videos}

@app.get("/api/test-transcript/{video_id}")
async def test_transcript(video_id: str):
    """Test transcript extraction for debugging"""
    try:
        transcript, lang, source = await fetch_transcript_advanced(video_id)
        return {
            "success": True,
            "video_id": video_id,
            "transcript_length": len(transcript),
            "detected_language": lang,
            "source": source,
            "first_200_chars": transcript[:200] + "..." if len(transcript) > 200 else transcript
        }
    except HTTPException as e:
        return {
            "success": False,
            "error": e.detail, 
            "status_code": e.status_code,
            "video_id": video_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e), 
            "status_code": 500,
            "video_id": video_id
        }
async def get_supported_languages():
    """Get comprehensive language information"""
    return {
        "languages": [
            {
                "code": code,
                "name": info["name"], 
                "native_name": info["native"],
                "flag": info["flag"],
                "display": f"{info['flag']} {info['native']}"
            }
            for code, info in SUPPORTED_LANGUAGES.items()
        ],
        "total_languages": len(SUPPORTED_LANGUAGES)
    }

@app.post("/api/advanced-summary")
async def api_advanced_summary(req: AdvancedSummaryReq):
    """Advanced multilingual video analysis"""
    # Validate languages
    if req.output_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(400, f"Unsupported output language: {req.output_language}")
    
    # Handle video language hint - ignore if it's empty, "string", or None
    if req.video_language_hint and req.video_language_hint not in ["string", ""] and req.video_language_hint not in SUPPORTED_LANGUAGES:
        raise HTTPException(400, f"Unsupported video language hint: {req.video_language_hint}")
    
    # Extract video info and transcript
    video_id = extract_video_id(req.url)
    meta = get_video_info(video_id)
    transcript, detected_video_lang, source_info = await fetch_transcript_advanced(video_id)
    
    # Use hint if provided and valid, otherwise use detected language
    video_language = detected_video_lang
    if req.video_language_hint and req.video_language_hint not in ["string", "", None] and req.video_language_hint in SUPPORTED_LANGUAGES:
        video_language = req.video_language_hint
    
    # Run AI analysis concurrently
    summary_task = asyncio.create_task(
        cross_language_summary(transcript, video_language, req.output_language, meta)
    )
    sentiment_task = asyncio.create_task(
        cross_language_sentiment(transcript, video_language, req.output_language)
    )
    themes_task = asyncio.create_task(
        cross_language_themes(transcript, video_language, req.output_language)
    )
    
    summary, sentiment, themes = await asyncio.gather(summary_task, sentiment_task, themes_task)
    wordcloud_b64 = make_wordcloud(transcript)
    
    return {
        "videoId": video_id,
        "timestamp": datetime.utcnow().isoformat(),
        "meta": meta,
        "transcript": transcript,
        "video_language": video_language,
        "video_language_name": SUPPORTED_LANGUAGES.get(video_language, {}).get("native", video_language),
        "output_language": req.output_language,
        "output_language_name": SUPPORTED_LANGUAGES.get(req.output_language, {}).get("native", req.output_language),
        "transcript_source": source_info,
        "summary": summary,
        "sentiment": sentiment,
        "themes": themes,
        "wordcloud_b64": wordcloud_b64,
    }

@app.post("/api/advanced-query")
async def api_advanced_query(req: AdvancedQueryReq):
    """Advanced multilingual Q&A"""
    if not req.transcript.strip():
        raise HTTPException(400, "Transcript empty")
    
    if req.output_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(400, f"Unsupported output language: {req.output_language}")
    
    output_lang_name = SUPPORTED_LANGUAGES.get(req.output_language, {}).get("native", req.output_language)
    query_lang_info = ""
    
    if req.query_language:
        query_lang_name = SUPPORTED_LANGUAGES.get(req.query_language, {}).get("native", req.query_language)
        query_lang_info = f" (question asked in {query_lang_name})"
    
    prompt = f"""You are a helpful multilingual assistant. Answer the user's question based ONLY on the provided transcript.

IMPORTANT:
- Provide your answer in {output_lang_name}
- Base your answer only on the transcript content
- If the transcript doesn't contain relevant information, say so in {output_lang_name}
- Be comprehensive and helpful

User Question{query_lang_info}: {req.query}

Video Transcript:
{req.transcript[:4000]}

Please provide a detailed answer in {output_lang_name}:"""

    answer = await openai_chat_advanced(prompt, max_tokens=400)
    
    return {
        "response": answer,
        "output_language": req.output_language,
        "output_language_name": output_lang_name,
        "query_language": req.query_language
    }

# ────── Backward Compatibility Endpoints ───────────────────
@app.post("/api/summary")
async def api_summary_compat(req: SummaryReq):
    """Backward compatible endpoint"""
    advanced_req = AdvancedSummaryReq(url=req.url, output_language=req.language)
    return await api_advanced_summary(advanced_req)

@app.post("/api/query") 
async def api_query_compat(req: QueryReq):
    """Backward compatible endpoint"""
    advanced_req = AdvancedQueryReq(
        transcript=req.transcript, 
        query=req.query, 
        output_language=req.language
    )
    return await api_advanced_query(advanced_req)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)