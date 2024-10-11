
import sys
import threading
from threading import Semaphore
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Union, Optional, Literal

from sessionID import start
from cctv_operation_BMA.cam_update import update_cctv_database, retrieve_camInfo_BMA
from utils.log_config import logger, log_setup
from utils.Database import retrieve_data, update_data
from utils.json_manager import save_alive_session_to_file, load_latest_cctv_sessions_from_json
from cctv_operation_BMA.worker import create_sessionID, validate_sessionID, quick_refresh_sessionID
from utils.utils import sort_key, readable_time, create_cctv_status_dict, select_non_empty, check_cctv_integrity


def getCCTVList():
    retrieve_data('cctv_locations_preprocessing',
                  ('cam_id',),
                  ('is_online',),
                  (True,)
                  )
    return


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




if __name__ == "__main__":
    log_setup("./logs/imageScraper","sessionID")
    result = load_latest_cctv_sessions_from_json()

    if not result:
        logger.warning("[INFO] No JSON file found or failed to load. Fetching all session ID")
        
    else:
        latestRefreshTime, latestUpdateTime, cctvSessions = result
        current_time = datetime.now()

        def parse_time_and_diff(time_str):
            time_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            diff = current_time - time_dt
            return time_dt, diff, readable_time(int(diff.total_seconds()))

        refreshTime, timeDiffRefresh, readable_diff_refresh = parse_time_and_diff(latestRefreshTime)
        updateTime, timeDiffUpdate, readable_diff_update = parse_time_and_diff(latestUpdateTime)

        max_timeDiffUpdate = timedelta(hours=4)
        max_timeDiffRefresh = timedelta(minutes=17)

        logger.info(f"[INFO] Latest Refresh Time: {latestRefreshTime}")
        logger.info(f"[INFO] Latest Update Time: {latestUpdateTime}")
        logger.info(f"[INFO] CCTV Sessions: {cctvSessions}")
        logger.info(f"[INFO] The latest update occurred at {latestUpdateTime}, which was {readable_diff_update} ago.")
        logger.info(f"[INFO] The latest refresh occurred at {latestRefreshTime}, which was {readable_diff_refresh} ago.")

        if timeDiffUpdate < max_timeDiffUpdate and timeDiffRefresh < max_timeDiffRefresh:
            # Case 1: Both the update and refresh times are within the valid range, so simply do a quick refresh and scraped image.
            # Do the scrapign now
            print("")
            
        elif timeDiffUpdate < max_timeDiffUpdate and timeDiffRefresh >= max_timeDiffRefresh:
            # Case 2: The update time is still valid, but the refresh time has expired, meaning all sessionIDs have expired. A new sessionID must be obtained.
            logger.info(f"[INFO] The latest refresh occurred {readable_diff_refresh} ago, exceeding the maximum allowed time difference of {readable_time(max_timeDiffRefresh.total_seconds())}.")
            # Have to call sessionID.py

        elif timeDiffUpdate >= max_timeDiffUpdate and timeDiffRefresh <= max_timeDiffRefresh:
            # Case 3: It is time to update the sessionID, but before that, a quick refresh is necessary to ensure that all sessionIDs remain usable during the update.
            logger.info(f"[INFO] The latest update occurred {readable_diff_update} ago, exceeding the maximum allowed time difference of {readable_time(max_timeDiffUpdate.total_seconds())}.")
            # Have to call sessionID.py

        else:
            # Case 4: Both the update and refresh times have expired, indicating that all sessionIDs have expired, and a new one must be acquired.
            logger.info(f"[INFO] Both update and refresh times exceed their maximum allowed time differences.")
            # Have to call sessionID.py

            