from worker import create_sessionID, validate_sessionID
from updateCamInfo import startUpdate
from utils.progress_gui import gui_setup, get_progress_gui
from utils.log_config import log_setup, logger
from utils.scraper_config import config
from utils.utils import sort_key, select_non_empty, create_cctv_status_dict, check_cctv_integrity
from utils.Database import retrieve_data, update_data
from updateCamInfo import update_cctv_database, retrieve_camInfo_BMA
import threading
from threading import Semaphore
from typing import List, Dict, Tuple, Optional, Union, Literal
from datetime import datetime, timedelta

camera_ids = startUpdate(170)    # List of online CCTV IDs + update CCTV info in DB + distance in meter for clustering

# Configure logging
log_setup()

# Setup the ProgressGUI is disable now
# gui_setup(total_tasks=len(camera_ids))


def finalize(cctv_list: Optional[List[str]], cctv_working: Dict[str, str], cctv_unresponsive: Dict[str, str], 
             cctv_fail: List[str], cctv_recheck: Optional[Dict[str, str]], current_time: str, latest_update_time: str) -> None:
    cctv_working_count, cctv_unresponsive_count, cctv_fail_count = map(len, (cctv_working, cctv_unresponsive, cctv_fail or []))
    cctv_recheck_count = len(cctv_recheck or {})

    if cctv_list and not cctv_recheck:
        cctv_list_count = len(cctv_list)
        logger.info(f"[MAIN] Successfully processed {cctv_working_count} CCTVs out of {cctv_list_count} CCTVs.")
        if cctv_list_count != (cctv_working_count + cctv_fail_count + cctv_unresponsive_count):
            logger.warning("[MAIN] Number of items in `CCTV_LIST` does not equal to the sum of `cctv_working_count`, `cctv_fail_count`, and `cctv_unresponsive_count`")
    else:
        logger.info(f"[MAIN] Successfully processed {cctv_working_count} CCTVs.")

    for category, count, items in [
        ("failed", cctv_fail_count, cctv_fail),
        ("unresponsive", cctv_unresponsive_count, cctv_unresponsive),
        ("need rechecking", cctv_recheck_count, cctv_recheck)
    ]:
        if items:
            logger.warning(f"[MAIN] {count} CCTVs are {category}: {items}")


    table = 'cctv_locations_preprocessing'
    columns_to_update = ['is_online']
    
    data_to_update = [(False,)]
    update_data(
        table,
        columns_to_update,
        data_to_update
    )

    data_to_update = [(True,)]
    columns_to_check_condition = ['cam_id']
    data_to_check_condition = [list(cctv_working.keys())]
    update_data(
        table,
        columns_to_update,
        data_to_update,
        columns_to_check_condition,
        data_to_check_condition
    )

    data_to_update = [(False,)]
    columns_to_check_condition = ['cam_id']
    data_to_check_condition = [list(cctv_unresponsive.keys()) + cctv_fail]
    update_data(
        table,
        columns_to_update,
        data_to_update,
        columns_to_check_condition,
        data_to_check_condition
    )

    integrity_passed, issues = check_cctv_integrity(cctv_working, cctv_unresponsive, cctv_fail)
    logger.info(f"[MAIN] Integrity check {'passed' if integrity_passed else 'failed'}.")
    if not integrity_passed:
        for issue in issues:
            logger.warning(f"[MAIN] {issue}")

    # save_alive_session_to_file(cctv_working, current_time, latest_update_time)
    logger.info("[MAIN] Finalization process completed.")


def prepare_create_sessionID_workers(cctv_list: List[str], alive_session: Dict[str, str] = None) -> Tuple[Dict[str, str], List[str]]:
    max_workers = 80
    semaphore = Semaphore(max_workers)
    threads = []
    cctv_fail = []
    alive_session = alive_session or {}

    logger.info("[THREADING-C] Initializing session creation workers.")

    for camera_id in cctv_list:
        semaphore.acquire()
        thread = threading.Thread(target=create_sessionID, args=(camera_id, semaphore, alive_session, cctv_fail))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    alive_session = dict(sorted(alive_session.items(), key=lambda x: sort_key(x[0])))
    cctv_fail = sorted(cctv_fail, key=sort_key)

    logger.info(f"[THREADING-C] {len(alive_session)} sessions prepared for CCTV: {list(alive_session.keys())}")
    logger.info(f"[THREADING-C] {len(cctv_fail)} sessions failed to create from CCTV: {cctv_fail}")
    logger.info("[THREADING-C] All sessions are validated.")

    return alive_session, cctv_fail

def prepare_validate_sessionID_workers(cctvSessions: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, List[bytes]]]:
    max_workers = 80
    semaphore = Semaphore(max_workers)
    threads = []
    working_session = {}
    unresponsive_session = {}
    all_cctv_image_list = {}

    logger.info("[THREADING-V] Initializing session validation workers.")

    for camera_id, session_id in cctvSessions.items():
        semaphore.acquire()
        thread = threading.Thread(target=validate_sessionID, args=(camera_id, session_id, semaphore, working_session, unresponsive_session, all_cctv_image_list))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()
    
    for session_dict in (working_session, unresponsive_session):
        sorted_items = sorted(session_dict.items(), key=lambda x: sort_key(x[0]))
        session_dict.clear()
        session_dict.update(sorted_items)

    logger.info(f"[THREADING-V] {len(working_session)} sessions are working from CCTV: {list(working_session.keys())}")
    logger.info(f"[THREADING-V] {len(unresponsive_session)} sessions are unresponsive from CCTV: {unresponsive_session}")
    logger.info("[THREADING-V] All sessions are validated.")

    return working_session, unresponsive_session, all_cctv_image_list


def sync_cctv_sessions(working_session: Dict[str, str]) -> Tuple[Union[List[str], Literal[False]], Optional[Dict[str, str]]]:
    logger.info("[SYNC_CCTV] Syncing CCTV sessions...")
    result = retrieve_camInfo_BMA()
    if not result:
        logger.error("[SYNC_CCTV] Failed to retrieve camera info from BMA.")
        logger.warning("[SYNC_CCTV] Failed to sync CCTV sessions.")
        return False, None

    current_cctv = {cam[0] for cam in result}
    get_session = sorted(current_cctv - set(working_session.keys()), key=sort_key)
    recheck_session = {cam_id: session_id for cam_id, session_id in working_session.items() if cam_id not in current_cctv}

    logger.warning(f"[SYNC_CCTV] The following CCTV was checked as working but not found in BMA Traffic list: {recheck_session}")

    logger.info(f"[SYNC_CCTV] Total online CCTV from BMA Traffic: {len(current_cctv)}")
    logger.info(f"[SYNC_CCTV] {len(get_session)} CCTV(s) need new session ID: {get_session}")
    logger.info(f"[SYNC_CCTV] {len(recheck_session)} CCTV(s) seem to be offline: {recheck_session}")
    logger.info("[SYNC_CCTV] All CCTV sessions are synced.")

    return get_session, recheck_session

# Run this using JSON session ID
def startValidatingSessionID(camDistance: int, loaded_JSON_cctvSessions: Dict[str, str], loaded_JSON_latestUpdateTime: str) -> None:
    try:
        cctv_working, cctv_unresponsive, all_cctv_image_list = prepare_validate_sessionID_workers(loaded_JSON_cctvSessions)
        get_session, cctv_recheck = sync_cctv_sessions(cctv_working)

        if get_session:
            logger.info(f"[MAIN] {len(get_session)} New CCTV available: {get_session}.")
            logger.info(f"Starting to get session IDs")
            cctv_session, cctv_fail = prepare_create_sessionID_workers(get_session)
            cctv_working_new, cctv_unresponsive_new, all_cctv_image_list = prepare_validate_sessionID_workers(cctv_session)

            cctv_working.update(cctv_working_new)
            cctv_working = dict(sorted(cctv_working.items(), key=lambda x: sort_key(x[0])))

            cctv_unresponsive = {k: v for k, v in cctv_unresponsive.items() if k not in cctv_working}
            cctv_unresponsive.update(cctv_unresponsive_new)
            cctv_unresponsive = dict(sorted(cctv_unresponsive.items(), key=lambda x: sort_key(x[0])))

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        finalize(None, cctv_working, cctv_unresponsive, cctv_fail, cctv_recheck, current_time, loaded_JSON_latestUpdateTime)
    except Exception as e:
        logger.error(f"[MAIN] Error startValidatingSessionID: {e}")
        logger.warning("[MAIN] Failed to refresh and prepare all session IDs. Trying to get a new set of CCTV info and session ID.")
        startGettingNewSessionID(camDistance)


# Run this one when JSON session ID is unusable
def startGettingNewSessionID(camDistance: int) -> None:
    logger.info("[MAIN] Starting to get a new set of CCTV info and session ID.")
    cctv_list_bma, cctv_list_db_secondary = update_cctv_database(camDistance)

    table = 'cctv_locations_preprocessing'
    columns = ['cam_id']
    cctv_list_db_primary = retrieve_data(table, columns)
    
    if not any((cctv_list_db_primary, cctv_list_bma, cctv_list_db_secondary)):
        logger.error("[MAIN] Script will be terminated due to failure of getting CCTV IDs and session IDs.")
        return
    
    item1 = (cctv_list_db_primary, "Latest CCTV IDs from database")
    item2 = (cctv_list_bma, "CCTV IDs from BMA Traffic")
    item3 = (cctv_list_db_secondary, "CCTV IDs from database before update new cam happen")

    cctv_list, item_name = select_non_empty(item1, item2, item3, item_description="cctv_list")

    logger.info(f"[MAIN] '{item_name}' has been selected, containing {len(cctv_list)} CCTV IDs.")

    cctv_session, cctv_fail = prepare_create_sessionID_workers(cctv_list)
    cctv_working, cctv_unresponsive, all_cctv_image_list = prepare_validate_sessionID_workers(cctv_session)

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    finalize(cctv_list, cctv_working, cctv_unresponsive, cctv_fail, None, current_time, current_time)

    logger.info("[MAIN] All session IDs have been successfully prepared and saved.")




# def run_scraping_tasks():
#     try:
#         alive_session, cctv_fail = prepare_create_sessionID_workers()
#         working_session, unresponsive_session, all_cctv_image_list = prepare_validate_sessionID_workers(alive_session)
#     except Exception as e:
#         logger.error(f"An error occurred during scraping: {str(e)}")
#     finally:
#         get_progress_gui().quit()


# Start the progress GUI and run the scraping tasks
logger.info("Starting Progress GUI and scraping tasks")
# get_progress_gui().run(run_scraping_tasks, ())
logger.info("Completed scraping tasks")