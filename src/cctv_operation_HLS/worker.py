from utils.log_config import logger
from readerwriterlock import rwlock
from threading import Semaphore
import threading
import time
import queue
from PIL import Image
import json
import subprocess
import io
from typing import List, Dict, Tuple, Optional, Union
from datetime import datetime
import requests

from utils.utils import detect_movement, select_images_and_datetimes
from cctv_operation_HLS.getDataHLS import get_video_resolution, start_ffmpeg_process, read_frame_ffmpeg_process

# Locks for thread safety
# alive_sessions_lock = rwlock.RWLockFair()
# cctv_fail_lock = rwlock.RWLockFair()
cctv_working_lock = rwlock.RWLockFair()
cctv_unresponsive_lock = rwlock.RWLockFair()

def check_cctv_status(semaphore, cctv_id, cctv_url, working_cctv, offline_cctv):
    with semaphore:
        try:
            response = requests.get(cctv_url, timeout=10)
            if response.status_code == 200:
                with cctv_working_lock.gen_wlock():
                    working_cctv[cctv_id] = cctv_url
                    logger.info(f"[HLS-Status] CCTV {cctv_id} response with {response.status_code}.")
            else:
                with cctv_unresponsive_lock.gen_wlock():
                    offline_cctv[cctv_id] = cctv_url
                    logger.error(f"[HLS-Status] CCTV {cctv_id} response with {response.status_code}.")
        except requests.RequestException as e:
            with cctv_unresponsive_lock.gen_wlock():
                offline_cctv[cctv_id] = cctv_url
                logger.error(f"[HLS-Status] CCTV {cctv_id} got response exception {str(e)}.")
        finally:
            semaphore.release()




def scrape_image_HLS(semaphore: Semaphore,
                     camera_id: str,
                     HLS_Link: str,
                     image_result: List[Tuple[str, Tuple[bytes], Tuple[datetime]]],
                     working_cctv: Dict[str, str],
                     unresponsive_cctv: Dict[str, str],
                     interval: float,
                     wait_before_get_image: int,
                     wait_to_get_image: int,
                     target_image_count: int,
                     timeout: float,
                     max_retries: int,
                     max_fail: int,
                     resolution: Optional[Tuple[str, str]]
                     ) -> None:
    with semaphore:
        try:
            logger.info(f"[SCRAPER-HLS] Starting capturing for CCTV {camera_id}")
            
            # Get resolution
            if resolution is None:
                width, height = get_video_resolution(camera_id, HLS_Link)
            else:
                width, height = map(int, resolution)
                logger.info(f"[SCRAPER-HLS] Manual resolution (W:{width} x H:{height}) is provided for CCTV {camera_id}")

            # Capture images
            image_png, image_time = [], []
            start_time = time.time()
            frame_size = width * height * 3  # 3 bytes per pixel for RGB24
            process = None
            read_thread = None
            frame_queue = queue.Queue()
            stop_flag = threading.Event()
            iteration_count = 1
            fail_count = 0

            while len(image_png) < target_image_count and time.time() - start_time < timeout:
                if process is None:
                    # Start FFmpeg process
                    stop_flag.clear()
                    frame_queue = queue.Queue()
                    process = start_ffmpeg_process(camera_id, HLS_Link, interval, width, height)
                    read_thread = threading.Thread(
                        target=read_frame_ffmpeg_process,
                        args=(camera_id, process, frame_size, frame_queue, stop_flag)
                    )
                    read_thread.start()
                    
                    time.sleep(wait_before_get_image)  # Give some time for the stream to initialize

                try:
                    frame_data = frame_queue.get(timeout=wait_to_get_image)
                    image_time.append(datetime.now())
                    logger.info(f"[SCRAPER-HLS] Frame data [{len(image_png) + 1}/{target_image_count}] read for CCTV [{camera_id}][F:{fail_count}][I:{iteration_count}]")
                    
                    image = Image.frombytes('RGB', (width, height), frame_data)
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='PNG')
                    image_png.append(img_byte_arr.getvalue())

                    logger.info(f"[SCRAPER-HLS] Image [{len(image_png)}/{target_image_count}] processed and added for CCTV [{camera_id}]")
                    iteration_count = 1
                except queue.Empty:
                    end_time = time.time()
                    logger.info(f"[SCRAPER-HLS] No new frame available for CCTV [{camera_id}][F:{fail_count}][I:{iteration_count}] after waiting {end_time - start_time} seconds (current image count: {len(image_png)}/{target_image_count})")
                    iteration_count += 1
                    
                    if iteration_count > max_retries:
                        fail_count += 1
                        logger.warning(f"[SCRAPER-HLS] Max retries reached for CCTV {camera_id}. Incrementing fail count to {fail_count}")
                        if fail_count >= max_fail:
                            raise Exception(f"Aborted scraping after {fail_count} fails")
                        logger.warning(f"[SCRAPER-HLS] Restarting connection for CCTV {camera_id}")
                        
                        # Kill the subprocess and reset
                        if process:
                            process.terminate()
                            process.wait(timeout=5)
                        if read_thread and read_thread.is_alive():
                            stop_flag.set()
                            read_thread.join(timeout=5)
                        
                        process = None  # This will trigger a reconnection in the next iteration
                        iteration_count = 1  # Reset iteration count
                    

            # If it is timeout, it should not fall here
            logger.info(f"[SCRAPER-HLS] CCTV {camera_id} capture complete. Total images captured: {len(image_png)}/{target_image_count}")
            with cctv_working_lock.gen_wlock():
                working_cctv[camera_id] = HLS_Link
                image_result.append((camera_id, tuple(image_png), tuple(image_time)))
            
        except Exception as e:
            logger.error(f"[SCRAPER-HLS] Error scraping camera {camera_id}: {str(e)}")
            with cctv_unresponsive_lock.gen_wlock():
                unresponsive_cctv[camera_id] = HLS_Link
        finally:
            semaphore.release()



