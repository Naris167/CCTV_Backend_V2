import concurrent.futures
from typing import Callable, List, Tuple, Dict, Any, Optional
from datetime import datetime
import time
import random
import math

from utils.Database import retrieve_data
# from cctv_operation_HLS.getDataHLS import capture_screenshots
from utils.log_config import logger, log_setup

# def scrape_image_HLS(camera_id: str, HLS_Link: str, 
#                      interval: float, target_image_count: int, 
#                      timeout: float, max_retries: int) -> Tuple[str, Tuple[bytes, ...], Tuple[datetime, ...]] | None:
#     # Simulating some work
#     time.sleep(random.uniform(0.1, 0.5))  # Reduced sleep time for faster testing
    
#     # Simulating success or failure
#     if random.random() > 0.1:  # 90% success rate
#         # Return a tuple of (camera_id, image_data, timestamps)
#         print(f"[{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}][{camera_id}] working!!!")
#         return camera_id, (b'dummy_image',) * target_image_count, (datetime.now(),) * target_image_count
#     else:
#         # Return None to indicate failure
#         print(f"[{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}][{camera_id}] failed!!!")
#         return None



# def scrape_image_HLS(camera_id: str, HLS_Link: str, 
#                      interval: float, target_image_count: int, 
#                      timeout: float, max_retries: int) -> Tuple[str, Tuple[bytes, ...], Tuple[datetime, ...]] | None:

#     try:
#         # Return a tuple of (camera_id, image_data, timestamps)
#         logger.info(f"[SCRAPER-HLS] Starting capturing for CCTV {camera_id}")
            
#         image_png, image_time = capture_screenshots(camera_id, HLS_Link, target_image_count, interval, max_retries, timeout)
                
#         logger.info(f"[SCRAPER-HLS] CCTV {camera_id} capture complete. Total images captured: {len(image_png)}/{target_image_count}")
#         return camera_id, image_png, image_time
#     except Exception as e:
#         # Return None to indicate failure
#         logger.error(f"[SCRAPER-HLS] Error scraping camera {camera_id}: {str(e)}")
#         return None




# Global variable to hold the cv2 module
cv2 = None

def safe_import_cv2():
    global cv2
    if cv2 is None:
        import cv2 as cv2_imported
        cv2 = cv2_imported


# Ensure cv2 is not imported in the main process
def scrape_image_HLS(camera_id: str, HLS_Link: str, 
                    interval: float, target_image_count: int, 
                    timeout: float, max_retries: int) -> Tuple[str, Tuple[bytes, ...], Tuple[datetime, ...]] | None:

    # Import cv2 here
    safe_import_cv2()
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
                        print(f"[{camera_id}] Screenshot {len(image_data)}/{num_images} captured")
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
    try:
        # Return a tuple of (camera_id, image_data, timestamps)
        logger.info(f"[SCRAPER-HLS] Starting capturing for CCTV {camera_id}")
            
        image_png, image_time = capture_screenshots(camera_id, HLS_Link, target_image_count, interval, max_retries, timeout)
                
        logger.info(f"[SCRAPER-HLS] CCTV {camera_id} capture complete. Total images captured: {len(image_png)}/{target_image_count}")
        return camera_id, image_png, image_time
    except Exception as e:
        # Return None to indicate failure
        logger.error(f"[SCRAPER-HLS] Error scraping camera {camera_id}: {str(e)}")
        return None












def worker_func(func: Callable, camera_id: str, url: str, kwargs: Dict[str, Any]) -> Tuple[str, Any]:
    # Import cv2 here, after the process has been forked
    safe_import_cv2()
    result = func(camera_id, url, **kwargs)
    return camera_id, result

def run_multiprocessing(func: Callable, 
                        max_concurrent: int,
                        working_cctv: Dict[str, str],
                        **kwargs: Any) -> Dict[str, Any]:
    
    # Determine the number of pools and workers per pool
    num_pools = math.ceil(max_concurrent / 60)  # 60 workers per pool to stay within Windows limits
    workers_per_pool = min(60, max(1, max_concurrent // num_pools))
    
    # Create process pools
    pools = [concurrent.futures.ProcessPoolExecutor(max_workers=workers_per_pool) for _ in range(num_pools)]
    
    # Distribute work among pools
    futures = []
    for i, (camera_id, url) in enumerate(working_cctv.items()):
        pool = pools[i % num_pools]
        futures.append(pool.submit(worker_func, func, camera_id, url, kwargs))
    
    # Collect results
    all_results = []
    for future in concurrent.futures.as_completed(futures):
        try:
            all_results.append(future.result())
        except Exception as e:
            print(f"An error occurred: {str(e)}")
    
    # Process results
    image_result = []
    updated_working_cctv = {}
    unresponsive_cctv = {}

    for camera_id, result in all_results:
        if result is not None:
            image_result.append(result)
            updated_working_cctv[camera_id] = working_cctv[camera_id]
        else:
            unresponsive_cctv[camera_id] = working_cctv[camera_id]

    # Shutdown all pools
    for pool in pools:
        pool.shutdown()

    return {
        "image_result": image_result,
        "working_cctv": updated_working_cctv,
        "unresponsive_cctv": unresponsive_cctv
    }

if __name__ == "__main__":


    






    # Configuration and setup
    log_setup("./logs/imageScraper","TestMultiprocessor")
    config = {
        'interval': 1.0,
        'target_image_count': 5,  # Reduced for faster testing
        'timeout': 30.0,
        'max_retries': 3
    }

    # Create 1000 dummy CCTVs
    # working_cctv: Dict[str, str] = {f'cam{i}': f'link{i}' for i in range(1, 101)}
    
    # database_result = dict(retrieve_data(
    #         'cctv_locations_general',
    #         ('Cam_ID', 'Stream_Link_1'),
    #         ('Stream_Method',),
    #         ('HLS',)
    #     ))
    # working_cctv: Dict[str, str] = {
    #             # "cctvp2c003": "http://183.88.214.137:1935/livecctv/cctvp2c003.stream/playlist.m3u8",
    #             "ITICM_BMAMI0133": "https://camerai1.iticfoundation.org/hls/ccs05.m3u8",
    #             # "ITICM_BMAMI0272": "https://camerai1.iticfoundation.org/hls/pty71.m3u8", # This one have problem. It take too long to response
    #             "ITICM_BMAMI0237": "https://camerai1.iticfoundation.org/hls/kk24.m3u8",
    #             "ITICM_BMAMI0257": "https://camerai1.iticfoundation.org/hls/pty56.m3u8",
    #             "cctvp2c011": "http://183.88.214.137:1935/livecctv/cctvp2c011.stream/playlist.m3u8",
    #             "ITICM_BMAMI0240": "https://camerai1.iticfoundation.org/hls/kk27.m3u8",
    #             "ITICM_BMAMI0186": "https://camerai1.iticfoundation.org/hls/ccs41.m3u8",
    #             "DOH-PER-3-006": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase3/PER_3_006_IN.stream/playlist.m3u8",
    #             # "cctvp2c001": "http://183.88.214.137:1935/livecctv/cctvp2c001.stream/playlist.m3u8"
    #             }

    working_cctv: Dict[str, str] = {
        "DOH-PER-9-004": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase9/PER_9_004.stream/playlist.m3u8",
        "ITICM_BMAMI0277": "https://camerai1.iticfoundation.org/hls/pty76.m3u8",
        "DOH-PER-9-026": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase9/PER_9_026_IN.stream/playlist.m3u8",
        "ITICM_BMAMI0278": "https://camerai1.iticfoundation.org/hls/pty77.m3u8",
        "ITICM_BMAMI0103": "https://camerai1.iticfoundation.org/hls/ss01.m3u8",
        "ITICM_BMAMI0081": "https://camera1.iticfoundation.org/hls/10.8.0.18_8001.m3u8",
        "DOH-PER-10-006": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase10/PER_10_006.stream/playlist.m3u8",
        "DOH-PER-3-006": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase3/PER_3_006_IN.stream/playlist.m3u8",
        "ITICM_BMAMI0102": "https://camera1.iticfoundation.org/hls/10.8.0.14_8554.m3u8",
        "ITICM_BMAMI0104": "https://camerai1.iticfoundation.org/hls/ss02.m3u8",
        "DOH-PER-9-005": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase9/PER_9_005.stream/playlist.m3u8",
        "ITICM_BMAMI0120": "https://camerai1.iticfoundation.org/hls/ss18.m3u8",
        "ITICM_BMAMI0119": "https://camerai1.iticfoundation.org/hls/ss17.m3u8",
        "ITICM_BMAMI0164": "https://camerai1.iticfoundation.org/hls/charlie-new-tran-8.m3u8",
        "DOH-PER-9-020": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase9/PER-9-020.stream/playlist.m3u8",
        "DOH-PER-4-003": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase4/PER_4_003.stream/playlist.m3u8",
        "DOH-PER-7-024": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase7/PER_7_024.stream/playlist.m3u8",
        "ITICM_BMAMI0116": "https://camerai1.iticfoundation.org/hls/ss14.m3u8",
        "DOH-PER-8-036": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase8/PER_8_036.stream/playlist.m3u8",
        "ITICM_BMAMI0107": "https://camerai1.iticfoundation.org/hls/ss05.m3u8",
        "ITICM_BMAMI0122": "https://camerai1.iticfoundation.org/hls/ss20.m3u8",
        "cctvp2c228": "http://183.88.214.137:1935/livecctv/cctvp2c228.stream/playlist.m3u8",
        "cctvp2c106": "http://183.88.214.137:1935/livecctv/cctvp2c106.stream/playlist.m3u8",
        "cctvp2c234": "http://183.88.214.137:1935/livecctv/cctvp2c234.stream/playlist.m3u8",
        "cctvp2c233": "http://183.88.214.137:1935/livecctv/cctvp2c233.stream/playlist.m3u8",
        "cctvp2c221": "http://183.88.214.137:1935/livecctv/cctvp2c221.stream/playlist.m3u8",
        "ITICM_BMAMI0131": "https://camerai1.iticfoundation.org/hls/ccs02.m3u8",
        "ITICM_BMAMI0121": "https://camerai1.iticfoundation.org/hls/ss19.m3u8",
        "cctvp2c121": "http://183.88.214.137:1935/livecctv/cctvp2c121.stream/playlist.m3u8",
        "cctvp2c224": "http://183.88.214.137:1935/livecctv/cctvp2c224.stream/playlist.m3u8",
        "cctvp2c211": "http://183.88.214.137:1935/livecctv/cctvp2c211.stream/playlist.m3u8",
        "ITICM_BMAMI0105": "https://camerai1.iticfoundation.org/hls/ss03.m3u8",
        "ITICM_BMAMI0129": "https://camerai1.iticfoundation.org/hls/ccs00.m3u8",
        "ITICM_BMAMI0130": "https://camerai1.iticfoundation.org/hls/ccs01.m3u8",
        "ITICM_BMAMI0106": "https://camerai1.iticfoundation.org/hls/ss04.m3u8",
        "ITICM_BMAMI0132": "https://camerai1.iticfoundation.org/hls/ccs03.m3u8",
        "cctvp2c035": "http://183.88.214.137:1935/livecctv/cctvp2c035.stream/playlist.m3u8",
        "ITICM_BMAMI0133": "https://camerai1.iticfoundation.org/hls/ccs05.m3u8",
        "cctvp2c210": "http://183.88.214.137:1935/livecctv/cctvp2c210.stream/playlist.m3u8",
        "cctvp2c237": "http://183.88.214.137:1935/livecctv/cctvp2c237.stream/playlist.m3u8",
        "ITICM_BMAMI0134": "https://camerai1.iticfoundation.org/hls/ccs06.m3u8",
        "cctvp1c060": "http://183.88.214.137:1935/livecctv/cctvp1c060.stream/playlist.m3u8",
        "cctvp2c029": "http://183.88.214.137:1935/livecctv/cctvp2c029.stream/playlist.m3u8",
        "cctvp2c123": "http://183.88.214.137:1935/livecctv/cctvp2c123.stream/playlist.m3u8",
        "cctvp2c052": "http://183.88.214.137:1935/livecctv/cctvp2c052.stream/playlist.m3u8",
        "cctvp2c071": "http://183.88.214.137:1935/livecctv/cctvp2c071.stream/playlist.m3u8",
        "cctvp2c028": "http://183.88.214.137:1935/livecctv/cctvp2c028.stream/playlist.m3u8",
        "cctvp2c030": "http://183.88.214.137:1935/livecctv/cctvp2c030.stream/playlist.m3u8",
        "cctvp2c036": "http://183.88.214.137:1935/livecctv/cctvp2c036.stream/playlist.m3u8",
        "cctvp2c002": "http://183.88.214.137:1935/livecctv/cctvp2c002.stream/playlist.m3u8",
        "ITICM_BMAMI0142": "https://camerai1.iticfoundation.org/hls/ccs16.m3u8",
        "cctvp2c025": "http://183.88.214.137:1935/livecctv/cctvp2c025.stream/playlist.m3u8",
        "cctvp2c022": "http://183.88.214.137:1935/livecctv/cctvp2c022.stream/playlist.m3u8",
        "cctvp2c057": "http://183.88.214.137:1935/livecctv/cctvp2c057.stream/playlist.m3u8",
        "cctvp2c055": "http://183.88.214.137:1935/livecctv/cctvp2c055.stream/playlist.m3u8",
        "cctvp2c072": "http://183.88.214.137:1935/livecctv/cctvp2c072.stream/playlist.m3u8",
        "cctvp2c105": "http://183.88.214.137:1935/livecctv/cctvp2c105.stream/playlist.m3u8",
        "ITICM_BMAMI0137": "https://camerai1.iticfoundation.org/hls/ccs09.m3u8",
        "cctvp2c227": "http://183.88.214.137:1935/livecctv/cctvp2c227.stream/playlist.m3u8",
        "DOH-PER-4-011": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase4/PER_4_011_IN.stream/playlist.m3u8",
        "cctvp2c056": "http://183.88.214.137:1935/livecctv/cctvp2c056.stream/playlist.m3u8",
        "cctvp2c187": "http://183.88.214.137:1935/livecctv/cctvp2c187.stream/playlist.m3u8",
        "cctvp2c138": "http://183.88.214.137:1935/livecctv/cctvp2c138.stream/playlist.m3u8",
        "cctvp2c188": "http://183.88.214.137:1935/livecctv/cctvp2c188.stream/playlist.m3u8",
        "cctvp2c125": "http://183.88.214.137:1935/livecctv/cctvp2c125.stream/playlist.m3u8",
        "cctvp2c229": "http://183.88.214.137:1935/livecctv/cctvp2c229.stream/playlist.m3u8",
        "cctvp2c167": "http://183.88.214.137:1935/livecctv/cctvp2c167.stream/playlist.m3u8",
        "cctvp2c191": "http://183.88.214.137:1935/livecctv/cctvp2c191.stream/playlist.m3u8",
        "cctvp2c075": "http://183.88.214.137:1935/livecctv/cctvp2c075.stream/playlist.m3u8",
        "cctvp2c189": "http://183.88.214.137:1935/livecctv/cctvp2c189.stream/playlist.m3u8",
        "cctvp2c193": "http://183.88.214.137:1935/livecctv/cctvp2c193.stream/playlist.m3u8",
        "cctvp2c190": "http://183.88.214.137:1935/livecctv/cctvp2c190.stream/playlist.m3u8",
        "DOH-PER-11-018-out": "https://camerai1.iticfoundation.org/pass/180.180.242.208:1935/Phase11/PER_11_018_OUT.stream/playlist.m3u8",
        "DOH-PER-4-011-out": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase4/PER_4_011_OUT.stream/playlist.m3u8",
        "ITICM_BMAMI0108": "https://camerai1.iticfoundation.org/hls/ss06.m3u8",
        "DOH-PER-12-025": "https://camerai1.iticfoundation.org/pass/180.180.242.208:1935/Phase12/PER_12_025.stream/playlist.m3u8",
        "DOH-PER-11-019": "https://camerai1.iticfoundation.org/pass/180.180.242.208:1935/Phase11/PER_11_019.stream/playlist.m3u8",
        "ITICM_BMAMI0143": "https://camerai1.iticfoundation.org/hls/ccs17.m3u8",
        "ITICM_BMAMI0076": "https://camera1.iticfoundation.org/hls/10.8.0.15_8552.m3u8",
        "cctvp2c042": "http://183.88.214.137:1935/livecctv/cctvp2c042.stream/playlist.m3u8",
        "cctvp2c099": "http://183.88.214.137:1935/livecctv/cctvp2c099.stream/playlist.m3u8",
        "cctvp2c100": "http://183.88.214.137:1935/livecctv/cctvp2c100.stream/playlist.m3u8",
        "cctvp2c040": "http://183.88.214.137:1935/livecctv/cctvp2c040.stream/playlist.m3u8",
        "DOH-PER-4-016": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase4/PER_4_016_IN.stream/playlist.m3u8",
        "ITICM_BMAMI0145": "https://camerai1.iticfoundation.org/hls/ccs19.m3u8",
        "DOH-PER-4-023": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase4/PER_4_023.stream/playlist.m3u8",
        "ITICM_BMAMI0173": "https://camerai1.iticfoundation.org/hls/ccs28.m3u8",
        "cctvp2c231": "http://183.88.214.137:1935/livecctv/cctvp2c231.stream/playlist.m3u8",
        "cctvp2c103": "http://183.88.214.137:1935/livecctv/cctvp2c103.stream/playlist.m3u8",
        "cctvp2c230": "http://183.88.214.137:1935/livecctv/cctvp2c230.stream/playlist.m3u8",
        "cctvp2c169": "http://183.88.214.137:1935/livecctv/cctvp2c169.stream/playlist.m3u8",
        "cctvp2c173": "http://183.88.214.137:1935/livecctv/cctvp2c173.stream/playlist.m3u8",
        "cctvp2c168": "http://183.88.214.137:1935/livecctv/cctvp2c168.stream/playlist.m3u8",
        "cctvp2c171": "http://183.88.214.137:1935/livecctv/cctvp2c171.stream/playlist.m3u8",
        "cctvp2c049": "http://183.88.214.137:1935/livecctv/cctvp2c049.stream/playlist.m3u8",
        "cctvp2c170": "http://183.88.214.137:1935/livecctv/cctvp2c170.stream/playlist.m3u8",
        "cctvp2c172": "http://183.88.214.137:1935/livecctv/cctvp2c172.stream/playlist.m3u8",
        "cctvp2c174": "http://183.88.214.137:1935/livecctv/cctvp2c174.stream/playlist.m3u8",
        "cctvp2c044": "http://183.88.214.137:1935/livecctv/cctvp2c044.stream/playlist.m3u8",
        "DOH-PER-5-001-out": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase5/PER_5_001_OUT.stream/playlist.m3u8",
        "ITICM_BMAMI0146": "https://camerai1.iticfoundation.org/hls/ccs20.m3u8",
        "cctvp2c082": "http://183.88.214.137:1935/livecctv/cctvp2c082.stream/playlist.m3u8",
        "DOH-PER-12-019": "https://camerai1.iticfoundation.org/pass/180.180.242.208:1935/Phase12/PER_12_019.stream/playlist.m3u8",
        "cctvp2c018": "http://183.88.214.137:1935/livecctv/cctvp2c018.stream/playlist.m3u8",
        "ITICM_BMAMI0147": "https://camerai1.iticfoundation.org/hls/ccs21.m3u8",
        "cctvp2c081": "http://183.88.214.137:1935/livecctv/cctvp2c081.stream/playlist.m3u8",
        "cctvp2c079": "http://183.88.214.137:1935/livecctv/cctvp2c079.stream/playlist.m3u8",
        "cctvp2c038": "http://183.88.214.137:1935/livecctv/cctvp2c038.stream/playlist.m3u8",
        "cctvp2c043": "http://183.88.214.137:1935/livecctv/cctvp2c043.stream/playlist.m3u8",
        "cctvp2c080": "http://183.88.214.137:1935/livecctv/cctvp2c080.stream/playlist.m3u8",
        "cctvp2c078": "http://183.88.214.137:1935/livecctv/cctvp2c078.stream/playlist.m3u8",
        "cctvp2c037": "http://183.88.214.137:1935/livecctv/cctvp2c037.stream/playlist.m3u8",
        "ITICM_BMAMI0167": "https://camerai1.iticfoundation.org/hls/ccs22.m3u8",
        "ITICM_BMAMI0166": "https://camerai1.iticfoundation.org/hls/charlie-new-tran-9.m3u8",
        "ITICM_BMAMI0075": "https://camera1.iticfoundation.org/hls/10.8.0.15_8551.m3u8",
        "DOH-PER-12-026": "https://camerai1.iticfoundation.org/pass/180.180.242.208:1935/Phase12/PER_12_026_IN.stream/playlist.m3u8",
        "ITICM_BMAMI0169": "https://camerai1.iticfoundation.org/hls/ccs24.m3u8",
        "ITICM_BMAMI0168": "https://camerai1.iticfoundation.org/hls/ccs23.m3u8",
        "ITICM_BMAMI0170": "https://camerai1.iticfoundation.org/hls/ccs25.m3u8",
        "cctvp2c246": "http://183.88.214.137:1935/livecctv/cctvp2c246.stream/playlist.m3u8",
        "cctvp2c019": "http://183.88.214.137:1935/livecctv/cctvp2c019.stream/playlist.m3u8",
        "cctvp2c021": "http://183.88.214.137:1935/livecctv/cctvp2c021.stream/playlist.m3u8",
        "cctvp2c050": "http://183.88.214.137:1935/livecctv/cctvp2c050.stream/playlist.m3u8",
        "cctvp2c250": "http://183.88.214.137:1935/livecctv/cctvp2c250.stream/playlist.m3u8",
        "cctvp2c051": "http://183.88.214.137:1935/livecctv/cctvp2c051.stream/playlist.m3u8",
        "cctvp2c076": "http://183.88.214.137:1935/livecctv/cctvp2c076.stream/playlist.m3u8",
        "cctvp2c033": "http://183.88.214.137:1935/livecctv/cctvp2c033.stream/playlist.m3u8",
        "ITICM_BMAMI0171": "https://camerai1.iticfoundation.org/hls/ccs26.m3u8",
        "ITICM_BMAMI0174": "https://camerai1.iticfoundation.org/hls/ccs29.m3u8",
        "ITICM_BMAMI0177": "https://camerai1.iticfoundation.org/hls/ccs32.m3u8",
        "ITICM_BMAMI0172": "https://camerai1.iticfoundation.org/hls/ccs27.m3u8",
        "ITICM_BMAMI0175": "https://camerai1.iticfoundation.org/hls/ccs30.m3u8",
        "ITICM_BMAMI0176": "https://camerai1.iticfoundation.org/hls/ccs31.m3u8",
        "ITICM_BMAMI0178": "https://camerai1.iticfoundation.org/hls/ccs33.m3u8",
        "ITICM_BMAMI0179": "https://camerai1.iticfoundation.org/hls/ccs34.m3u8",
        "ITICM_BMAMI0181": "https://camerai1.iticfoundation.org/hls/ccs36.m3u8",
        "cctvp2c085": "http://183.88.214.137:1935/livecctv/cctvp2c085.stream/playlist.m3u8",
        "ITICM_BMAMI0182": "https://camerai1.iticfoundation.org/hls/ccs37.m3u8",
        "cctvp2c111": "http://183.88.214.137:1935/livecctv/cctvp2c111.stream/playlist.m3u8",
        "cctvp2c113": "http://183.88.214.137:1935/livecctv/cctvp2c113.stream/playlist.m3u8",
        "cctvp2c110": "http://183.88.214.137:1935/livecctv/cctvp2c110.stream/playlist.m3u8",
        "cctvp2c031": "http://183.88.214.137:1935/livecctv/cctvp2c031.stream/playlist.m3u8",
        "cctvp2c114": "http://183.88.214.137:1935/livecctv/cctvp2c114.stream/playlist.m3u8",
        "cctvp2c108": "http://183.88.214.137:1935/livecctv/cctvp2c108.stream/playlist.m3u8",
        "ITICM_BMAMI0183": "https://camerai1.iticfoundation.org/hls/ccs38.m3u8",
        "ITICM_BMAMI0184": "https://camerai1.iticfoundation.org/hls/ccs39.m3u8",
        "ITICM_BMAMI0186": "https://camerai1.iticfoundation.org/hls/ccs41.m3u8",
        "ITICM_BMAMI0185": "https://camerai1.iticfoundation.org/hls/ccs40.m3u8",
        "cctvp2c010": "http://183.88.214.137:1935/livecctv/cctvp2c010.stream/playlist.m3u8",
        "cctvp2c026": "http://183.88.214.137:1935/livecctv/cctvp2c026.stream/playlist.m3u8",
        "cctvp2c119": "http://183.88.214.137:1935/livecctv/cctvp2c119.stream/playlist.m3u8",
        "ITICM_BMAMI0192": "https://camerai1.iticfoundation.org/hls/pty21.m3u8",
        "cctvp2c020": "http://183.88.214.137:1935/livecctv/cctvp2c020.stream/playlist.m3u8",
        "cctvp2c013": "http://183.88.214.137:1935/livecctv/cctvp2c013.stream/playlist.m3u8",
        "ITICM_BMAMI0187": "https://camerai1.iticfoundation.org/hls/ccs42.m3u8",
        "ITICM_BMAMI0201": "https://camerai1.iticfoundation.org/hls/pty30.m3u8",
        "ITICM_BMAMI0202": "https://camerai1.iticfoundation.org/hls/pty31.m3u8",
        "ITICM_BMAMI0215": "https://camerai1.iticfoundation.org/hls/kk02.m3u8",
        "ITICM_BMAMI0216": "https://camerai1.iticfoundation.org/hls/kk03.m3u8",
        "ITICM_BMAMI0218": "https://camerai1.iticfoundation.org/hls/kk05.m3u8",
        "ITICM_BMAMI0217": "https://camerai1.iticfoundation.org/hls/kk04.m3u8",
        "ITICM_BMAMI0219": "https://camerai1.iticfoundation.org/hls/kk06.m3u8",
        "ITICM_BMAMI0221": "https://camerai1.iticfoundation.org/hls/kk08.m3u8",
        "ITICM_BMAMI0220": "https://camerai1.iticfoundation.org/hls/kk07.m3u8",
        "ITICM_BMAMI0222": "https://camerai1.iticfoundation.org/hls/kk09.m3u8",
        "ITICM_BMAMI0188": "https://camerai1.iticfoundation.org/hls/charlie-new5.m3u8",
        "DOH-PER-4-003-out": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase4/PER_4_003_OUT.stream/playlist.m3u8",
        "DOH-PER-10-033": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase10/PER_10_033.stream/playlist.m3u8",
        "DOH-PER-3-009-out": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase3/PER_3_009_OUT.stream/playlist.m3u8",
        "ITICM_BMAMI0224": "https://camerai1.iticfoundation.org/hls/kk11.m3u8",
        "ITICM_BMAMI0227": "https://camerai1.iticfoundation.org/hls/kk14.m3u8",
        "ITICM_BMAMI0223": "https://camerai1.iticfoundation.org/hls/kk10.m3u8",
        "ITICM_BMAMI0225": "https://camerai1.iticfoundation.org/hls/kk12.m3u8",
        "DOH-PER-10-013": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase10/PER_10_013.stream/playlist.m3u8",
        "ITICM_BMAMI0165": "https://camerai1.iticfoundation.org/hls/charlie-new-tran-10.m3u8",
        "DOH-PER-6-007": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase6/PER_6_007.stream/playlist.m3u8",
        "DOH-PER-3-009": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase3/PER_3_009_IN.stream/playlist.m3u8",
        "ITICM_BMAMI0226": "https://camerai1.iticfoundation.org/hls/kk13.m3u8",
        "ITICM_BMAMI0236": "https://camerai1.iticfoundation.org/hls/kk23.m3u8",
        "ITICM_BMAMI0242": "https://camerai1.iticfoundation.org/hls/pty41.m3u8",
        "ITICM_BMAMI0241": "https://camerai1.iticfoundation.org/hls/pty40.m3u8",
        "ITICM_BMAMI0071": "https://camera1.iticfoundation.org/hls/10.8.0.14_8002.m3u8",
        "ITICM_BMAMI0268": "https://camerai1.iticfoundation.org/hls/pty67.m3u8",
        "ITICM_BMAMI0257": "https://camerai1.iticfoundation.org/hls/pty56.m3u8",
        "ITICM_BMAMI0072": "https://camera1.iticfoundation.org/hls/10.8.0.14_8003.m3u8",
        "ITICM_BMAMI0243": "https://camerai1.iticfoundation.org/hls/pty42.m3u8",
        "DOH-PER-5-007-out": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase5/PER_5_007_OUT.stream/playlist.m3u8",
        "DOH-PER-11-022": "https://camerai1.iticfoundation.org/pass/180.180.242.208:1935/Phase11/PER_11_022.stream/playlist.m3u8",
        "ITICM_BMAMI0180": "https://camerai1.iticfoundation.org/hls/ccs35.m3u8",
        "DOH-PER-8-012": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase8/PER_8_012.stream/playlist.m3u8",
        "ITICM_BMAMI0074": "https://camera1.iticfoundation.org/hls/10.8.0.14_8001.m3u8",
        "ITICM_BMAMI0272": "https://camerai1.iticfoundation.org/hls/pty71.m3u8",
        "ITICM_BMAMI0280": "https://camerai1.iticfoundation.org/hls/pty79.m3u8",
        "ITICM_BMAMI0279": "https://camerai1.iticfoundation.org/hls/pty78.m3u8",
        "DOH-PER-5-006": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase5/PER_5_006_IN.stream/playlist.m3u8",
        "DOH-PER-5-006-out": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase5/PER_5_006_OUT.stream/playlist.m3u8",
        "ITICM_BMAMI0271": "https://camerai1.iticfoundation.org/hls/pty70.m3u8",
        "ITICM_BMAMI0276": "https://camerai1.iticfoundation.org/hls/pty75.m3u8",
        "ITICM_BMAMI0240": "https://camerai1.iticfoundation.org/hls/kk27.m3u8",
        "ITICM_BMAMI0269": "https://camerai1.iticfoundation.org/hls/pty68.m3u8",
        "DOH-PER-7-035-out": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase7/PER_7_035_OUT.stream/playlist.m3u8",
        "ITICM_BMAMI0274": "https://camerai1.iticfoundation.org/hls/pty73.m3u8",
        "ITICM_BMAMI0282": "https://camerai1.iticfoundation.org/hls/pty81.m3u8",
        "ITICM_BMAMI0281": "https://camerai1.iticfoundation.org/hls/pty80.m3u8",
        "ITICM_BMAMI0109": "https://camerai1.iticfoundation.org/hls/ss07.m3u8",
        "ITICM_BMAMI0114": "https://camerai1.iticfoundation.org/hls/ss12.m3u8",
        "DOH-PER-11-026-out": "https://camerai1.iticfoundation.org/pass/180.180.242.208:1935/Phase11/PER_11_026_OUT.stream/playlist.m3u8",
        "ITICM_BMAMI0124": "https://camera1.iticfoundation.org/hls/10.8.0.19_8801.m3u8",
        "DOH-PER-6-004": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase6/PER_6_004.stream/playlist.m3u8",
        "ITICM_BMAMI0125": "https://camera1.iticfoundation.org/hls/10.8.0.19_8802.m3u8",
        "ITICM_BMAMI0235": "https://camerai1.iticfoundation.org/hls/kk22.m3u8",
        "DOH-PER-3-006-out": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase3/PER_3_006_OUT.stream/playlist.m3u8",
        "cctvp2c034": "http://183.88.214.137:1935/livecctv/cctvp2c034.stream/playlist.m3u8",
        "cctvp2c064": "http://183.88.214.137:1935/livecctv/cctvp2c064.stream/playlist.m3u8",
        "cctvp2c059": "http://183.88.214.137:1935/livecctv/cctvp2c059.stream/playlist.m3u8",
        "cctvp2c090": "http://183.88.214.137:1935/livecctv/cctvp2c090.stream/playlist.m3u8",
        "cctvp2c023": "http://183.88.214.137:1935/livecctv/cctvp2c023.stream/playlist.m3u8",
        "cctvp2c066": "http://183.88.214.137:1935/livecctv/cctvp2c066.stream/playlist.m3u8",
        "cctvp2c004": "http://183.88.214.137:1935/livecctv/cctvp2c004.stream/playlist.m3u8",
        "DOH-PER-11-003": "https://camerai1.iticfoundation.org/pass/180.180.242.208:1935/Phase11/PER_11_003.stream/playlist.m3u8",
        "cctvp2c011": "http://183.88.214.137:1935/livecctv/cctvp2c011.stream/playlist.m3u8",
        "cctvp2c068": "http://183.88.214.137:1935/livecctv/cctvp2c068.stream/playlist.m3u8",
        "cctvp2c094": "http://183.88.214.137:1935/livecctv/cctvp2c094.stream/playlist.m3u8",
        "cctvp2c226": "http://183.88.214.137:1935/livecctv/cctvp2c226.stream/playlist.m3u8",
        "cctvp2c067": "http://183.88.214.137:1935/livecctv/cctvp2c067.stream/playlist.m3u8",
        "ITICM_BMAMI0208": "https://camera1.iticfoundation.org/hls/10.8.0.21_8001.m3u8",
        "cctvp2c065": "http://183.88.214.137:1935/livecctv/cctvp2c065.stream/playlist.m3u8",
        "ITICM_BMAMI0209": "https://camera1.iticfoundation.org/hls/10.8.0.21_8002.m3u8",
        "ITICM_BMAMI0118": "https://camerai1.iticfoundation.org/hls/ss16.m3u8",
        "DOH-PER-12-012": "https://camerai1.iticfoundation.org/pass/180.180.242.208:1935/Phase12/PER_12_012_IN.stream/playlist.m3u8",
        "DOH-PER-6-013-out": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase6/PER_6_013_OUT.stream/playlist.m3u8",
        "cctvp2c093": "http://183.88.214.137:1935/livecctv/cctvp2c093.stream/playlist.m3u8",
        "cctvp2c058": "http://183.88.214.137:1935/livecctv/cctvp2c058.stream/playlist.m3u8",
        "cctvp2c181": "http://183.88.214.137:1935/livecctv/cctvp2c181.stream/playlist.m3u8",
        "cctvp2c003": "http://183.88.214.137:1935/livecctv/cctvp2c003.stream/playlist.m3u8",
        "cctvp2c088": "http://183.88.214.137:1935/livecctv/cctvp2c088.stream/playlist.m3u8",
        "cctvp2c060": "http://183.88.214.137:1935/livecctv/cctvp2c060.stream/playlist.m3u8",
        "cctvp2c089": "http://183.88.214.137:1935/livecctv/cctvp2c089.stream/playlist.m3u8",
        "cctvp2c095": "http://183.88.214.137:1935/livecctv/cctvp2c095.stream/playlist.m3u8",
        "cctvp2c007": "http://183.88.214.137:1935/livecctv/cctvp2c007.stream/playlist.m3u8",
        "cctvp2c115": "http://183.88.214.137:1935/livecctv/cctvp2c115.stream/playlist.m3u8",
        "cctvp2c163": "http://183.88.214.137:1935/livecctv/cctvp2c163.stream/playlist.m3u8",
        "cctvp2c063": "http://183.88.214.137:1935/livecctv/cctvp2c063.stream/playlist.m3u8",
        "cctvp2c024": "http://183.88.214.137:1935/livecctv/cctvp2c024.stream/playlist.m3u8",
        "cctvp2c008": "http://183.88.214.137:1935/livecctv/cctvp2c008.stream/playlist.m3u8",
        "cctvp2c175": "http://183.88.214.137:1935/livecctv/cctvp2c175.stream/playlist.m3u8",
        "cctvp2c166": "http://183.88.214.137:1935/livecctv/cctvp2c166.stream/playlist.m3u8",
        "cctvp2c225": "http://183.88.214.137:1935/livecctv/cctvp2c225.stream/playlist.m3u8",
        "cctvp2c202": "http://183.88.214.137:1935/livecctv/cctvp2c202.stream/playlist.m3u8",
        "cctvp2c240": "http://183.88.214.137:1935/livecctv/cctvp2c240.stream/playlist.m3u8",
        "ITICM_BMAMI0111": "https://camerai1.iticfoundation.org/hls/ss09.m3u8",
        "ITICM_BMAMI0123": "https://camerai1.iticfoundation.org/hls/ss21.m3u8",
        "cctvp2c091": "http://183.88.214.137:1935/livecctv/cctvp2c091.stream/playlist.m3u8",
        "cctvp2c073": "http://183.88.214.137:1935/livecctv/cctvp2c073.stream/playlist.m3u8",
        "cctvp2c101": "http://183.88.214.137:1935/livecctv/cctvp2c101.stream/playlist.m3u8",
        "cctvp2c061": "http://183.88.214.137:1935/livecctv/cctvp2c061.stream/playlist.m3u8",
        "cctvp2c165": "http://183.88.214.137:1935/livecctv/cctvp2c165.stream/playlist.m3u8",
        "cctvp2c161": "http://183.88.214.137:1935/livecctv/cctvp2c161.stream/playlist.m3u8",
        "DOH-PER-7-026": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase7/PER_7_026.stream/playlist.m3u8",
        "DOH-PER-7-022": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase7/PER_7_022.stream/playlist.m3u8",
        "DOH-PER-10-032": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase10/PER_10_032.stream/playlist.m3u8",
        "DOH-PER-7-010": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase7/PER_7_010.stream/playlist.m3u8",
        "ITICM_BMAMI0135": "https://camerai1.iticfoundation.org/hls/ccs07.m3u8",
        "cctvp2c054": "http://183.88.214.137:1935/livecctv/cctvp2c054.stream/playlist.m3u8",
        "cctvp2c016": "http://183.88.214.137:1935/livecctv/cctvp2c016.stream/playlist.m3u8",
        "cctvp2c096": "http://183.88.214.137:1935/livecctv/cctvp2c096.stream/playlist.m3u8",
        "cctvp2c017": "http://183.88.214.137:1935/livecctv/cctvp2c017.stream/playlist.m3u8",
        "cctvp2c245": "http://183.88.214.137:1935/livecctv/cctvp2c245.stream/playlist.m3u8",
        "cctvp2c184": "http://183.88.214.137:1935/livecctv/cctvp2c184.stream/playlist.m3u8",
        "cctvp2c097": "http://183.88.214.137:1935/livecctv/cctvp2c097.stream/playlist.m3u8",
        "cctvp2c012": "http://183.88.214.137:1935/livecctv/cctvp2c012.stream/playlist.m3u8",
        "cctvp2c015": "http://183.88.214.137:1935/livecctv/cctvp2c015.stream/playlist.m3u8",
        "cctvp2c186": "http://183.88.214.137:1935/livecctv/cctvp2c186.stream/playlist.m3u8",
        "cctvp2c053": "http://183.88.214.137:1935/livecctv/cctvp2c053.stream/playlist.m3u8",
        "ITICM_BMAMI0144": "https://camerai1.iticfoundation.org/hls/ccs18.m3u8",
        "ITICM_BMAMI0162": "https://camerai1.iticfoundation.org/hls/pty15.m3u8",
        "DOH-PER-7-035": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase7/PER_7_035_IN.stream/playlist.m3u8",
        "cctvp2c251": "http://183.88.214.137:1935/livecctv/cctvp2c251.stream/playlist.m3u8",
        "ITICM_BMAMI0212": "https://camerai1.iticfoundation.org/hls/cl211-d.m3u8",
        "cctvp2c179": "http://183.88.214.137:1935/livecctv/cctvp2c179.stream/playlist.m3u8",
        "ITICM_BMAMI0203": "https://camerai1.iticfoundation.org/hls/pty32.m3u8",
        "cctvp2c087": "http://183.88.214.137:1935/livecctv/cctvp2c087.stream/playlist.m3u8",
        "cctvp2c178": "http://183.88.214.137:1935/livecctv/cctvp2c178.stream/playlist.m3u8",
        "cctvp2c241": "http://183.88.214.137:1935/livecctv/cctvp2c241.stream/playlist.m3u8",
        "ITICM_BMAMI0211": "https://camerai1.iticfoundation.org/hls/cl210-d.m3u8",
        "cctvp2c239": "http://183.88.214.137:1935/livecctv/cctvp2c239.stream/playlist.m3u8",
        "ITICM_BMAMI0210": "https://camerai1.iticfoundation.org/hls/cl209-d.m3u8",
        "ITICM_BMAMI0214": "https://camerai1.iticfoundation.org/hls/kk01.m3u8",
        "cctvp2c104": "http://183.88.214.137:1935/livecctv/cctvp2c104.stream/playlist.m3u8",
        "ITICM_BMAMI0213": "https://camerai1.iticfoundation.org/hls/cl212-d.m3u8",
        "cctvp2c124": "http://183.88.214.137:1935/livecctv/cctvp2c124.stream/playlist.m3u8",
        "DOH-PER-11-028": "https://camerai1.iticfoundation.org/pass/180.180.242.208:1935/Phase11/PER_11_028_IN.stream/playlist.m3u8",
        "ITICM_BMAMI0110": "https://camerai1.iticfoundation.org/hls/ss08.m3u8",
        "ITICM_BMAMI0080": "https://camera1.iticfoundation.org/hls/10.8.0.18_8002.m3u8",
        "ITICM_BMAMI0078": "https://camera1.iticfoundation.org/hls/10.8.0.17_8002.m3u8",
        "cctvp2c032": "http://183.88.214.137:1935/livecctv/cctvp2c032.stream/playlist.m3u8",
        "cctvp2c194": "http://183.88.214.137:1935/livecctv/cctvp2c194.stream/playlist.m3u8",
        "DOH-PER-12-008": "https://camerai1.iticfoundation.org/pass/180.180.242.208:1935/Phase12/PER_12_008.stream/playlist.m3u8",
        "cctvp2c200": "http://183.88.214.137:1935/livecctv/cctvp2c200.stream/playlist.m3u8",
        "cctvp2c039": "http://183.88.214.137:1935/livecctv/cctvp2c039.stream/playlist.m3u8",
        "cctvp2c160": "http://183.88.214.137:1935/livecctv/cctvp2c160.stream/playlist.m3u8",
        "cctvp2c062": "http://183.88.214.137:1935/livecctv/cctvp2c062.stream/playlist.m3u8",
        "cctvp2c201": "http://183.88.214.137:1935/livecctv/cctvp2c201.stream/playlist.m3u8",
        "cctvp2c009": "http://183.88.214.137:1935/livecctv/cctvp2c009.stream/playlist.m3u8",
        "ITICM_BMAMI0138": "https://camerai1.iticfoundation.org/hls/ccs12.m3u8",
        "ITICM_BMAMI0112": "https://camerai1.iticfoundation.org/hls/ss10.m3u8",
        "ITICM_BMAMI0139": "https://camerai1.iticfoundation.org/hls/ccs13.m3u8",
        "ITICM_BMAMI0141": "https://camerai1.iticfoundation.org/hls/ccs15.m3u8",
        "ITICM_BMAMI0140": "https://camerai1.iticfoundation.org/hls/ccs14.m3u8",
        "ITICM_BMAMI0117": "https://camerai1.iticfoundation.org/hls/ss15.m3u8",
        "cctvp2c238": "http://183.88.214.137:1935/livecctv/cctvp2c238.stream/playlist.m3u8",
        "cctvp2c256": "http://183.88.214.137:1935/livecctv/cctvp2c256.stream/playlist.m3u8",
        "cctvp2c162": "http://183.88.214.137:1935/livecctv/cctvp2c162.stream/playlist.m3u8",
        "cctvp2c253": "http://183.88.214.137:1935/livecctv/cctvp2c253.stream/playlist.m3u8",
        "cctvp2c122": "http://183.88.214.137:1935/livecctv/cctvp2c122.stream/playlist.m3u8",
        "ITICM_BMAMI0113": "https://camerai1.iticfoundation.org/hls/ss11.m3u8",
        "ITICM_BMAMI0115": "https://camerai1.iticfoundation.org/hls/ss13.m3u8",
        "ITICM_BMAMI0136": "https://camerai1.iticfoundation.org/hls/ccs08.m3u8",
        "ITICM_BMAMI0237": "https://camerai1.iticfoundation.org/hls/kk24.m3u8",
        "DOH-PER-3-004-out": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase3/PER_3_004_OUT.stream/playlist.m3u8",
        "DOH-PER-12-002": "https://camerai1.iticfoundation.org/pass/180.180.242.208:1935/Phase12/PER_12_002.stream/playlist.m3u8",
        "DOH-PER-6-002-out": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase6/PER_6_002_OUT.stream/playlist.m3u8",
        "cctvp2c117": "http://183.88.214.137:1935/livecctv/cctvp2c117.stream/playlist.m3u8",
        "cctvp2c118": "http://183.88.214.137:1935/livecctv/cctvp2c118.stream/playlist.m3u8",
        "cctvp2c116": "http://183.88.214.137:1935/livecctv/cctvp2c116.stream/playlist.m3u8",
        "cctvp2c236": "http://183.88.214.137:1935/livecctv/cctvp2c236.stream/playlist.m3u8",
        "ITICM_BMAMI0284": "https://camerai1.iticfoundation.org/hls/pty83.m3u8",
        "ITICM_BMAMI0283": "https://camerai1.iticfoundation.org/hls/pty82.m3u8",
        "cctvp2c074": "http://183.88.214.137:1935/livecctv/cctvp2c074.stream/playlist.m3u8",
        "cctvp2c176": "http://183.88.214.137:1935/livecctv/cctvp2c176.stream/playlist.m3u8",
        "DOH-PER-8-013": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase8/PER_8_013.stream/playlist.m3u8",
        "DOH-PER-12-017": "https://camerai1.iticfoundation.org/pass/180.180.242.208:1935/Phase12/PER_12_017.stream/playlist.m3u8",
        "DOH-PER-12-010": "https://camerai1.iticfoundation.org/pass/180.180.242.208:1935/Phase12/PER_12_010_IN.stream/playlist.m3u8",
        "cctvp2c014": "http://183.88.214.137:1935/livecctv/cctvp2c014.stream/playlist.m3u8",
        "cctvp2c092": "http://183.88.214.137:1935/livecctv/cctvp2c092.stream/playlist.m3u8",
        "cctvp2c069": "http://183.88.214.137:1935/livecctv/cctvp2c069.stream/playlist.m3u8",
        "cctvp2c180": "http://183.88.214.137:1935/livecctv/cctvp2c180.stream/playlist.m3u8"
    }



    print(f"Starting scraping for {len(working_cctv)} CCTVs...")
    start_time = time.time()

    # Run the multiprocessing function
    results = run_multiprocessing(
        scrape_image_HLS,
        80,  # Desired number of concurrent processes
        working_cctv,
        **config
    )

    end_time = time.time()
    total_time = end_time - start_time

    # Process the results
    print(f"\nScraping completed in {total_time:.2f} seconds")
    print(f"Successfully scraped {len(results['image_result'])} cameras")
    print(f"Working CCTV: {len(results['working_cctv'])}")
    print(f"Unresponsive CCTV: {len(results['unresponsive_cctv'])}")

    # Calculate and print statistics
    success_rate = len(results['working_cctv']) / len(working_cctv) * 100
    print(f"\nSuccess rate: {success_rate:.2f}%")
    print(f"Average time per camera: {total_time / len(working_cctv):.4f} seconds")