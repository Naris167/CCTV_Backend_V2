import cv2
import time
import os
from datetime import datetime, timedelta
from utils.utils import save_cctv_images

import cv2
import time
from datetime import datetime

def capture_screenshots(name, url, num_images=5, interval=10):
    print(f"Connecting to {name}...")
    
    captured_images = 0
    last_capture_time = None
    image_data = []
    capture_times = []
    
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        print(f"{name}: Unable to open video stream")
        return [], []

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        print(f"{name}: Unable to determine stream FPS, using 30 as default")
        fps = 30

    while captured_images < num_images:
        try:
            current_time = time.time()

            # Check if enough time has passed since the last capture
            if last_capture_time is None or (current_time - last_capture_time) >= interval:
                # Skip frames to reach the desired interval
                frames_to_skip = int(fps * interval)
                for _ in range(frames_to_skip):
                    cap.grab()

                ret, frame = cap.read()
                if not ret:
                    print(f"{name}: Error reading frame, reconnecting...")
                    cap.release()
                    time.sleep(1)
                    cap = cv2.VideoCapture(url)
                    continue

                # Convert frame to bytes
                _, buffer = cv2.imencode('.jpg', frame)
                image_bytes = buffer.tobytes()
                
                # Store image bytes and capture time
                image_data.append(image_bytes)
                capture_times.append(datetime.now())
                
                captured_images += 1
                last_capture_time = current_time
                print(f"{name}: Screenshot {captured_images}/{num_images} captured")
            else:
                # Wait for the remaining interval
                wait_time = interval - (current_time - last_capture_time)
                if wait_time > 0:
                    time.sleep(wait_time)

        except Exception as e:
            print(f"{name}: Error occurred - {str(e)}")
            time.sleep(interval)

    cap.release()
    print(f"{name}: Captured {num_images} screenshots")
    
    return tuple(image_data), tuple(capture_times)



# Example usage
image_data, capture_times = capture_screenshots("pty71", "https://camerai1.iticfoundation.org/hls/pty71.m3u8", num_images=10, interval=1)
save_cctv_images([("pty71", image_data, capture_times)], "./data/screenshot", "TODAY")


# cctvLinks = {
#     "cctvp2c003": "http://183.88.214.137:1935/livecctv/cctvp2c003.stream/playlist.m3u8",
#     "ITICM_BMAMI0133": "https://camerai1.iticfoundation.org/hls/ccs05.m3u8",
#     "ITICM_BMAMI0272": "https://camerai1.iticfoundation.org/hls/pty71.m3u8",
#     "ITICM_BMAMI0237": "https://camerai1.iticfoundation.org/hls/kk24.m3u8",
#     "ITICM_BMAMI0257": "https://camerai1.iticfoundation.org/hls/pty56.m3u8"
# }
