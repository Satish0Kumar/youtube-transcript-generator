from youtube_transcript_api import YouTubeTranscriptApi

video_id = "LadcLQIKbNY"
print(f"Testing video ID: {video_id}")

try:
    # NEW API: Create instance and use fetch()
    ytt_api = YouTubeTranscriptApi()
    fetched_transcript = ytt_api.fetch(video_id)
    
    print("✅ SUCCESS: Found transcript!")
    print(f"📊 Total entries: {len(fetched_transcript)}")
    print(f"🎯 Video ID: {fetched_transcript.video_id}")
    print(f"🌍 Language: {fetched_transcript.language}")
    
    print("\n📝 First few lines:")
    for i, snippet in enumerate(fetched_transcript[:3]):
        timestamp = f"{int(snippet.start//60):02d}:{int(snippet.start%60):02d}"
        print(f"[{timestamp}] {snippet.text}")
        
    # Convert to raw data (list of dictionaries) if needed
    raw_data = fetched_transcript.to_raw_data()
    print(f"\n🔧 Raw data sample: {raw_data[0]}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
