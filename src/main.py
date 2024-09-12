import sys
import threading
from threading import Semaphore
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Union, Optional, Literal

from cam_update import update_cctv_database, retrieve_camInfo_BMA
from log_config import logger, log_setup
from database import *
from json_manager import save_alive_session_to_file, load_latest_cctv_sessions_from_json
from worker import create_sessionID, refresh_sessionID
from utils import sort_key, readableTime, create_cctv_status_dict


def initialize() -> int:
    if len(sys.argv) > 1:  # Check if an argument is provided
        param = int(sys.argv[1])  # Get the parameter from command-line arguments
    else:
        try:
            param = int(input("Please enter the parameter number: "))
        except ValueError:
            print("Invalid input. Please enter a valid number.", file=sys.stderr)
            sys.exit(1)

    log_setup()
    logger.info(f"[MAIN] Application initialized with parameter {param}")
    logger.info("[MAIN] Application started...")

    return param


def finalize(cctv_list: Union[List[str], None], alive_session: Dict[str, str], cctv_fail: List[str], current_time: str, latest_update_time: str) -> None:
    alive_session_count = len(alive_session)
    cctv_fail_count = len(cctv_fail)

    if cctv_list:
        scraped_cctv = len(cctv_list)
        logger.info(f"[MAIN] Total number of scraped CCTVs: {scraped_cctv}")
        logger.info(f"[MAIN] Successfully processed {alive_session_count} CCTVs out of {scraped_cctv}.")

        if scraped_cctv != (alive_session_count + cctv_fail_count):
            logger.warning("[MAIN] Number of items in `CCTV_LIST` does not equal to the sum of `alive_session_count` and `cctv_fail_count`")
    else:
        logger.info(f"[MAIN] Successfully processed {alive_session_count} CCTVs.")

    if cctv_fail:
        logger.info(f"[MAIN] {cctv_fail_count} CCTV IDs failed to prepare and will not be available: {cctv_fail}")
        update_isCamOnline(create_cctv_status_dict(cctv_fail, False))

    update_isCamOnline(list(alive_session.keys()))
    save_alive_session_to_file(alive_session, current_time, latest_update_time if not cctv_list else current_time)

    logger.info("[MAIN] Finalization process completed.")


# Function to manage workers for session creation
def prepare_create_sessionID_workers(cctv_list: List[str], alive_session: Dict[str, str] = None) -> Tuple[Dict[str, str], List[str]]:
    threads = []
    max_workers = 80
    semaphore = Semaphore(max_workers)

    cctv_fail = []
    if alive_session is None:
        alive_session = {}

    logger.info("[THREADING-C] Initializing session creation workers.")

    for camera_id in cctv_list:
        semaphore.acquire()
        thread = threading.Thread(target=create_sessionID, args=(camera_id, semaphore, alive_session, cctv_fail))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    alive_session = dict(sorted(alive_session.items(), key=lambda x: sort_key(x[0])))
    cctv_fail = sorted(cctv_fail, key=sort_key)

    alive_count = len(alive_session)
    fail_count = len(cctv_fail)

    logger.info(f"[THREADING-C] {alive_count} sessions are alive from CCTV: {list(alive_session.keys())}\n")
    
    logger.info(f"[THREADING-C] {fail_count} sessions are failed to create from CCTV: {cctv_fail}\n")

    logger.info(f"[THREADING-C] All sessions are validated.\n\n")

    return alive_session, cctv_fail


# Function to manage workers for session refreshion
def prepare_refresh_sessionID_workers(loaded_JSON_cctvSessions: Dict[str, str]) -> Tuple[Dict[str, str], List[str]]:
    threads = []
    max_workers = 80
    semaphore = Semaphore(max_workers)
    
    alive_session = {}
    offline_session = []

    logger.info("[THREADING-R] Initializing session validation workers.")
    
    for camera_id, session_id in loaded_JSON_cctvSessions.items():
        semaphore.acquire()  # Acquire a slot for this thread
        thread = threading.Thread(target=refresh_sessionID, args=(camera_id, session_id, semaphore, alive_session, offline_session))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()


    offline_session = sorted(offline_session, key=sort_key)
    alive_session = dict(sorted(alive_session.items(), key=lambda x: sort_key(x[0])))

    alive_count = len(alive_session)
    offline_count = len(offline_session)


    logger.info(f"[THREADING-R] {alive_count} sessions are alive from CCTV: {list(alive_session.keys())}\n")
    
    logger.info(f"[THREADING-R] {offline_count} sessions are offline from CCTV: {offline_session}\n")

    logger.info(f"[THREADING-R] All sessions are validated.\n\n")

    return alive_session, offline_session




def sync_cctv_sessions(alive_session: Dict[str, str], offline_session: List[str]) -> Tuple[Union[List[str], Literal[False]], Optional[List[str]]]:
    logger.info("[SYNC_CCTV] Syncing CCTV sessions...")
    
    # Call retrieve_camInfo_BMA() to get a list of tuples or False if failed
    result = retrieve_camInfo_BMA()

    if not result:
        logger.error("[SYNC_CCTV] Failed to retrieve camera info from BMA.")
        logger.warning("[SYNC_CCTV] Failed to sync CCTV sessions.\n\n")
        return False, None

    # Extract the cam IDs from the result (assuming the tuple format is like (cam_id, some_other_data))
    current_cctv = [cam[0] for cam in result]  # List of current cam IDs

    # Initialize get_session list to store new cam IDs that need sessions
    get_session = []

    # Step 1: Check for cam IDs in current_cctv that are not present in alive_session
    for cam_id in current_cctv:
        if cam_id not in alive_session:
            get_session.append(cam_id)

    # Step 2: Check for cam IDs in alive_session that are not present in current_cctv
    for cam_id in alive_session.keys():
        if cam_id not in current_cctv:
            offline_session.append(cam_id)
            # For this part, add a function to recheck the image in this case again. Fetch the image (maybe 5-6 images evry 2 sec) and see if there are any movement or not.
            # This could be done by checking difference in imgae size.
            # Some CCTV do not appear in the BMA Traffic but when fetch the image, it still working.
            # Most of the offline CCVT are also have the image but it already freeze
            # This edge case happen a lot as CCTV list from BMA Traffic keep changing frequently. (even around 2-3 minutes some CCTV can become offline or online)
            logger.warning(f"[SYNC_CCTV] CCTV ID {cam_id} is alive but not found in current cam list. Marking as offline for edge case.")

    # Log results
    logger.info(f"[SYNC_CCTV] Total online CCTV from BMA Traffic: {len(current_cctv)}")
    logger.info(f"[SYNC_CCTV] {len(get_session)} CCTV(s) need new session ID which are {sorted(get_session, key=sort_key)}\n")

    logger.info(f"[SYNC_CCTV] {len(offline_session)} CCTV(s) are offline (including edge cases): {offline_session}\n")

    logger.info("[SYNC_CCTV] All CCTV sessions are synced.\n\n")


    return get_session, offline_session


def startRefreshingSessionID(camDistance: int, loaded_JSON_cctvSessions: Dict[str, str], loaded_JSON_latestUpdateTime: str) -> None:
    logger.info("[MAIN] Starting to refresh session ID.")
    alive_session, offline_session = prepare_refresh_sessionID_workers(loaded_JSON_cctvSessions)
    get_session, offline_session = sync_cctv_sessions(alive_session, offline_session)

    if not get_session:
        logger.warning("[MAIN] Defaulting to CCTV list from database.")
        get_session = retrieve_onlineCam()

    alive_session, cctv_fail = prepare_create_sessionID_workers(get_session, alive_session)

    if not alive_session and set(cctv_fail) == set(get_session):
        logger.warning("[MAIN] Could not get new session ID from BMA Traffic.")
        logger.warning("[MAIN] Failed to refresh and prepare all session IDs.")
        logger.warning("[MAIN] Trying to get a new set of CCTV info and session ID.\n\n")
        startGettingNewSessionID(camDistance)
        return

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    finalize(None, alive_session, cctv_fail, current_time, loaded_JSON_latestUpdateTime)
    
    logger.info("[MAIN] All session IDs have been successfully refreshed and saved.\n\n")


def startGettingNewSessionID(camDistance: int) -> None:
    logger.info("[MAIN] Starting to get a new set of CCTV info and session ID.")
    # cctv_list = ['7', '11', '39', '77', '83', '572']
    cctv_list = update_cctv_database(camDistance)
    if not cctv_list:
        logger.error("[MAIN] Script will be terminated due to failure of getting CCTV IDs and session IDs.\n\n")
        return

    alive_session, cctv_fail = prepare_create_sessionID_workers(cctv_list)
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    finalize(cctv_list, alive_session, cctv_fail, current_time, current_time)

    logger.info("[MAIN] All session IDs have been successfully prepared and saved.\n\n")



if __name__ == "__main__":
    camDistance = initialize()
    result = load_latest_cctv_sessions_from_json()

    if result:
        loaded_JSON_latestRefreshTime, loaded_JSON_latestUpdateTime, loaded_JSON_cctvSessions = result
        logger.info(f"[INFO] Latest Refresh Time: {loaded_JSON_latestRefreshTime}")
        logger.info(f"[INFO] Latest Update Time: {loaded_JSON_latestUpdateTime}")
        logger.info(f"[INFO] CCTV Sessions: {loaded_JSON_cctvSessions}")

        current_time = datetime.now()
        loaded_JSON_latestUpdateTime_dt = datetime.strptime(loaded_JSON_latestUpdateTime, "%Y-%m-%d %H:%M:%S")
        timeDiff = current_time - loaded_JSON_latestUpdateTime_dt

        total_seconds = int(timeDiff.total_seconds())
        readable_diff = readableTime(total_seconds)

        if timeDiff < timedelta(hours=1, minutes=30):
            logger.info(f"[INFO] The latest update occurred at {loaded_JSON_latestUpdateTime}, which was {readable_diff}.")
            startRefreshingSessionID(camDistance, loaded_JSON_cctvSessions, loaded_JSON_latestUpdateTime)

        else:
            logger.info("[INFO] The latest update time is older than 3 hours.")
            startGettingNewSessionID(camDistance)
    else:
        logger.warning("[INFO] No JSON file found or failed to load. Fetching all session ID")
        startGettingNewSessionID(camDistance)
        
