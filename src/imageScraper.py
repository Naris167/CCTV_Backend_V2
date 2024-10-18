import sys
import os
from threading import Semaphore, Thread
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Union, Optional, Literal

from utils.log_config import logger, log_setup
from utils.Database import retrieve_data, update_data
from utils.json_manager import load_latest_cctv_sessions_from_json
from cctv_operation_BMA.worker import scrape_image_BMA
from cctv_operation_HLS.worker import check_cctv_status, scrape_image_HLS
from utils.utils import readable_time, sort_results, run_threaded, save_cctv_images


def scraper_factory(BMA_JSON_result: Tuple[str, str, Dict[str, str]], isBMAReady: bool,
                    HLS_information: Tuple[Tuple[str, str], ...], isHLSReady: bool):

    if isBMAReady:
        _, _, cctvSessions = BMA_JSON_result
        # BMA_working, BMA_unresponsive, BMA_image_result = prepare_scrape_image_BMA_workers(cctvSessions)
    
    if isHLSReady:
        cctvLinks = dict(HLS_information)

        # cctvLinks = {"cctvp2c001": "http://183.88.214.137:1935/livecctv/cctvp2c001.stream/playlist.m3u8",
        #              "cctvp2c003": "http://183.88.214.137:1935/livecctv/cctvp2c003.stream/playlist.m3u8",
        #              "ITICM_BMAMI0133": "https://camerai1.iticfoundation.org/hls/ccs05.m3u8",
        #              "ITICM_BMAMI0272": "https://camerai1.iticfoundation.org/hls/pty71.m3u8", # This one have problem. It take too long to response
        #              "ITICM_BMAMI0237": "https://camerai1.iticfoundation.org/hls/kk24.m3u8",
        #              "ITICM_BMAMI0257": "https://camerai1.iticfoundation.org/hls/pty56.m3u8"   
        # #              "": "https://camerai1.iticfoundation.org/hls/charlie-new51.ts"
        #              }

        HLS_working, HLS_unresponsive, offline_cctv, HLS_image_result = prepare_scrape_image_HLS_workers(cctvLinks)

    print(HLS_working)
    
    # update_data(
    #     'cctv_locations_general',
    #     ('is_online', 'stream_method'),
    #     (True, 'HLS')
    # )
    
    # update_data(
    #     'cctv_locations_general',
    #     ('is_online',),
    #     (False,),
    #     ('cam_id', 'stream_method'),
    #     (tuple(offline_cctv.keys()), 'HLS')
    # )

    # update_data(
    #     'cctv_locations_general',
    #     ('is_online',),
    #     (False,),
    #     ('cam_id', 'stream_method'),
    #     (tuple(HLS_unresponsive.keys()), 'HLS')
    # )

    # save_cctv_images(HLS_image_result, "./data/screenshot", "TODAY")
        


def prepare_scrape_image_HLS_workers(cctvURL: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str], List[Tuple[str, Tuple[bytes], Tuple[datetime]]]]:
    config = {
        'max_workers': 80,
        'interval': 1,
        'target_image_count': 1,
        'timeout': 300.0,
        'max_retries': 2,
    }

    semaphore_1 = Semaphore(config['max_workers'])
    semaphore_2 = Semaphore(config['max_workers'])
    working_cctv, offline_cctv, unresponsive_cctv = {}, {}, {}
    image_result: List[Tuple[str, Tuple[bytes, ...], Tuple[datetime, ...]]] = []

    logger.info(f"[THREADING-S-HLS] CCTV List count = {len(cctvURL)}: {list(cctvURL.keys())}")
    
    
    logger.info("[THREADING-S-HLS] Initializing HLS workers.")
    logger.info("[THREADING-S-HLS] Verifying CCTV status...")

    run_threaded(check_cctv_status, semaphore_1, *[(camera_id, url, working_cctv, offline_cctv) for camera_id, url in cctvURL.items()])
    
    logger.info("[THREADING-S-HLS] Verify CCTV status done.")
    sort_results(working_cctv, offline_cctv)
    logger.info(f"[THREADING-S-HLS] {len(working_cctv)} CCTVs are online: {list(working_cctv.keys())}")
    logger.info(f"[THREADING-S-HLS] {len(offline_cctv)} CCTVs are offline: {list(offline_cctv.keys())}")
    
    # logger.info(f"[THREADING-S-HLS] Scraping started, Images: {config['target_image_count']}, Interval: {config['interval']} second")
    # included_keys = ['interval', 'target_image_count', 'timeout', 'max_retries']
    # scraper_args = {k: config[k] for k in included_keys if k in config}
    # run_threaded(scrape_image_HLS, semaphore_2, *[(camera_id, url, image_result, working_cctv, unresponsive_cctv, *scraper_args.values()) 
    #                                  for camera_id, url in working_cctv.items()])
    
    # logger.info("[THREADING-S-HLS] Scraping done.")

    # sort_results(working_cctv, unresponsive_cctv, image_result)
    # logger.info(f"[THREADING-S-HLS] {len(working_cctv)} CCTVs are successfully captured: {list(working_cctv.keys())}")
    # logger.info(f"[THREADING-S-HLS] {len(unresponsive_cctv)} CCTVs are unresponsive: {list(unresponsive_cctv.keys())}")

    return working_cctv, unresponsive_cctv, offline_cctv, image_result


def prepare_scrape_image_BMA_workers(cctvSessions: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str], List[Tuple[str, Tuple[bytes], Tuple[datetime]]]]:
    config = {
        'max_workers': 80,
        'target_image_count': 2
    }

    semaphore = Semaphore(config['max_workers'])
    working_session, unresponsive_session = {}, {}
    image_result: List[Tuple[str, Tuple[bytes, ...], Tuple[datetime, ...]]] = []

    logger.info("[THREADING-S-BMA] Initializing BMA workers.")
    logger.info("[THREADING-S-BMA] Scraping started.")

    run_threaded(scrape_image_BMA, semaphore, *[(camera_id, session_id, image_result, working_session, unresponsive_session, config['target_image_count']) 
                                     for camera_id, session_id in cctvSessions.items()])

    logger.info("[THREADING-S-BMA] Scraping done.")

    sort_results(working_session, unresponsive_session, image_result)
    logger.info(f"[THREADING-S-BMA] {len(working_session)} sessions are working from CCTV: {list(working_session.keys())}")
    logger.info(f"[THREADING-S-BMA] {len(unresponsive_session)} sessions are unresponsive from CCTV: {unresponsive_session}")

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

def getHLSInfo():
    HLS_information = retrieve_data(
            'cctv_locations_general',
            ('Cam_ID', 'Stream_Link_1'),
            ('Stream_Method',),
            ('HLS',)
        )
    
    if not HLS_information:
        logger.warning("[INFO] No HLS link found or failed to load.")
        logger.warning(f"[INFO] Scraping for HLS will not be initiated because no HLS link is provided.")
        return False, None
    
    return True, HLS_information


def getBMAInfo():
    BMA_JSON_result = load_latest_cctv_sessions_from_json()

    if not BMA_JSON_result:
        logger.warning("[INFO] No JSON file found or failed to load.")
        logger.warning(f"[INFO] Scraping for BMA will not be initiated because no session ID is provided.")
        return False, None

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
        logger.info(f"[INFO] Session IDs are valid, scraping for BMA will be initiated soon.")
        return True, BMA_JSON_result
        
    else:
        # Case 2:
        # This scrip just check for refresh times so it will not redundant with the sessionID.py
        # This script designed to scrape image, not preparing session ID.
        # So this condition will just terminate the script as sessionID have been expired.
        logger.warning(f"[INFO] Scraping for BMA will not be initiated because refresh times exceed their maximum allowed time differences.")
        # exit(0)
        return False, None


if __name__ == "__main__":
    log_setup("./logs/imageScraper","Scraper")
    # get_video_resolution("ITICM_BMAMI0257", "https://camerai1.iticfoundation.org/hls/pty56.m3u8")
    # get_video_resolution("ITICM_BMAMI0272", "https://camerai1.iticfoundation.org/hls/pty71.m3u8")
    # get_video_resolution("ITICM_BMAMI0257", "https://camerai1.iticfoundation.org/hls/pty56.m3u8")



    scrape_BMA, BMA_JSON_result = getBMAInfo()
    scrape_HLS, HLS_information = getHLSInfo()

    scraper_factory(BMA_JSON_result, scrape_BMA,
                    HLS_information, scrape_HLS)





    