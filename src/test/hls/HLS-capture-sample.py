import subprocess
import time
from typing import List
import io
from PIL import Image
import threading
import queue
import json

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



def capture_screenshots_from_hls(stream_url: str, num_images: int, interval: float, resolution: tuple = None, timeout: float = 300.0, max_retries: int = 70) -> List[bytes]:
    """
    Captures multiple screenshots from an HLS video stream at specified intervals with retry mechanism.
    
    :param stream_url: URL of the HLS stream
    :param num_images: Number of images to capture
    :param interval: Interval between captures in seconds
    :param resolution: Tuple of (width, height). If None, assumes 1280x720.
    :param timeout: Total timeout for the entire capture process in seconds
    :param max_retries: Maximum number of consecutive retries before giving up
    :return: List of image data as bytes
    """
    images = []
    print(f"Debug 1: Starting capture. URL: {stream_url}, Images: {num_images}, Interval: {interval}s")

    # Default resolution if not provided
    if resolution is None:
        width, height = get_video_resolution(stream_url)
    else:
        width, height = resolution

    frame_size = width * height * 3  # 3 bytes per pixel for RGB24
    print(f"Debug 2: Using resolution {width}x{height}")

    def start_ffmpeg_process():
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', stream_url,
            '-vf', f'fps=1/{interval},scale={width}:{height}',
            '-f', 'rawvideo',
            '-pix_fmt', 'rgb24',
            '-'
        ]
        print(f"Debug 3: FFmpeg command: {' '.join(ffmpeg_cmd)}")
        return subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def read_frames(process, frame_queue, stop_event):
        while not stop_event.is_set():
            try:
                frame_data = process.stdout.read(frame_size)
                if len(frame_data) == frame_size:
                    frame_queue.put(frame_data)
                else:
                    break  # End of stream or error
            except Exception as e:
                print(f"Debug Error: {str(e)}")
                break

    start_time = time.time()
    retry_count = 0
    process = None
    read_thread = None
    frame_queue = queue.Queue()
    stop_event = threading.Event()

    try:
        while len(images) < num_images and time.time() - start_time < timeout:
            if process is None or process.poll() is not None:
                if process:
                    process.terminate()
                    process.wait(timeout=5)
                if read_thread and read_thread.is_alive():
                    stop_event.set()
                    read_thread.join(timeout=5)
                
                stop_event.clear()
                frame_queue = queue.Queue()
                process = start_ffmpeg_process()
                read_thread = threading.Thread(target=read_frames, args=(process, frame_queue, stop_event))
                read_thread.start()
                print("Debug 4: FFmpeg process (re)started")
                time.sleep(interval)  # Give some time for the stream to initialize

            try:
                frame_data = frame_queue.get(timeout=interval)
                print(f"Debug 5.1: Frame data read for image {len(images) + 1}/{num_images}")
                
                # Convert raw frame data to PIL Image
                image = Image.frombytes('RGB', (width, height), frame_data)
                
                # Convert PIL Image to PNG bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                images.append(img_byte_arr.getvalue())

                print(f"Debug 5.2: Image {len(images)} processed and added")
                retry_count = 0  # Reset retry count on successful frame capture
            except queue.Empty:
                print(f"Debug 5.3: No new frame available after waiting {interval} seconds")
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"Debug 5.4: Max retries ({max_retries}) reached. Restarting connection.")
                    process = None  # This will trigger a reconnection in the next iteration
                    retry_count = 0

        print("Debug 6: Capture complete or timeout reached")

    finally:
        if process:
            process.terminate()
            process.wait(timeout=5)
        stop_event.set()
        if read_thread and read_thread.is_alive():
            read_thread.join(timeout=5)
        
        print(f"Debug 7: Process terminated. Total images captured: {len(images)}")

        # Check FFmpeg output for errors
        if process:
            stderr_output = process.stderr.read().decode('utf-8')
            if stderr_output:
                print(f"Debug 8: FFmpeg stderr output:\n{stderr_output}")

        return images

    # except subprocess.CalledProcessError as e:
    #     print(f"Debug Error 1: FFmpeg error: {e.stderr.decode()}")
    #     raise RuntimeError(f"FFmpeg error: {e.stderr.decode()}")
    # except Exception as e:
    #     print(f"Debug Error 2: Unexpected error: {str(e)}")
    #     raise RuntimeError(f"Error capturing screenshots: {str(e)}")

    

def binary_to_image(binary_data, output_path):
    """Save binary data as an image file."""
    try:
        with open(output_path, 'wb') as file:
            file.write(binary_data)
        print(f"Image saved successfully: {output_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied when writing to {output_path}. Check your write permissions.")
    except IOError as e:
        raise IOError(f"Error writing image file: {str(e)}")


def save_images(image_list, output_dir):
    for index, image_data in enumerate(image_list):
        output_path = f"{output_dir}/image_{index:03d}.png"
        binary_to_image(image_data, output_path)
        print(f"Saved image {index} to {output_path}")



# stream_url = "http://183.88.214.137:1935/livecctv/cctvp2c003.stream/playlist.m3u8"
stream_url = "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase8/PER_8_013.stream/playlist.m3u8"
num_images = 3
interval = 2  # seconds

image_list = capture_screenshots_from_hls(stream_url, num_images, interval)
print(f"total element in the list is {len(image_list)}")

output_directory = "screenshots"

save_images(image_list, output_directory)










# Now image_list contains 5 images as bytes, captured at 4-second intervals