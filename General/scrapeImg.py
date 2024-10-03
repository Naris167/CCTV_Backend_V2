import cv2
import ffmpeg
import numpy as np
import os

# Function to capture one screenshot from the HLS stream
def capture_one_screenshot_from_hls(stream_url, output_dir):
    """
    Captures a single frame from an HLS stream and saves it as an image.

    :param stream_url: HLS stream URL (e.g., .m3u8 file)
    :param output_dir: Directory where the image will be saved
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Use ffmpeg to capture video from the HLS stream
    video_stream = ffmpeg.input(stream_url)

    # Open a pipe to get the first frame
    process = (
        ffmpeg
        .output(video_stream, 'pipe:', format='rawvideo', pix_fmt='rgb24', vframes=1)
        .run_async(pipe_stdout=True)
    )

    # Read the first frame's raw data
    in_bytes = process.stdout.read(1920 * 1080 * 3)  # Adjust width and height based on video resolution

    if in_bytes:
        # Convert frame to numpy array (OpenCV compatible)
        frame = (
            np.frombuffer(in_bytes, np.uint8)
            .reshape([1080, 1920, 3])  # Adjust based on your video's resolution
        )

        # Save the frame as an image
        frame_filename = os.path.join(output_dir, 'screenshot.png')
        cv2.imwrite(frame_filename, frame)
        print(f"Captured screenshot: {frame_filename}")

    # Close the process pipe
    process.stdout.close()
    process.wait()

# Usage
stream_url = "http://183.88.214.137:1935/livecctv/cctvp2c003.stream/playlist.m3u8"
output_dir = './captured_screenshot'

capture_one_screenshot_from_hls(stream_url, output_dir)
