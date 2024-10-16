import subprocess
import json
import os
from utils.utils import binary_to_image
from utils.log_config import logger

def get_video_resolution(camera_id, stream_url):
    """Get the resolution (width, height) of the video stream using ffprobe."""
    ffprobe_cmd = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height', '-of', 'json', stream_url
    ]
    try:
        result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(result.stdout)
        width = probe_data['streams'][0]['width']
        height = probe_data['streams'][0]['height']
        
        logger.info(f"[{camera_id}] Detected CCTV resolution of W:{width} x H:{height}")
        
        return width, height
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, IndexError) as e:
        raise RuntimeError(f"[{camera_id}] Failed to get CCTV resolution: {str(e)}")


def start_ffmpeg_process(camera_id, stream_url, interval, width, height):
    try:
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', stream_url,
            '-vf', f'fps=1/{interval},scale={width}:{height}',
            '-f', 'rawvideo',
            '-pix_fmt', 'rgb24',
            '-'
        ]

        logger.info(f"[{camera_id}] Started FFmpeg sub process")
        
        return subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"[{camera_id}] FFmpeg error: {e.stderr.decode()}")
    except Exception as e:
        raise RuntimeError(f"[{camera_id}] Error capturing screenshots: {str(e)}")


def read_frame_ffmpeg_process(camera_id, process, frame_size, frame_queue, stop_flag):
    while not stop_flag.is_set():
        logger.info(f"[{camera_id}] HLS frame reader started")
        try:
            frame_data = process.stdout.read(frame_size)
            if len(frame_data) == frame_size:
                frame_queue.put(frame_data)
            else:
                break  # End of stream or error
        except Exception as e:
            raise RuntimeError(f"[{camera_id}] Error HLS frame reader: {str(e)}")




# def capture_one_screenshot_from_hls(stream_url):
#     """Captures a single frame from an HLS stream and saves it as an image."""

#     try:
#         width, height = get_video_resolution(stream_url)
#         print(f"Detected video resolution: {width}x{height}")

#         ffmpeg_cmd = [
#             'ffmpeg', '-i', stream_url, '-vframes', '1',
#             '-f', 'image2pipe', '-vcodec', 'png', '-'
#         ]
#         result = subprocess.run(ffmpeg_cmd, capture_output=True, check=True)
#         return result.stdout

#     except subprocess.CalledProcessError as e:
#         raise RuntimeError(f"FFmpeg error: {e.stderr.decode()}")
#     except Exception as e:
#         raise RuntimeError(f"Error capturing screenshot: {str(e)}")

# if __name__ == "__main__":
#     stream_url = "https://camera1.iticfoundation.org/hls/10.8.0.17_8002.m3u8"
#     output_dir = './captured_screenshot'
#     try:
#         image = capture_one_screenshot_from_hls(stream_url, output_dir)
#         frame_filename = os.path.join(output_dir, 'screenshot.png')
#         binary_to_image(image, frame_filename)
#     except Exception as e:
#         print(f"An error occurred: {str(e)}")