import streamlit as st
from dotenv import load_dotenv
load_dotenv()  # load all environment variables
import google.genai as genai  # NEW: Changed from google.generativeai
import os
import re

# Import correctly
from youtube_transcript_api import YouTubeTranscriptApi

st.set_page_config(page_title="YouTube Summarizer", page_icon="🎬")
st.title("🎬 YouTube Transcript to Detailed Notes Converter")

# Add custom CSS
st.markdown("""
    <style>
    .stTextInput > div > div > input {
        font-size: 16px;
        padding: 12px;
    }
    .stButton > button {
        background-color: #FF4B4B;
        color: white;
        font-weight: bold;
        padding: 10px 24px;
        border-radius: 5px;
        border: none;
    }
    .stButton > button:hover {
        background-color: #FF3333;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("### Paste a YouTube link below to get AI-generated notes:")

# Initialize Gemini API with NEW package
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    try:
        # NEW: Configure with the new package
        client = genai.Client(api_key=api_key)
        st.session_state.gemini_available = True
        st.session_state.gemini_client = client
    except Exception as e:
        st.error(f"❌ Gemini API configuration failed: {e}")
        st.session_state.gemini_available = False
else:
    st.warning("⚠️ GOOGLE_API_KEY not found in .env file")
    st.session_state.gemini_available = False

prompt = """You are a YouTube Video Summarizer. You will be taking the transcript text and summarizing 
the entire video and providing the important summary in points within 250 words. Please provide the
summary of the content here:"""

## getting the transcript data from yt videos
def extract_transcript_details(youtube_video_url):
    try:
        # Extract video ID using regex for better handling
        video_id = None
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, youtube_video_url)
            if match:
                video_id = match.group(1)
                break
        
        if not video_id:
            st.error("❌ Could not extract video ID from URL")
            return None
        
        st.write(f"📹 Video ID: `{video_id}`")
        
        # Create instance and fetch transcript
        api = YouTubeTranscriptApi()
        result = api.fetch(video_id)
        
        # Extract text
        transcript_text = ""
        
        if hasattr(result, 'snippets'):
            for snippet in result.snippets:
                transcript_text += " " + snippet.text
        elif hasattr(result, '__iter__'):
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

## NEW Gemini AI summary function with updated package
def generate_gemini_content(transcript_text, prompt):
    try:
        # Get client from session state
        client = st.session_state.get('gemini_client')
        if not client:
            return None
        
        # Try different model names (new models from your test)
        model_names = [
            "gemini-2.5-flash",  # Fast and capable
            "gemini-2.5-flash-exp",  # Experimental version
            "gemini-2.0-flash",  # Previous version
            "gemini-1.5-pro",  # Pro version
            "gemini-pro",  # Legacy name
        ]
        
        for model_name in model_names:
            try:
                with st.spinner(f"Using {model_name}..."):
                    # NEW: Generate content with the new package
                    response = client.models.generate_content(
                        model=model_name,
                        contents=f"{prompt}\n\nTranscript:\n{transcript_text[:8000]}"  # Limit length
                    )
                    return response.text
            except Exception as e:
                st.write(f"Model {model_name} failed: {str(e)[:100]}")
                continue
        
        return None  # All models failed
        
    except Exception as e:
        st.error(f"Gemini API error: {str(e)[:200]}")
        return None

## Simple text summarizer as fallback
def generate_simple_summary(transcript_text):
    """Fallback summarizer when Gemini fails"""
    # Simple algorithm: take first 100 words as summary
    words = transcript_text.split()
    
    if len(words) > 100:
        summary = " ".join(words[:100]) + "..."
    else:
        summary = transcript_text
    
    # Add some formatting
    formatted_summary = f"""
    ## 📋 Summary (Simple Extraction)
    
    {summary}
    
    *Note: This is a simple text extraction since AI summarization is unavailable.*
    *To enable AI summarization, please check your Gemini API configuration.*
    
    **Transcript Length:** {len(words)} words, {len(transcript_text)} characters
    """
    
    return formatted_summary

# User input
youtube_link = st.text_input(
    "YouTube Video URL:",
    placeholder="https://www.youtube.com/watch?v=...",
    help="Paste any YouTube video link here"
)

# Show examples
with st.expander("💡 Need a video to test?"):
    st.markdown("""
    Try these videos (they have captions):
    - `https://www.youtube.com/watch?v=cE72C0e0bKw` (Short tutorial)
    - `https://www.youtube.com/watch?v=9bZkp7q19f0` (Gangnam Style - has captions)
    - `https://www.youtube.com/watch?v=dQw4w9WgXcQ` (Classic)
    """)

# Show thumbnail if URL is entered
if youtube_link and ("youtube.com" in youtube_link or "youtu.be" in youtube_link):
    try:
        # Extract video ID
        video_id = None
        match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', youtube_link)
        if match:
            video_id = match.group(1)
        
        if video_id:
            st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", width=500)
            st.caption(f"Video ID: `{video_id}`")
    except:
        pass

# Process button
if st.button("🎯 Generate Detailed Notes", type="primary", use_container_width=True):
    if not youtube_link:
        st.warning("⚠️ Please enter a YouTube URL")
        st.stop()
    
    if "youtube.com" not in youtube_link and "youtu.be" not in youtube_link:
        st.error("❌ Please enter a valid YouTube URL")
        st.stop()
    
    # Step 1: Extract transcript
    with st.spinner("🔍 Extracting transcript from YouTube..."):
        transcript_text = extract_transcript_details(youtube_link)
    
    if not transcript_text:
        st.error("❌ Could not extract transcript. The video might not have captions.")
        st.stop()
    
    st.success(f"✅ Transcript extracted ({len(transcript_text)} characters)")
    
    # Show transcript preview
    with st.expander("📄 View Transcript Preview", expanded=False):
        st.text(transcript_text[:1000] + "..." if len(transcript_text) > 1000 else transcript_text)
    
    # Step 2: Generate summary
    st.markdown("---")
    st.subheader("🤖 AI Summary Generation")
    
    # Check if Gemini is available
    if st.session_state.get('gemini_available', False):
        st.info("Using Google Gemini AI for summarization...")
        
        with st.spinner("Generating AI-powered summary..."):
            ai_summary = generate_gemini_content(transcript_text, prompt)
        
        if ai_summary:
            st.success("✅ AI summary generated successfully!")
            st.markdown("## 📝 Detailed Notes:")
            st.write(ai_summary)
            
            # Add AI tag
            st.caption("🤖 Generated by Google Gemini AI")
        else:
            st.warning("⚠️ Gemini AI failed. Using simple text extraction...")
            summary = generate_simple_summary(transcript_text)
            st.markdown("## 📝 Notes (Simple Extraction):")
            st.write(summary)
            st.caption("📄 Simple text extraction (AI unavailable)")
    else:
        st.warning("⚠️ Gemini API not configured. Using simple text extraction...")
        summary = generate_simple_summary(transcript_text)
        st.markdown("## 📝 Notes (Simple Extraction):")
        st.write(summary)
        st.caption("📄 Simple text extraction")
    
    # Step 3: Download options
    st.markdown("---")
    st.subheader("📥 Download Options")
    
    col1, col2 = st.columns(2)
    
    # Get the final summary text
    final_summary = ai_summary if st.session_state.get('gemini_available', False) and ai_summary else summary
    
    with col1:
        st.download_button(
            label="💾 Download Summary",
            data=final_summary,
            file_name="youtube_summary.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        st.download_button(
            label="💾 Download Full Transcript",
            data=transcript_text,
            file_name="youtube_transcript.txt",
            mime="text/plain",
            use_container_width=True
        )

# Add footer
st.markdown("---")
st.caption("✨ Powered by YouTube Transcript API & Google Gemini AI")