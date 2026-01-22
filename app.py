import streamlit as st
from dotenv import load_dotenv
load_dotenv()  # load all environment variables
import google.generativeai as genai
import os

# Import correctly
from youtube_transcript_api import YouTubeTranscriptApi

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Debug: List available models
try:
    st.sidebar.write("🔍 Checking available Gemini models...")
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
    st.sidebar.write(f"Available models: {available_models}")
except:
    st.sidebar.warning("Could not list models")

prompt = """You are a YouTube Video Summarizer. You will be taking the transcript text and summarizing 
the entire video and providing the important summary in points within 250 words. Please provide the
summary of the content here:"""

## getting the transcript data from yt videos
def extract_transcript_details(youtube_video_url):
    try:
        # Extract video ID
        if "v=" in youtube_video_url:
            video_id = youtube_video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in youtube_video_url:
            video_id = youtube_video_url.split("youtu.be/")[1].split("?")[0]
        else:
            video_id = youtube_video_url.split("/")[-1]
        
        st.write(f"📹 Video ID: {video_id}")
        
        # Create instance
        api = YouTubeTranscriptApi()
        
        # Use fetch method
        result = api.fetch(video_id)
        
        # Extract text from result
        transcript_text = ""
        
        if hasattr(result, 'snippets'):
            # If result has snippets attribute
            for snippet in result.snippets:
                transcript_text += " " + snippet.text
        elif hasattr(result, '__iter__'):
            # If result is iterable
            for item in result:
                if hasattr(item, 'text'):
                    transcript_text += " " + item.text
                elif isinstance(item, dict) and 'text' in item:
                    transcript_text += " " + item['text']
        else:
            transcript_text = str(result)
        
        return transcript_text.strip()
        
    except Exception as e:
        st.error(f"❌ Error extracting transcript: {str(e)}")
        return None

## getting the summary based on Prompt from Google Gemini Pro
def generate_gemini_content(transcript_text, prompt):
    # Try different model names (Google updated their model names)
    model_names_to_try = [
        "gemini-1.0-pro",      # Most common new name
        "gemini-1.5-pro",      # Newer version
        "models/gemini-pro",   # Full path
        "gemini-pro",          # Old name (might still work)
        "gemini-pro-vision",   # Alternative
    ]
    
    for model_name in model_names_to_try:
        try:
            st.write(f"Trying model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt + transcript_text)
            return response.text
        except Exception as e:
            st.warning(f"Model {model_name} failed: {str(e)[:100]}...")
            continue
    
    # If all fail, try to list available models and use first available
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                model = genai.GenerativeModel(m.name)
                response = model.generate_content(prompt + transcript_text)
                return response.text
    except Exception as e:
        st.error(f"All models failed: {e}")
        return f"Error: Could not generate summary. {str(e)}"

st.title("🎬 YouTube Transcript to Detailed Notes Converter")
youtube_link = st.text_input("Enter YouTube Video Link:", "https://www.youtube.com/watch?v=HFfXvfFe9F8")

if youtube_link:
    try:
        if "v=" in youtube_link:
            video_id = youtube_link.split("v=")[1].split("&")[0]
        elif "youtu.be/" in youtube_link:
            video_id = youtube_link.split("youtu.be/")[1].split("?")[0]
        else:
            video_id = youtube_link.split("/")[-1]
        
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)
        st.write(f"**Video ID:** `{video_id}`")
        
    except Exception as e:
        st.warning(f"Could not extract thumbnail: {e}")

if st.button("🎯 Get Detailed Notes"):
    if youtube_link:
        with st.spinner("🔍 Extracting transcript..."):
            transcript_text = extract_transcript_details(youtube_link)
        
        if transcript_text:
            st.success(f"✅ Transcript extracted successfully! ({len(transcript_text)} characters)")
            
            with st.expander("📄 Preview Transcript"):
                # Show first 500 chars
                preview = transcript_text[:500] + "..." if len(transcript_text) > 500 else transcript_text
                st.text(preview)
            
            with st.spinner("🤖 Generating summary with Gemini AI..."):
                summary = generate_gemini_content(transcript_text, prompt)
            
            st.markdown("## 📝 Detailed Notes:")
            st.write(summary)
            
            # Add download buttons
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download Summary",
                    data=summary,
                    file_name="youtube_summary.txt",
                    mime="text/plain"
                )
            with col2:
                st.download_button(
                    label="📥 Download Full Transcript",
                    data=transcript_text,
                    file_name="youtube_transcript.txt",
                    mime="text/plain"
                )
        else:
            st.error("❌ Failed to extract transcript.")
    else:
        st.warning("⚠️ Please enter a YouTube URL first.")