import subprocess
import json
import os
import re
from utils.utils import binary_to_image
from utils.Database import insert_data, retrieve_data
import concurrent.futures
import datetime
from typing import List, Tuple
import threading

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

def capture_one_screenshot_from_hls(stream_url):
    """Captures a single frame from an HLS stream and saves it as an image."""
    # try:
    #     os.makedirs(output_dir, exist_ok=True)
    # except PermissionError:
    #     raise PermissionError(f"Permission denied when creating directory {output_dir}. Check your write permissions.")

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

def filter_cctv_list(cctv_list: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    pattern = re.compile(r'kk\d+\.m3u8$')
    return [
        (cam_id, stream_link) for cam_id, stream_link in cctv_list
        if pattern.search(stream_link)
    ]

def capture_screenshots(cam_id: str, stream_url: str, num_images: int) -> List[Tuple[str, bytes, str]]:
    results = []
    for _ in range(num_images):
        image_data = capture_one_screenshot_from_hls(stream_url)
        timestamp = datetime.datetime.now().isoformat()
        results.append((cam_id, image_data, timestamp))
    return results

def process_stream(cam_id: str, stream_url: str, num_images: int) -> List[Tuple[str, bytes, str]]:
    return capture_screenshots(cam_id, stream_url, num_images)


if __name__ == "__main__":
    try:
        # Retrieve CCTV locations and stream links from the database
        table = 'cctv_locations_general'
        columns = ['Cam_ID', 'Stream_Link_1']
        cctv_data = retrieve_data(table, columns)

        # Filter the CCTV list
        filtered_cctv_data = filter_cctv_list(cctv_data)

        num_images_per_cam = 3  # Specify the number of images you want per camera
        max_workers = min(32, len(filtered_cctv_data))  # Adjust the number of workers as needed

        all_results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_cam = {executor.submit(process_stream, cam_id, stream_url, num_images_per_cam): cam_id 
                             for cam_id, stream_url in filtered_cctv_data}
            
            for future in concurrent.futures.as_completed(future_to_cam, timeout=60):
                cam_id = future_to_cam[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as exc:
                    print(f"{cam_id} generated an exception: {exc}")

        # Insert all captured data into the database
        insert_data('cctv_images_general', ['Cam_ID', 'Image_data', 'Captured_at'], all_results)
        # Save images to disk
        # output_directory = r"C:\Users\naris\Desktop\TEST"
        # for cam_id, image_data, timestamp in all_results:
        #     # Create a unique filename for each image
        #     filename = f"{cam_id}_{timestamp.replace(':', '-')}.jpg"
        #     output_path = os.path.join(output_directory, filename)
            
        #     # Call the binary_to_image function to save the image
        #     binary_to_image(image_data, output_path)

    except Exception as e:
        print(f"An error occurred: {str(e)}")