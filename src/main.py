import sys
import threading
from threading import Semaphore
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Union, Optional, Literal

from cam_update import update_cctv_database, retrieve_camInfo_BMA
from log_config import logger, log_setup
from database import *
from json_manager import save_alive_session_to_file, load_latest_cctv_sessions_from_json
from worker import create_sessionID, validate_sessionID, quick_refresh_sessionID
from utils import sort_key, readableTime, create_cctv_status_dict, select_non_empty, check_cctv_integrity


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


def finalize(cctv_list: Union[List[str], None], cctv_working: Dict[str, str], cctv_unresponsive: Dict[str, str], cctv_fail: List[str], cctv_recheck: Union[Dict[str, str], None], current_time: str, latest_update_time: str) -> None:
    cctv_working_count = len(cctv_working)
    cctv_unresponsive_count = len(cctv_unresponsive)
    cctv_fail_count = 0
    cctv_recheck_count = 0

    if cctv_fail:
        cctv_fail_count = len(cctv_fail)
    # else:
    #     logger.info("No CCTV failed to prepare session ID from prepare_create_sessionID_workers().")

    if cctv_list and not cctv_recheck:
        # This block is only for startGettingNewSessionID()
        cctv_list_count = len(cctv_list)
        logger.info(f"[MAIN] Successfully processed {cctv_working_count} CCTVs out of {cctv_list_count} CCTVs.")

        if cctv_list_count != (cctv_working_count + cctv_fail_count + cctv_unresponsive_count):
            logger.warning("[MAIN] Number of items in `CCTV_LIST` does not equal to the sum of `cctv_working_count`, `cctv_fail_count`, and `cctv_unresponsive_count`")
    else:
        # Else, this is for startValidatingSessionID()
        logger.info(f"[MAIN] Successfully processed {cctv_working_count} CCTVs.") # This part have to check logic again

    if cctv_fail:
        logger.warning(f"[MAIN] {cctv_fail_count} CCTVs failed to prepare and will not be available: {cctv_fail}")
        update_isCamOnline(create_cctv_status_dict(cctv_fail, False))

    if cctv_unresponsive:
        logger.warning(f"[MAIN] {cctv_unresponsive_count} CCTVs are unresponsive and will not be available: {cctv_unresponsive}")
        update_isCamOnline(create_cctv_status_dict(list(cctv_unresponsive.keys()), False))

    if cctv_recheck:
        cctv_recheck_count = len(cctv_recheck)
        logger.warning(f"[MAIN] {cctv_recheck_count} might be unavailable. Consider checking them: {cctv_recheck}")

    update_isCamOnline(list(cctv_working.keys()))
   
    # try:
    logger.info(f"[MAIN] Starting integrity check...")
    logger.info(f"[DEBUG] cctv_working: {cctv_working}")
    logger.info(f"[DEBUG] cctv_unresponsive: {cctv_unresponsive}")
    logger.info(f"[DEBUG] cctv_fail: {cctv_fail}")
    integrity_passed, issues = check_cctv_integrity(cctv_working, cctv_unresponsive, cctv_fail)

    if integrity_passed:
        logger.info(f"[MAIN] Integrity check passed.")
    else:
        logger.warning(f"[MAIN] Integrity check failed.")
        logger.warning("[MAIN] Issues found:")
        for issue in issues:
            logger.warning(f"{issue}\n")
    logger.info(f"[MAIN] Integrity check done.")
    # except Exception as e:
    #         logger.error(f"[MAIN] Integrity check failed: {e}")


    save_alive_session_to_file(cctv_working, current_time, latest_update_time)

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

    logger.info(f"[THREADING-C] {alive_count} sessions has been prepare for CCTV: {list(alive_session.keys())}\n")
    
    logger.info(f"[THREADING-C] {fail_count} sessions are failed to create from CCTV: {cctv_fail}\n")

    logger.info(f"[THREADING-C] All sessions are validated.\n\n")

    return alive_session, cctv_fail


# Function to manage workers for session refreshion
def prepare_validate_sessionID_workers(cctvSessions: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str]]:
    threads = []
    max_workers = 80
    semaphore = Semaphore(max_workers)
    
    working_session = {}
    unresponsive_session = {}

    logger.info("[THREADING-V] Initializing session validation workers.")
    
    for camera_id, session_id in cctvSessions.items():
        semaphore.acquire()  # Acquire a slot for this thread
        thread = threading.Thread(target=validate_sessionID, args=(camera_id, session_id, semaphore, working_session, unresponsive_session))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()


    unresponsive_session = dict(sorted(unresponsive_session.items(), key=lambda x: sort_key(x[0])))
    working_session = dict(sorted(working_session.items(), key=lambda x: sort_key(x[0])))

    working_count = len(working_session)
    unresponsive_count = len(unresponsive_session)


    logger.info(f"[THREADING-V] {working_count} sessions are working from CCTV: {list(working_session.keys())}\n")
    
    logger.info(f"[THREADING-V] {unresponsive_count} sessions are unresponsive from CCTV: {unresponsive_session}\n")

    logger.info(f"[THREADING-V] All sessions are validated.\n\n")

    return working_session, unresponsive_session


# Function to manage workers for quick session refreshion
def prepare_quick_refresh_sessionID_workers(loaded_JSON_cctvSessions: Dict[str, str]) -> None:
    threads = []
    max_workers = 80
    semaphore = Semaphore(max_workers)

    for camera_id, session_id in loaded_JSON_cctvSessions.items():
        semaphore.acquire()  # Acquire a slot for this thread
        thread = threading.Thread(target=quick_refresh_sessionID, args=(camera_id, session_id, semaphore))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()


def sync_cctv_sessions(working_session: Dict[str, str]) -> Tuple[Union[List[str], Literal[False]], Optional[Dict[str, str]]]:
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

    # Initialize recheck dictionary to store cam IDs that need verify images movement
    recheck_session = {}

    # Step 1: Check for cam IDs in current_cctv that are not present in alive_session
    for cam_id in current_cctv:
        if cam_id not in working_session:
            get_session.append(cam_id)

    # Step 2: Check for cam IDs in alive_session that are not present in current_cctv
    for cam_id in working_session.keys():
        if cam_id not in current_cctv:
            recheck_session[cam_id] = working_session[cam_id]
            logger.warning(f"[SYNC_CCTV] CCTV ID {cam_id} was checked that is working but not found in BMA Traffic list.")
            '''
            Any cctv ID that get in here are already verified that image size > 5120 bytes and have movements
            Display warnning message for this part just in case
            '''

    get_session = sorted(get_session, key=sort_key)

    # Log results
    logger.info(f"[SYNC_CCTV] Total online CCTV from BMA Traffic: {len(current_cctv)}")
    logger.info(f"[SYNC_CCTV] {len(get_session)} CCTV(s) need new session ID which are {get_session}\n")

    logger.info(f"[SYNC_CCTV] {len(recheck_session)} CCTV(s) seem to be offline. Movement detector will be initialize: {recheck_session}\n")

    logger.info("[SYNC_CCTV] All CCTV sessions are synced.\n\n")


    return get_session, recheck_session


def startValidatingSessionID(camDistance: int, loaded_JSON_cctvSessions: Dict[str, str], loaded_JSON_latestUpdateTime: str) -> None:
    try:
        cctv_working_merge = None
        cctv_unresponsive_merge = None
        cctv_fail = []
        
        logger.info("[MAIN] Starting to validate session ID.")
        cctv_working, cctv_unresponsive = prepare_validate_sessionID_workers(loaded_JSON_cctvSessions)
        '''
        offline_session should be use to show list of offline cct as well, but now have to remove it from sync_cctv_sessions()
        because this is offline not edge case.

        offline_session.append(cam_id)
        logger.warning(f"[SYNC_CCTV] CCTV ID {cam_id} is alive but not found in current cam list. Marking as offline for edge case.")
        logger.info(f"[SYNC_CCTV] {len(offline_session)} CCTV(s) are offline (including edge cases): {offline_session}\n")
        '''
        
        get_session, cctv_recheck = sync_cctv_sessions(cctv_working)

        if get_session:
            logger.info(f"[MAIN] {len(get_session)} New CCTV is available which are {get_session}. "
                        f"Starting to get session IDs")
            cctv_session, cctv_fail = prepare_create_sessionID_workers(get_session)
            cctv_working_new, cctv_unresponsive_new = prepare_validate_sessionID_workers(cctv_session)

            # Merge cctv_working and cctv_working_new
            cctv_working_merge = {**cctv_working, **cctv_working_new}
            cctv_working_merge = dict(sorted(cctv_working_merge.items(), key=lambda x: sort_key(x[0])))

            # Remove keys from cctv_unresponsive that exist in cctv_working_merge
            cctv_unresponsive = {key: value for key, value in cctv_unresponsive.items() if key not in cctv_working_merge}
            
            # Merge cctv_unresponsive and cctv_unresponsive_new
            cctv_unresponsive_merge = {**cctv_unresponsive, **cctv_unresponsive_new}
            cctv_unresponsive_merge = dict(sorted(cctv_unresponsive_merge.items(), key=lambda x: sort_key(x[0])))

        cctv_working_final, _ = select_non_empty(cctv_working_merge, "cctv_working_merge",
                                                    cctv_working, "cctv_working",
                                                    {}, None, "Working CCTV Dictionary")
        cctv_unresponsive_final, _ = select_non_empty(cctv_unresponsive_merge, "cctv_unresponsive_merge",
                                                    cctv_unresponsive, "cctv_unresponsive",
                                                    {}, None, "Unresponsive CCTV Dictionary")

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        finalize(None, cctv_working_final, cctv_unresponsive_final, cctv_fail, cctv_recheck, current_time, loaded_JSON_latestUpdateTime)
            
    except Exception as e:
        logger.error(f"[MAIN] Error startValidatingSessionID: {e}")
        logger.warning("[MAIN] Could not get new session ID from BMA Traffic.")
        logger.warning("[MAIN] Failed to refresh and prepare all session IDs.")
        logger.warning("[MAIN] Trying to get a new set of CCTV info and session ID.\n\n")
        startGettingNewSessionID(camDistance)


def startGettingNewSessionID(camDistance: int) -> None:
    logger.info("[MAIN] Starting to get a new set of CCTV info and session ID.")
    # cctv_list = ['7', '11', '39', '77', '83', '572']
    cctv_list_bma, cctv_list_db_secondary = update_cctv_database(camDistance)
    cctv_list_db_primary = retrieve_camID()
    cctv_fail = []
    
    if not cctv_list_db_primary and not cctv_list_bma and not cctv_list_db_secondary:
        logger.error("[MAIN] Script will be terminated due to failure of getting CCTV IDs and session IDs.\n\n")
        return

    cctv_list, item_name = select_non_empty(cctv_list_db_primary, "Latest CCTV IDs from database",
                                 cctv_list_bma, "CCTV IDs from BMA Traffic",
                                 cctv_list_db_secondary, "CCTV IDs from database before update new cam happen",
                                 "cctv_list")

    logger.info(f"[MAIN] '{item_name}' has been selected, containing {len(cctv_list)} CCTV IDs.")

    # this function only get session ID and play video. It do not filter img less than 5120 bytes out
    cctv_session, cctv_fail = prepare_create_sessionID_workers(cctv_list) 

    # check if img size is less than 5120 kb or not
    cctv_working, cctv_unresponsive = prepare_validate_sessionID_workers(cctv_session)

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    finalize(cctv_list, cctv_working, cctv_unresponsive, cctv_fail, None, current_time, current_time)

    logger.info("[MAIN] All session IDs have been successfully prepared and saved.\n\n")


def startQuickRefreshSessionID(loaded_JSON_cctvSessions: Dict[str, str]) -> None:
    logger.info("[MAIN] Starting quick refresh to keep session IDs alive during new session ID processing.")
    prepare_quick_refresh_sessionID_workers(loaded_JSON_cctvSessions)
    logger.info("[MAIN] Quick refresh of session IDs completed.")



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
        max_timeDiff = timedelta(hours=2, minutes=0)
        readable_max_timeDiff = readableTime(max_timeDiff.total_seconds())

        if timeDiff < max_timeDiff:
            logger.info(f"[INFO] The latest update occurred at {loaded_JSON_latestUpdateTime}, which was {readable_diff} ago.")
            startValidatingSessionID(camDistance, loaded_JSON_cctvSessions, loaded_JSON_latestUpdateTime)

        else:
            logger.info(f"[INFO] The latest update occurred at {loaded_JSON_latestUpdateTime}, {readable_diff} ago, exceeding the maximum allowed time difference of {readable_max_timeDiff}.")
            startQuickRefreshSessionID(loaded_JSON_cctvSessions)
            startGettingNewSessionID(camDistance)
    else:
        logger.warning("[INFO] No JSON file found or failed to load. Fetching all session ID")
        startGettingNewSessionID(camDistance)
        
'''
1. In case where all session IDs are expried but script try to validate all of them, it will take time around 10 minutes
2. In case where all max time diff exceeded, it will take time around 10 minutes
3. In case of validating sesion IDs, it will take around 
'''