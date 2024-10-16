import requests
import m3u8
import subprocess
import json
import tempfile
import os

def process_hls_stream(url, max_segments=10):
    results = []
    playlist = m3u8.load(url)
    
    for i, segment in enumerate(playlist.segments[:max_segments]):
        segment_url = segment.absolute_uri
        try:
            # Download segment
            response = requests.get(segment_url, timeout=30)
            response.raise_for_status()
            segment_data = response.content

            # Analyze segment with FFprobe
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ts') as temp_file:
                temp_file.write(segment_data)
                temp_file_path = temp_file.name

            ffprobe_command = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',  # Select only the first video stream
                '-show_entries', 'stream=codec_name,width,height,avg_frame_rate',
                '-of', 'json',
                temp_file_path
            ]

            result = subprocess.run(ffprobe_command, capture_output=True, text=True, timeout=10)
            os.unlink(temp_file_path)

            if result.returncode == 0:
                segment_info = json.loads(result.stdout)
                results.append({
                    "segment_number": i + 1,
                    "segment_url": segment_url,
                    "analysis": segment_info
                })
            else:
                results.append({
                    "segment_number": i + 1,
                    "segment_url": segment_url,
                    "error": f"FFprobe error: {result.stderr}"
                })

        except Exception as e:
            results.append({
                "segment_number": i + 1,
                "segment_url": segment_url,
                "error": str(e)
            })

    return results

# Example usage
url = "https://camerai1.iticfoundation.org/hls/pty71.m3u8"
stream_info = process_hls_stream(url)
print(json.dumps(stream_info, indent=2))