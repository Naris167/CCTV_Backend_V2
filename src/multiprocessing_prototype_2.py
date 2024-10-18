import concurrent.futures
from typing import Callable, List, Tuple, Dict, Any, Optional
from datetime import datetime
import time
import random
import math

# Global variable to hold the cv2 module
cv2 = None

def safe_import_cv2():
    global cv2
    if cv2 is None:
        import cv2 as cv2_imported
        cv2 = cv2_imported

class MultiprocessingImageScraper:
    def __init__(self, logger):
        self.logger = logger

    def worker_func(self, func: Callable, camera_id: str, url: str, kwargs: Dict[str, Any]) -> Tuple[str, Any]:
        safe_import_cv2()
        result = func(camera_id, url, **kwargs)
        return camera_id, result

    def run_multiprocessing(self, func: Callable, 
                            max_concurrent: int,
                            working_cctv: Dict[str, str],
                            **kwargs: Any) -> Dict[str, Any]:
        
        num_pools = math.ceil(max_concurrent / 60)
        workers_per_pool = min(60, max(1, max_concurrent // num_pools))
        
        pools = [concurrent.futures.ProcessPoolExecutor(max_workers=workers_per_pool) for _ in range(num_pools)]
        
        futures = []
        for i, (camera_id, url) in enumerate(working_cctv.items()):
            pool = pools[i % num_pools]
            futures.append(pool.submit(self.worker_func, func, camera_id, url, kwargs))
        
        all_results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                all_results.append(future.result())
            except Exception as e:
                self.logger.error(f"An error occurred: {str(e)}")
        
        image_result = []
        updated_working_cctv = {}
        unresponsive_cctv = {}

        for camera_id, result in all_results:
            if result is not None:
                image_result.append(result)
                updated_working_cctv[camera_id] = working_cctv[camera_id]
            else:
                unresponsive_cctv[camera_id] = working_cctv[camera_id]

        for pool in pools:
            pool.shutdown()

        return {
            "image_result": image_result,
            "working_cctv": updated_working_cctv,
            "unresponsive_cctv": unresponsive_cctv
        }

def capture_screenshots(
    camera_id: str,
    stream_url: str,
    num_images: int = 1,
    interval: float = 1,
    max_retries: int = 3,
    timeout: float = 30,
    logger = None
) -> Tuple[Tuple[bytes, ...], Tuple[datetime, ...]]:
    safe_import_cv2()
    
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

                if last_capture_time is None or (current_time - last_capture_time) >= interval:
                    frames_to_skip = int(fps * interval)
                    for _ in range(frames_to_skip):
                        cap.grab()

                    ret, frame = cap.read()
                    if not ret:
                        logger.warning(f"[{camera_id}] Error reading frame, reconnecting...")
                        break
                    
                    _, buffer = cv2.imencode('.png', frame)
                    image_bytes = buffer.tobytes()

                    if len(image_bytes) <= 10000:
                        logger.warning(f"[{camera_id}] Image size less than 10 Kb, retrying...")
                        break
                    
                    image_data.append(image_bytes)
                    capture_times.append(datetime.now())
                    
                    last_capture_time = current_time
                    print(f"[{camera_id}] Screenshot {len(image_data)}/{num_images} captured")
                else:
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

def scrape_image_HLS(camera_id: str, HLS_Link: str, 
                    interval: float, target_image_count: int, 
                    timeout: float, max_retries: int,
                    logger = None) -> Tuple[str, Tuple[bytes, ...], Tuple[datetime, ...]] | None:
    try:
        logger.info(f"[SCRAPER-HLS] Starting capturing for CCTV {camera_id}")
            
        image_png, image_time = capture_screenshots(camera_id, HLS_Link, target_image_count, interval, max_retries, timeout, logger)
                
        logger.info(f"[SCRAPER-HLS] CCTV {camera_id} capture complete. Total images captured: {len(image_png)}/{target_image_count}")
        return camera_id, image_png, image_time
    except Exception as e:
        logger.error(f"[SCRAPER-HLS] Error scraping camera {camera_id}: {str(e)}")
        return None