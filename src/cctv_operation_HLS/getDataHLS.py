import cv2
import time
from datetime import datetime
from utils.log_config import logger
from typing import Tuple, List, Optional


def capture_screenshots(
    camera_id: str,
    stream_url: str,
    num_images: int = 1,
    interval: float = 1,
    max_retries: int = 3,
    timeout: float = 30
) -> Tuple[Tuple[bytes, ...], Tuple[datetime, ...]]:
    
    logger.info(f"[{camera_id}] Connecting...")

    last_capture_time: Optional[float] = None
    image_data: List[bytes] = []
    capture_times: List[datetime] = []
    retries: int = 0
    
    while len(image_data) < num_images and retries < max_retries:
        try:
            cap = cv2.VideoCapture(stream_url)
            if not cap.isOpened():
                raise Exception(f"Unable to open video stream")

            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30
                logger.warning(f"[{camera_id}] Unable to determine stream FPS, using {fps} as default")
            
            start_time = time.time()

            while len(image_data) < num_images:
                current_time = time.time()
                
                if current_time - start_time > timeout:
                    logger.warning(f"[{camera_id}] Timeout reached. Reconnecting...")
                    break

                # Check if enough time has passed since the last capture
                if last_capture_time is None or (current_time - last_capture_time) >= interval:
                    # Skip frames to reach the desired interval
                    frames_to_skip = int(fps * interval)
                    for _ in range(frames_to_skip):
                        cap.grab()

                    ret, frame = cap.read()
                    if not ret:
                        logger.warning(f"[{camera_id}] Error reading frame, reconnecting...")
                        break
                    
                    # Convert frame to bytes
                    _, buffer = cv2.imencode('.png', frame)
                    image_bytes = buffer.tobytes()

                    # Check image validity
                    if len(image_bytes) <= 10000:
                        logger.warning(f"[{camera_id}] Image size less than 10 Kb, retrying...")
                        break
                    
                    # Store image bytes and capture time
                    image_data.append(image_bytes)
                    capture_times.append(datetime.now())
                    
                    last_capture_time = current_time
                    logger.info(f"[{camera_id}] Screenshot {len(image_data)}/{num_images} captured")
                else:
                    # Wait for the remaining interval
                    wait_time = interval - (current_time - last_capture_time)
                    if wait_time > 0:
                        time.sleep(min(wait_time, timeout - (current_time - start_time)))

            cap.release()

            if len(image_data) == num_images:
                break
            else:
                retries += 1
                logger.warning(f"[{camera_id}] Retry {retries}/{max_retries}")
                time.sleep(1)

        except Exception as e:
            logger.error(f"[{camera_id}] Error occurred - {str(e)}")
            retries += 1
            logger.warning(f"[{camera_id}] Retry {retries}/{max_retries}")
            time.sleep(1)

    if len(image_data) <= 0:
        raise Exception(f"Unable to capture any screenshots after {max_retries} retries")

    if len(image_data) < num_images:
        logger.warning(f"[{camera_id}] Captured only {len(image_data)}/{num_images} screenshots after {max_retries} retries")
    
    if len(image_data) >= num_images:
        logger.info(f"[{camera_id}] Captured {len(image_data)}/{num_images} screenshots")
    
    return tuple(image_data), tuple(capture_times)