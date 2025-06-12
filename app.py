app.py
import streamlit as st
import os
import re
import json
from pathlib import Path
from datetime import datetime
import base64
from io import BytesIO

from youtube_transcript_api import YouTubeTranscriptApi
import openai
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Video Analysis Tool",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        background-color: #667eea;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #764ba2;
        transform: translateY(-2px);
    }
    .success-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Initialize storage
STORAGE_PATH = Path('./data')
STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# API Configuration
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Configure OpenAI
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    MODEL_NAME = "gpt-3.5-turbo"  # You can also use "gpt-4" if you have access
    model_available = True
else:
    model_available = False
    st.error("OpenAI API key not found. Please add OPENAI_API_KEY to your .env file")

# Download NLTK data if needed
@st.cache_resource
def download_nltk_data():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)

download_nltk_data()

# Initialize session state
if 'analyzed_videos' not in st.session_state:
    st.session_state.analyzed_videos = {}
if 'insights' not in st.session_state:
    st.session_state.insights = []

def call_openai(prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
    """Call OpenAI API with the given prompt"""
    if not model_available:
        return None
    
    try:
        response = openai.ChatCompletion.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes YouTube videos."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI API Error: {str(e)}")
        return None

def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        r'(?:youtube\.com\/embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtube\.com\/v\/)([0-9A-Za-z_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_info(video_id: str) -> dict:
    """Get video information using YouTube Data API v3"""
    if not YOUTUBE_API_KEY:
        return {"title": f"Video {video_id}", "description": "No API key provided"}
    
    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        
        request = youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id=video_id
        )
        response = request.execute()
        
        if response.get('items'):
            item = response['items'][0]
            return {
                'title': item['snippet'].get('title', 'Unknown Title'),
                'channel': item['snippet'].get('channelTitle', 'Unknown Channel'),
                'description': item['snippet'].get('description', '')[:500],
                'published': item['snippet'].get('publishedAt', ''),
                'views': int(item['statistics'].get('viewCount', 0)),
                'likes': int(item['statistics'].get('likeCount', 0)),
                'duration': item['contentDetails'].get('duration', ''),
                'thumbnail': item['snippet'].get('thumbnails', {}).get('high', {}).get('url', '')
            }
        else:
            return {"title": f"Video {video_id}", "description": "Video not found"}
            
    except HttpError as e:
        st.warning(f"YouTube API error: {str(e)[:100]}")
        return {"title": f"Video {video_id}", "description": "Could not fetch video info"}
        
    except Exception as e:
        st.warning(f"Error fetching video info: {str(e)[:100]}")
        return {"title": f"Video {video_id}", "description": "Could not fetch video info"}

def extract_transcript(video_id: str) -> tuple:
    """Extract transcript from YouTube video"""
    video_info = get_video_info(video_id)
    
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to get English transcript first
        for transcript in transcript_list:
            if transcript.language_code.startswith('en'):
                try:
                    data = transcript.fetch()
                    text = " ".join([entry['text'] for entry in data])
                    st.success("✅ Extracted English transcript!")
                    return text, video_info
                except:
                    continue
        
        # Try any available transcript
        for transcript in transcript_list:
            try:
                if transcript.is_translatable:
                    translated = transcript.translate('en')
                    data = translated.fetch()
                    text = " ".join([entry['text'] for entry in data])
                    st.success(f"✅ Translated from {transcript.language} to English!")
                    return text, video_info
                else:
                    data = transcript.fetch()
                    text = " ".join([entry['text'] for entry in data])
                    st.warning(f"⚠️ Using {transcript.language} transcript")
                    return text, video_info
            except:
                continue
                    
        st.error("❌ Could not extract transcript from this video")
        return None, video_info
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)[:200]}")
        return None, video_info

def analyze_video_content(video_id: str, video_info: dict) -> dict:
    """Analyze what the video is about using OpenAI"""
    title = video_info.get('title', '')
    channel = video_info.get('channel', '')
    description = video_info.get('description', '')
    
    if not title and not description:
        return None
    
    prompt = f"""Based on this YouTube video information, analyze and explain what the video is about:

Title: {title}
Channel: {channel}
Description: {description}

Please provide:
1. **Main Topic**: What is this video primarily about? (1-2 sentences)
2. **Key Points**: What are the 3-5 main points or topics covered?
3. **Target Audience**: Who would be interested in this video?
4. **Category**: What category does this video fall into? (News, Education, Entertainment, etc.)
5. **Summary**: A brief 2-3 sentence summary of what viewers will learn or see

Format your response clearly with these headings."""

    response = call_openai(prompt)
    
    if response:
        return {
            'raw_analysis': response,
            'title': title,
            'channel': channel
        }
    return None

def analyze_sentiment_with_openai(transcript: str) -> dict:
    """Analyze sentiment using OpenAI"""
    if not model_available:
        return {"overall": "API key required", "score": 0.5, "explanation": "Please add OpenAI API key"}
    
    prompt = f"""Analyze the sentiment of this video transcript. 
    Provide:
    1. Overall sentiment (positive, negative, or neutral)
    2. Sentiment score (0-1, where 0 is very negative and 1 is very positive)
    3. A brief explanation of the sentiment
    
    Respond in JSON format like:
    {{
        "overall": "positive/negative/neutral",
        "score": 0.75,
        "explanation": "Brief explanation"
    }}
    
    Transcript: {transcript[:3000]}..."""
    
    response = call_openai(prompt)
    
    if response:
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
    
    return {
        "overall": "neutral",
        "score": 0.5,
        "explanation": response[:200] if response else "Could not analyze sentiment"
    }

def extract_themes_with_openai(transcript: str) -> dict:
    """Extract themes using OpenAI"""
    if not model_available:
        return extract_themes_basic(transcript)
    
    prompt = f"""Analyze this video transcript and identify the 5 main themes or topics discussed.
    For each theme provide:
    1. Theme name
    2. Relevance score (0-1)
    3. Brief description
    
    Also provide a list of 10 keywords.
    
    Respond in JSON format like:
    {{
        "themes": [
            {{"theme": "Theme Name", "relevance": 0.9, "description": "Brief description"}},
            ...
        ],
        "keywords": ["keyword1", "keyword2", ...]
    }}
    
    Transcript: {transcript[:3000]}..."""
    
    response = call_openai(prompt)
    
    if response:
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
            
    return extract_themes_basic(transcript)

def extract_themes_basic(transcript: str) -> dict:
    """Basic theme extraction using NLTK"""
    try:
        stop_words = set(stopwords.words('english'))
        words = word_tokenize(transcript.lower())
        filtered_words = [word for word in words 
                        if word.isalnum() and 
                        word not in stop_words and 
                        len(word) > 3]
        
        word_counts = Counter(filtered_words)
        most_common = word_counts.most_common(20)
        
        themes = []
        for word, count in most_common[:5]:
            relevance = min(0.9, count / (len(filtered_words) * 0.01)) if filtered_words else 0.5
            themes.append({
                'theme': word.title(),
                'relevance': float(relevance),
                'description': f"Mentioned {count} times"
            })
        
        return {
            'themes': themes,
            'keywords': [word for word, _ in most_common[:10]]
        }
    except Exception as e:
        return {'themes': [], 'keywords': []}

def summarize_with_openai(transcript: str) -> str:
    """Generate summary using OpenAI"""
    if not model_available:
        return transcript[:500] + "..." if len(transcript) > 500 else transcript
    
    prompt = f"""Create a concise summary of this video transcript in about 200 words.
    Focus on the main points, key takeaways, and overall message.
    
    Transcript: {transcript[:4000]}..."""
    
    response = call_openai(prompt)
    return response if response else transcript[:500] + "..."

def create_word_cloud(transcript: str) -> BytesIO:
    """Create word cloud visualization"""
    try:
        stop_words = set(stopwords.words('english'))
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            stopwords=stop_words,
            max_words=100,
            colormap='viridis'
        ).generate(transcript)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        plt.close()
        
        return buf
    except Exception as e:
        st.error(f"Error creating word cloud: {str(e)}")
        return None

# Main UI
st.title("🎥 Video Analysis Tool")
st.markdown("Extract insights from YouTube videos using AI")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Status
    st.subheader("API Status")
    
    # OpenAI Status
    if OPENAI_API_KEY:
        st.success(f"✅ OpenAI API Connected ({MODEL_NAME})")
    else:
        st.warning("⚠️ OpenAI API Key Missing")
        st.markdown("[Get your API key](https://platform.openai.com/api-keys)")
    
    # YouTube Status
    if YOUTUBE_API_KEY:
        st.success("✅ YouTube API Connected")
    else:
        st.info("ℹ️ YouTube API Optional")
        st.markdown("[Enable YouTube API](https://console.cloud.google.com/apis/library/youtube.googleapis.com)")
    
    # Insights section
    st.divider()
    st.subheader("💡 Insights Memo")
    
    new_insight = st.text_input("Add an insight")
    if st.button("Add Insight", key="add_insight"):
        if new_insight:
            st.session_state.insights.append({
                'text': new_insight,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
            })
            st.success("Insight added!")
    
    if st.session_state.insights:
        st.text_area(
            "All Insights",
            value="\n".join([f"• {i['text']} ({i['timestamp']})" for i in st.session_state.insights]),
            height=200,
            disabled=True
        )
        
        if st.button("Clear All Insights"):
            st.session_state.insights = []
            st.rerun()

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    url = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        help="Enter a YouTube video URL to analyze"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_button = st.button("🔍 Analyze Video", type="primary", use_container_width=True)

# Analysis section
if analyze_button and url:
    video_id = extract_video_id(url)
    
    if not video_id:
        st.error("Invalid YouTube URL. Please check the URL and try again.")
    else:
        # Get video info first
        with st.spinner("Fetching video information..."):
            video_info = get_video_info(video_id)
        
        if video_info and video_info.get('title'):
            # Display video info
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"### 🎬 {video_info.get('title', 'Video Analysis')}")
                st.markdown(f"**Channel:** {video_info.get('channel', 'Unknown')}")
            
            with col2:
                if video_info.get('views'):
                    st.metric("Views", f"{video_info['views']:,}")
            
            with col3:
                if video_info.get('likes'):
                    st.metric("Likes", f"{video_info['likes']:,}")
            
            # Analyze what the video is about
            with st.spinner("Analyzing what this video is about..."):
                content_analysis = analyze_video_content(video_id, video_info)
            
            if content_analysis:
                st.success("✅ Video content analyzed!")
                
                # Display the analysis
                st.markdown("---")
                st.markdown("## 📊 Video Content Analysis")
                st.markdown(content_analysis['raw_analysis'])
                
                # Try to get transcript for deeper analysis
                with st.expander("🔍 Want deeper analysis with transcript?"):
                    st.info("For sentiment analysis, themes, and summaries, we need the transcript.")
                    
                    if st.button("Extract and Analyze Transcript"):
                        with st.spinner("Extracting transcript..."):
                            transcript, _ = extract_transcript(video_id)
                        
                        if transcript:
                            # Store analysis
                            analysis = {
                                'video_id': video_id,
                                'transcript': transcript,
                                'video_info': video_info,
                                'content_analysis': content_analysis
                            }
                            
                            # Perform deeper analysis
                            with st.spinner("Analyzing transcript..."):
                                analysis['sentiment'] = analyze_sentiment_with_openai(transcript)
                                analysis['themes'] = extract_themes_with_openai(transcript)
                                analysis['summary'] = summarize_with_openai(transcript)
                            
                            st.session_state.analyzed_videos[video_id] = analysis
                            st.success("✅ Detailed analysis complete!")
                            st.rerun()
                        else:
                            st.warning("Couldn't extract transcript.")
            else:
                st.error("Could not analyze video content.")
        else:
            st.error("Could not fetch video information.")

# Display results if we have analysis
if url and extract_video_id(url) in st.session_state.analyzed_videos:
    video_id = extract_video_id(url)
    analysis = st.session_state.analyzed_videos[video_id]
    
    # Create tabs
    tabs = st.tabs(["📝 Summary", "😊 Sentiment", "🎯 Themes", "📊 Visualizations", "📄 Transcript"])
    
    with tabs[0]:
        st.subheader("Video Summary")
        if 'summary' in analysis:
            st.write(analysis['summary'])
    
    with tabs[1]:
        st.subheader("Sentiment Analysis")
        if 'sentiment' in analysis:
            sentiment = analysis['sentiment']
            
            col1, col2 = st.columns([1, 2])
            with col1:
                sentiment_emoji = {
                    'positive': '😊',
                    'negative': '😞',
                    'neutral': '😐'
                }.get(sentiment.get('overall', 'neutral'), '😐')
                
                st.metric(
                    "Overall Sentiment",
                    f"{sentiment_emoji} {sentiment.get('overall', 'Unknown').title()}",
                    f"Score: {sentiment.get('score', 0):.2f}"
                )
            
            with col2:
                st.info(sentiment.get('explanation', 'No explanation available'))
    
    with tabs[2]:
        st.subheader("Key Themes")
        if 'themes' in analysis and analysis['themes'].get('themes'):
            for theme in analysis['themes']['themes']:
                with st.expander(f"**{theme['theme']}** - {theme.get('relevance', 0)*100:.0f}% relevance"):
                    st.write(theme.get('description', 'No description'))
            
            if analysis['themes'].get('keywords'):
                st.subheader("Keywords")
                st.write(", ".join(analysis['themes']['keywords']))
    
    with tabs[3]:
        st.subheader("Word Cloud")
        if 'transcript' in analysis:
            wordcloud = create_word_cloud(analysis['transcript'])
            if wordcloud:
                st.image(wordcloud, use_column_width=True)
    
    with tabs[4]:
        st.subheader("Transcript")
        if 'transcript' in analysis:
            st.text_area("", analysis['transcript'], height=400, disabled=True)
            
            # Download button
            st.download_button(
                label="Download Transcript",
                data=analysis['transcript'],
                file_name=f"transcript_{video_id}.txt",
                mime="text/plain"
            )

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        Powered by OpenAI GPT-3.5 | Made with ❤️ using Streamlit
    </div>
    """,
    unsafe_allow_html=True
)