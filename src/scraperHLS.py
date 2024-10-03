import subprocess
import json
import os
from utils import binary_to_image

def get_video_resolution(stream_url):
    """Get the resolution (width, height) of the video stream using ffprobe."""
    ffprobe_cmd = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height', '-of', 'json', stream_url
    ]
    try:
        result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(result.stdout)
        return (
            probe_data['streams'][0]['width'],
            probe_data['streams'][0]['height']
        )
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, IndexError) as e:
        raise RuntimeError(f"Failed to get video resolution: {str(e)}")

def capture_one_screenshot_from_hls(stream_url, output_dir):
    """Captures a single frame from an HLS stream and saves it as an image."""
    try:
        os.makedirs(output_dir, exist_ok=True)
    except PermissionError:
        raise PermissionError(f"Permission denied when creating directory {output_dir}. Check your write permissions.")

    try:
        width, height = get_video_resolution(stream_url)
        print(f"Detected video resolution: {width}x{height}")

        ffmpeg_cmd = [
            'ffmpeg', '-i', stream_url, '-vframes', '1',
            '-f', 'image2pipe', '-vcodec', 'png', '-'
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, check=True)
        return result.stdout

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg error: {e.stderr.decode()}")
    except Exception as e:
        raise RuntimeError(f"Error capturing screenshot: {str(e)}")

if __name__ == "__main__":
    stream_url = "https://camera1.iticfoundation.org/hls/10.8.0.17_8002.m3u8"
    output_dir = './captured_screenshot'
    try:
        image = capture_one_screenshot_from_hls(stream_url, output_dir)
        frame_filename = os.path.join(output_dir, 'screenshot.png')
        binary_to_image(image, frame_filename)
    except Exception as e:
        print(f"An error occurred: {str(e)}")