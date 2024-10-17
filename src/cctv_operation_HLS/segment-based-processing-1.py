import subprocess
import json
import requests
import time
import re
import tempfile
import os

def download_m3u8(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return f"Error downloading m3u8: {str(e)}"

def get_segment_url(m3u8_url, m3u8_content):
    base_url = m3u8_url.rsplit('/', 1)[0] + '/'
    segment_name = re.search(r'#EXTINF:.*\n(.+)', m3u8_content).group(1)
    return base_url + segment_name

def download_segment(segment_url):
    try:
        response = requests.get(segment_url, timeout=30)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        return f"Error downloading segment: {str(e)}"

def ffprobe_segment(segment_data):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ts') as temp_file:
        temp_file.write(segment_data)
        temp_file_path = temp_file.name

    ffprobe_command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'stream=codec_type,codec_name,width,height,avg_frame_rate,bit_rate',
        '-of', 'json',
        temp_file_path
    ]
    try:
        result = subprocess.run(ffprobe_command, capture_output=True, text=True, timeout=10)
        os.unlink(temp_file_path)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, ffprobe_command, result.stderr)
        return json.loads(result.stdout)
    except Exception as e:
        os.unlink(temp_file_path)
        return f"Error analyzing segment with ffprobe: {str(e)}"

def diagnose_stream(url):
    print(f"Diagnosing stream: {url}")
    
    m3u8_content = download_m3u8(url)
    print("\n1. M3U8 Playlist Content:")
    print(m3u8_content)
    
    segment_url = get_segment_url(url, m3u8_content)
    print(f"\n2. Segment URL: {segment_url}")
    
    segment_data = download_segment(segment_url)
    if isinstance(segment_data, bytes):
        print(f"Successfully downloaded segment ({len(segment_data)} bytes)")
        
        print("\n3. FFprobe Segment Analysis:")
        ffprobe_result = ffprobe_segment(segment_data)
        print(json.dumps(ffprobe_result, indent=2))
    else:
        print(segment_data)  # Print error message

# Test both URLs
urls = [
    "https://camerai1.iticfoundation.org/hls/pty56.m3u8",
    "https://camerai1.iticfoundation.org/hls/pty71.m3u8"
]

for url in urls:
    diagnose_stream(url)
    print("\n" + "="*50 + "\n")