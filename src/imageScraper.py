
import sys
import threading
from threading import Semaphore
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Union, Optional, Literal

from cctv_operation_BMA.cam_update import update_cctv_database, retrieve_camInfo_BMA
from utils.log_config import logger, log_setup
from utils.Database import retrieve_data, update_data
from utils.json_manager import load_latest_cctv_sessions_from_json
from cctv_operation_BMA.worker import scrape_image_BMA
from utils.utils import sort_key, readable_time, create_cctv_status_dict, select_non_empty, check_cctv_integrity


def scraper_factory(BMA_JSON_result: Tuple[str, str, Dict[str, str]], isBMAReady: bool,
                    HLS_information: Tuple[Tuple[str, str], ...], isHLSReady: bool):

    if isBMAReady:
        _, _, cctvSessions = BMA_JSON_result
        BMA_working, BMA_unresponsive, BMA_image_result = prepare_scrape_image_BMA_workers(cctvSessions)
    
    if isHLSReady:
        # HLS_working, HLS_unresponsive, HLS_image_result = prepare_scrape_image_HLS_workers(cctvURL)
        return







def prepare_scrape_image_BMA_workers(cctvSessions: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str], List[Tuple[str, List[bytes], datetime]]]:
    max_workers = 80
    semaphore = Semaphore(max_workers)
    threads = []
    working_session = {}
    unresponsive_session = {}
    image_result = [] # This must be [('001', byte data, time),...]
    target_image_count = 2

    logger.info("[THREADING-S] Initializing session validation workers.")

    for camera_id, session_id in cctvSessions.items():
        semaphore.acquire()
        thread = threading.Thread(target=scrape_image_BMA, args=(camera_id, session_id, semaphore, working_session, unresponsive_session, image_result, target_image_count))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()
    
    working_session = dict(sorted(working_session.items(), key=lambda x: sort_key(x[0])))
    unresponsive_session = dict(sorted(unresponsive_session.items(), key=lambda x: sort_key(x[0])))
    image_result = sorted(image_result, key=lambda x: sort_key(x[0]))

    logger.info(f"[THREADING-S] {len(working_session)} sessions are working from CCTV: {list(working_session.keys())}")
    logger.info(f"[THREADING-S] {len(unresponsive_session)} sessions are unresponsive from CCTV: {unresponsive_session}")
    logger.info("[THREADING-S] All sessions are validated.")

    return working_session, unresponsive_session, image_result


'''
Step 0: Get cctv list
have to create a function that get all session id based on latest update in database (online cctv in db), if cannot get from db, just get from bma

Step 1: get session ID
give cctv list to prepare_create_sessionID_workers()

Step 2: verify session ID
after having all session id, have to verify that image is valid or not.

Step 3: scrape the image
image from this step could use the one from step 2


***For other cctv, have to write a separate function, but at the end it should output the same data


the scraping output should be in byte data
Create a dictionary that have a key as cctv provider and value as a list of tuple containing a cctv id as string, image data as byte, and capture time as datetime object

result = {'BMA': [('001', byte data, time), ('002', byte data, time)],
        'BMA': [('001', byte data, time), ('002', byte data, time)]
}
result: Dict[str, List[Tuple[str, bytes, datetime]]]


*** Futher processing

then save it to file or database
but the problem is that other cctv have big file, might not good for database

anyway I have to put the image in numpy array and send directly to model and update the result
'''





def verifyBMA(BMA_JSON_result):
    latestRefreshTime, latestUpdateTime, cctvSessions = BMA_JSON_result
    current_time = datetime.now()

    def parse_time_and_diff(time_str):
        time_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        diff = current_time - time_dt
        return time_dt, diff, readable_time(int(diff.total_seconds()))

    refreshTime, timeDiffRefresh, readable_diff_refresh = parse_time_and_diff(latestRefreshTime)
    updateTime, timeDiffUpdate, readable_diff_update = parse_time_and_diff(latestUpdateTime)

    # max_timeDiffUpdate = timedelta(hours=4)
    max_timeDiffRefresh = timedelta(minutes=20)

    logger.info(f"[INFO] Latest Refresh Time: {latestRefreshTime}")
    logger.info(f"[INFO] Latest Update Time: {latestUpdateTime}")
    logger.info(f"[INFO] CCTV Sessions: {cctvSessions}")
    logger.info(f"[INFO] The latest update occurred at {latestUpdateTime}, which was {readable_diff_update} ago.")
    logger.info(f"[INFO] The latest refresh occurred at {latestRefreshTime}, which was {readable_diff_refresh} ago.")

    if timeDiffRefresh < max_timeDiffRefresh:
        # Case 1:
        # Refresh times is within the valid range, so simply do a quick refresh and scraped image.
        # Do the scrapign now
        # start_scraping(cctvSessions)
        return True
        
    else:
        # Case 2:
        # This scrip just check for refresh times so it will not redundant with the sessionID.py
        # This script designed to scrape image, not preparing session ID.
        # So this condition will just terminate the script as sessionID have expired.
        logger.info(f"[INFO] Refresh times exceed their maximum allowed time differences.")
        # exit(0)
        return False





if __name__ == "__main__":
    log_setup("./logs/imageScraper","sessionID")
    scrape_BMA = True
    scrape_HLS = True
    BMA_JSON_result = load_latest_cctv_sessions_from_json()
    HLS_information = retrieve_data(
        'cctv_locations_general',
        ('Cam_ID', 'Stream_Link_1'),
        ('Stream_Method',),
        ('HLS',)
    )

    if not BMA_JSON_result:
        logger.warning("[INFO] No JSON file found or failed to load.")
        scrape_BMA = False
    else:
        scrape_BMA = verifyBMA(BMA_JSON_result)
        
    if not HLS_information:
        logger.warning("[INFO] No HLS information found or failed to load.")
        scrape_HLS = False
    else:
        logger.info("[INFO] HLS information ready")


    scraper_factory(BMA_JSON_result, scrape_BMA,
                    HLS_information, scrape_HLS)
            