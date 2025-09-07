import streamlit as st
import whisper
import yt_dlp
import tempfile
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime

# Configure the Streamlit page
st.set_page_config(
    page_title="YouTube Transcript Generator",
    page_icon="📝",
    layout="wide"
)

# Title and description
st.title("🎥 YouTube Transcript Generator")
st.write("Extract transcripts from YouTube videos!")

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    # Remove any extra parameters first
    url = url.split('&')[0].split('?')[0] if '?' in url else url
    
    patterns = [
        r'(?:v=|/)([0-9A-Za-z_-]{11}).*',
        r'youtu\.be/([0-9A-Za-z_-]{11})',
        r'embed/([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            if len(video_id) == 11:
                return video_id
    return None

@st.cache_resource
def load_whisper_model(model_size="base"):
    """Load Whisper model (cached for better performance)"""
    return whisper.load_model(model_size)

def get_existing_transcript(video_url):
    """Get existing captions using NEW API format"""
    try:
        video_id = extract_video_id(video_url)
        if not video_id:
            return None, "Invalid URL"
        
        # NEW API: Create instance and use fetch()
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id)
        
        # Convert to raw data and format
        raw_data = fetched_transcript.to_raw_data()
        formatted_text = '\n'.join([entry['text'] for entry in raw_data])
        return formatted_text, "captions"
        
    except Exception as e:
        return None, f"No captions: {str(e)}"

def download_audio(video_url, output_path):
    """Download audio from YouTube video for Whisper processing"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'extractaudio': True,
        'audioformat': 'wav',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return True
    except Exception as e:
        st.error(f"Audio download failed: {str(e)}")
        return False

def transcribe_with_whisper(audio_path, model_size="base"):
    """Transcribe audio using Whisper"""
    try:
        model = load_whisper_model(model_size)
        result = model.transcribe(audio_path)
        return result["text"], "whisper"
    except Exception as e:
        return None, f"Transcription failed: {str(e)}"

# User input section
video_url = st.text_input(
    "🔗 YouTube Video URL",
    placeholder="https://www.youtube.com/watch?v=... or https://youtu.be/...",
    help="Paste any YouTube video URL here"
)

# Model selection in sidebar
st.sidebar.title("⚙️ Settings")
whisper_model = st.sidebar.selectbox(
    "Whisper Model Size",
    ["tiny", "base", "small", "medium"],
    index=1,
    help="Larger models are more accurate but slower"
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Model Info:**")
st.sidebar.markdown("- **tiny**: Fastest (~1min per 10min video)")
st.sidebar.markdown("- **base**: Recommended balance")
st.sidebar.markdown("- **small**: Better accuracy")
st.sidebar.markdown("- **medium**: Best accuracy (slower)")

# Process button
if st.button("🚀 Generate Transcript", type="primary"):
    if video_url:
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Try existing captions
            status_text.text("🔍 Checking for existing captions...")
            progress_bar.progress(20)
            
            transcript, method = get_existing_transcript(video_url)
            
            if transcript and method == "captions":
                status_text.text("✅ Found existing captions!")
                progress_bar.progress(100)
                
                # Display results
                st.success("🎉 Transcript generated successfully using existing captions!")
                
                # Create tabs for better organization
                tab1, tab2 = st.tabs(["📄 Transcript", "💾 Download"])
                
                with tab1:
                    st.text_area("Transcript Content", transcript, height=400)
                
                with tab2:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📥 Download as TXT",
                            transcript,
                            file_name=f"transcript_{extract_video_id(video_url)}.txt",
                            mime="text/plain"
                        )
                    with col2:
                        # Copy to clipboard info
                        st.info("💡 You can also copy the text directly from the transcript area above")
                
            else:
                # Step 2: Use Whisper for videos without captions
                status_text.text("🎵 No captions found. Downloading audio...")
                progress_bar.progress(40)
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    audio_path = os.path.join(temp_dir, "audio.%(ext)s")
                    
                    if download_audio(video_url, audio_path):
                        status_text.text("🤖 Transcribing with Whisper AI...")
                        progress_bar.progress(70)
                        
                        # Find the actual downloaded file
                        audio_files = [f for f in os.listdir(temp_dir) if f.startswith("audio")]
                        if audio_files:
                            actual_audio_path = os.path.join(temp_dir, audio_files[0])
                            transcript, method = transcribe_with_whisper(actual_audio_path, whisper_model)
                            
                            if transcript:
                                status_text.text("✅ AI transcription completed!")
                                progress_bar.progress(100)
                                
                                st.success("🎉 Transcript generated successfully using AI speech recognition!")
                                
                                # Create tabs
                                tab1, tab2 = st.tabs(["📄 Transcript", "💾 Download"])
                                
                                with tab1:
                                    st.text_area("AI-Generated Transcript", transcript, height=400)
                                
                                with tab2:
                                    st.download_button(
                                        "📥 Download as TXT",
                                        transcript,
                                        file_name=f"ai_transcript_{extract_video_id(video_url)}.txt",
                                        mime="text/plain"
                                    )
                                
                                st.info(f"📊 Generated using Whisper '{whisper_model}' model")
                            else:
                                st.error("❌ Failed to transcribe audio")
                        else:
                            st.error("❌ Audio file not found after download")
                    else:
                        st.error("❌ Failed to download video audio")
                
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
        finally:
            progress_bar.empty()
            status_text.empty()
    else:
        st.error("⚠️ Please enter a YouTube URL")

# Add helpful information
with st.expander("📖 How to Use"):
    st.markdown("""
    **Step 1:** Paste any YouTube video URL in the input field above
    
    **Step 2:** Choose your preferred Whisper model size in the sidebar:
    - **tiny**: Fastest processing, good for testing
    - **base**: Recommended for most users (good balance)
    - **small**: Better accuracy, takes longer
    - **medium**: Best accuracy, slowest processing
    
    **Step 3:** Click "Generate Transcript"
    
    **Step 4:** Wait for processing:
    - Videos with existing captions: ~2-5 seconds ⚡
    - Videos without captions: 1-5 minutes (depends on video length and model size) 🤖
    
    **Step 5:** View and download your transcript!
    """)

with st.expander("🔧 Troubleshooting"):
    st.markdown("""
    **Common Issues:**
    - **Slow processing:** Try a smaller Whisper model (tiny/base)
    - **Download fails:** Some videos may be restricted or private
    - **Out of memory:** Use 'tiny' model for very long videos
    - **Poor transcription quality:** Try 'medium' model for better accuracy
    
    **Supported URLs:**
    - `https://www.youtube.com/watch?v=VIDEO_ID`
    - `https://youtu.be/VIDEO_ID`
    - `https://www.youtube.com/embed/VIDEO_ID`
    """)

with st.expander("🔧 Debug Information"):
    if video_url:
        video_id = extract_video_id(video_url)
        st.write(f"**Input URL:** {video_url}")
        st.write(f"**Extracted Video ID:** {video_id}")
        st.write(f"**Video ID Length:** {len(video_id) if video_id else 'None'}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>🔥 Built with Streamlit, OpenAI Whisper, and youtube-transcript-api</p>
        <p>💡 Free • Open Source • No Data Stored</p>
    </div>
    """, 
    unsafe_allow_html=True
)
