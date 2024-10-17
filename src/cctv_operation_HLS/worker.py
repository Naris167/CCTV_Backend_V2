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
from cctv_operation_HLS.getDataHLS import capture_screenshots

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




# def scrape_image_HLS(semaphore: Semaphore,
#                      camera_id: str,
#                      HLS_Link: str,
#                      image_result: List[Tuple[str, Tuple[bytes, ...], Tuple[datetime, ...]]],
#                      working_cctv: Dict[str, str],
#                      unresponsive_cctv: Dict[str, str],
#                      interval: float,
#                      target_image_count: int,
#                      timeout: float,
#                      max_retries: int
#                      ) -> None:
#     with semaphore:
#         try:
#             logger.info(f"[SCRAPER-HLS] Starting capturing for CCTV {camera_id}")
            
#             image_png, image_time = capture_screenshots(camera_id, HLS_Link, target_image_count, interval, max_retries, timeout)
                    
#             logger.info(f"[SCRAPER-HLS] CCTV {camera_id} capture complete. Total images captured: {len(image_png)}/{target_image_count}")
#             with cctv_working_lock.gen_wlock():
#                 working_cctv[camera_id] = HLS_Link
#                 image_result.append((camera_id, image_png, image_time))
            
#         except Exception as e:
#             logger.error(f"[SCRAPER-HLS] Error scraping camera {camera_id}: {str(e)}")
#             with cctv_unresponsive_lock.gen_wlock():
#                 unresponsive_cctv[camera_id] = HLS_Link
#         finally:
#             semaphore.release()


def scrape_image_HLS(semaphore: Semaphore,
                     camera_id: str,
                     HLS_Link: str,
                     image_result: List[Tuple[str, Tuple[bytes, ...], Tuple[datetime, ...]]],
                     working_cctv: Dict[str, str],
                     unresponsive_cctv: Dict[str, str],
                     interval: float,
                     target_image_count: int,
                     timeout: float,
                     max_retries: int
                     ) -> None:
    with semaphore:
        try:
            logger.info(f"[SCRAPER-HLS] Starting capturing for CCTV {camera_id}")
            
            image_png, image_time = capture_screenshots(camera_id, HLS_Link, target_image_count, interval, max_retries, timeout)
                    
            logger.info(f"[SCRAPER-HLS] CCTV {camera_id} capture complete. Total images captured: {len(image_png)}/{target_image_count}")
            with cctv_working_lock.gen_wlock():
                working_cctv[camera_id] = HLS_Link
                image_result.append((camera_id, image_png, image_time))
            
        except Exception as e:
            logger.error(f"[SCRAPER-HLS] Error scraping camera {camera_id}: {str(e)}")
            with cctv_unresponsive_lock.gen_wlock():
                unresponsive_cctv[camera_id] = HLS_Link
        finally:
            semaphore.release()
