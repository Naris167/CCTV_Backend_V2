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
from cctv_operation_HLS.getDataHLS import get_video_resolution, start_ffmpeg_process

# Locks for thread safety
# alive_sessions_lock = rwlock.RWLockFair()
# cctv_fail_lock = rwlock.RWLockFair()
cctv_working_lock = rwlock.RWLockFair()
cctv_unresponsive_lock = rwlock.RWLockFair()

def check_cctv_status(semaphore, cctv_id, cctv_url, working_cctv, unresponsive_cctv):
    with semaphore:
        try:
            response = requests.get(cctv_url, timeout=10)
            if response.status_code == 200:
                with cctv_working_lock.gen_wlock():
                    working_cctv[cctv_id] = cctv_url
                    logger.info(f"[HLS-Verify-1] CCTV {cctv_id} response with {response.status_code}.")
            else:
                with cctv_unresponsive_lock.gen_wlock():
                    unresponsive_cctv[cctv_id] = cctv_url
                    logger.error(f"[HLS-Verify-1] CCTV {cctv_id} response with {response.status_code}.")
        except requests.RequestException as e:
            with cctv_unresponsive_lock.gen_wlock():
                unresponsive_cctv[cctv_id] = cctv_url
                logger.error(f"[HLS-Verify-1] CCTV {cctv_id} got response exception {str(e)}.")
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
            logger.info(f"Starting capture. URL: {HLS_Link}, Images: {target_image_count}, Interval: {interval}s")
            
            # Get resolution
            if resolution is None:
                width, height = get_video_resolution(HLS_Link)
            else:
                width, height = map(int, resolution)
            logger.info(f"Using resolution {width}x{height}")

            # Capture images
            image_png, image_time = [], []
            start_time = time.time()
            frame_size = width * height * 3  # 3 bytes per pixel for RGB24
            process = None
            read_thread = None
            frame_queue = queue.Queue()
            stop_flag = threading.Event()
            retry_count = 0
            fail = 0

            while len(image_png) < target_image_count and time.time() - start_time < timeout:
                if fail >= max_fail:
                    raise Exception(f"{camera_id} Failed after retry {fail} times")

                if process is None or process.poll() is not None:
                    if process:
                        process.terminate()
                        process.wait(timeout=5)
                    if read_thread and read_thread.is_alive():
                        stop_flag.set()
                        read_thread.join(timeout=5)

                    # Start FFmpeg process
                    stop_flag.clear()
                    frame_queue = queue.Queue()
                    process = start_ffmpeg_process(HLS_Link, interval, width, height)
                    read_thread = threading.Thread(
                        target=read_frame_HLS,
                        args=(camera_id, process, frame_size, frame_queue, stop_flag)
                    )
                    read_thread.start()
                    logger.info("FFmpeg process started")
                    time.sleep(wait_before_get_image)  # Give some time for the stream to initialize


                try:
                    frame_data = frame_queue.get(timeout=wait_to_get_image)
                    image_time.append(datetime.now())
                    logger.info(f"Frame data read for image {len(image_png) + 1}")
                    
                    image = Image.frombytes('RGB', (width, height), frame_data)
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='PNG')
                    image_png.append(img_byte_arr.getvalue())

                    logger.info(f"Image {len(image_png)} processed and added")
                    retry_count = 0
                except queue.Empty:
                    logger.info(f"No new frame available after waiting {wait_before_get_image + wait_to_get_image} seconds")
                    retry_count += 1
                    fail += 1
                    if retry_count >= max_retries:
                        logger.info(f"Debug 5.4: Max retries ({max_retries}) reached. Restarting connection.")
                        process = None  # This will trigger a reconnection in the next iteration
                        retry_count = 0



            logger.info(f"Capture complete. Total images captured: {len(image_png)}")
            with cctv_working_lock.gen_wlock():
                working_cctv[camera_id] = HLS_Link
                image_result.append((camera_id, tuple(image_png), tuple(image_time)))
            
        except Exception as e:
            logger.error(f"Error scraping camera {camera_id}: {str(e)}")
            with cctv_unresponsive_lock.gen_wlock():
                unresponsive_cctv[camera_id] = HLS_Link
        finally:
            semaphore.release()


def read_frame_HLS(camera_id, process, frame_size, frame_queue, stop_flag):
    while not stop_flag.is_set():
        try:
            frame_data = process.stdout.read(frame_size)
            if len(frame_data) == frame_size:
                frame_queue.put(frame_data)
            else:
                break  # End of stream or error
        except Exception as e:
            raise RuntimeError(f"Error HLS frame reader for camera {camera_id}: {str(e)}")
