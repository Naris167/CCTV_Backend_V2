import re
import ast
import requests
import time
from typing import List, Tuple, Union, Literal

from database import update_isCamOnline, retrieve_camLocation, add_camRecord, retrieve_onlineCam, update_camCluster
from utils import sort_key
from cam_cluster import cluster
from log_config import logger

BASE_URL = "http://www.bmatraffic.com"


# Get online CCTV list from BMA Traffic
def retrieve_camInfo_BMA(url: str = BASE_URL, max_retries: int = 5, delay: int = 5, timeout: int = 120) -> Union[List[Tuple[str, Union[str, None], Union[str, None], Union[str, None], Union[str, None], Union[str, None], Union[float, None], Union[float, None], Union[str, None], Union[str, None]]], Literal[False]]:
    # Return list of tuple or False if failed
    logger.info(f"[UPDATER] Getting camera list from {url}")
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()  # Check if the request was successful

            # Find the var locations = [...] data
            data_pattern = re.compile(r"var locations = (\[.*?\]);", re.DOTALL)
            match = data_pattern.search(response.text)

            if match:
                data_string = match.group(1)
                
                # Convert the JavaScript array to a Python list using ast.literal_eval
                json_data = ast.literal_eval(data_string)

                # Process data to use the specified column names
                processed_data = []
                for item in json_data:
                    code_match = re.match(r'^[A-Z0-9\-]+', item[1])
                    code = code_match.group(0) if code_match else ''
                    cam_name = item[1][len(code):].strip() if code else item[1]
                    
                    processed_item = (
                        item[0],       # ID (str)
                        code or None,  # Code (str or None)
                        cam_name or None,  # Cam_Name (str or None)
                        item[2] or None,   # Cam_Name_e (str or None)
                        item[3] or None,   # Cam_Location (str or None)
                        item[4] or None,   # Cam_Direction (str or None)
                        item[5] or None,   # Latitude (float or None)
                        item[6] or None,   # Longitude (float or None)
                        item[7] or None,   # IP (str or None)
                        item[8] or None    # Icon (str or None)
                    )
                    processed_data.append(processed_item)

                logger.info("[UPDATER] Successfully retrieved camera list.")
                return processed_data
            else:
                logger.error("[UPDATER] Error parsing camera list.")
                return False

        except requests.RequestException as e:
            retries += 1
            logger.warning(f"[UPDATER] Error retrieving camera list: {e}. Retry {retries + 1}/{max_retries}...")
            time.sleep(delay)  # Wait before retrying

    logger.error(f"[UPDATER] Failed to retrieve camera list after {max_retries} retries.")
    return False

# Compare both online_cam and db_cam.
# Take any duplicate record out from online_cam.
# Return a list of tuple of new CCTV only
# Return a list of tuple of all CCTV (ID, Latitude, and Longitude)

def filter_new_and_all_cams(
    online_cam_info: List[Tuple[str, Union[str, None], Union[str, None], Union[str, None], Union[str, None], Union[str, None], Union[float, None], Union[float, None], Union[str, None], Union[str, None]]],
    db_cam_coordinate: List[Tuple[str, float, float]]
) -> Tuple[
    List[Tuple[str, Union[str, None], Union[str, None], Union[str, None], Union[str, None], Union[str, None], Union[float, None], Union[float, None], Union[str, None], Union[str, None]]],
    List[Tuple[str, float, float]]
]:
    # Extract Cam_IDs from db_cam_coordinate (record from DB in a list of tuple) to create a set for quick lookup
    db_cam_ids = set(str(cam[0]) for cam in db_cam_coordinate)

    # List of tuple to store new camera info
    new_cam_info = []

    # List to store all unique cameras (combined db_cam_coordinate and online_cam_info)
    all_cams_coordinate = db_cam_coordinate.copy()  # Start with db_cam_coordinate data

    # Iterate over online_cam (list of tuple) to filter new cameras and update all_cams_combined
    for cam in online_cam_info:

        cam_id = str(cam[0])

        if cam_id not in db_cam_ids:
            # This camera is new, add to new_cam_info list
            new_cam_info.append(cam)
            # Also add to all_cams_combined list
            all_cams_coordinate.append((cam_id, cam[6], cam[7]))  # (Cam_ID, Latitude, Longitude)
        else:
            # Camera exists in db_cam, ensure it's in all_cams_combined
            # Since all_cams_combined starts with db_cam data, this step is redundant here
            pass

    return new_cam_info, all_cams_coordinate

def update_cctv_database(meters: int) -> List[str]:
    onlineCamInfo = retrieve_camInfo_BMA()
    dbCamCoordinate = retrieve_camLocation()
    cctv_list = []

    if onlineCamInfo:
        cctv_list = sorted([str(t[0]) for t in onlineCamInfo], key=sort_key)
        new_cams_info, all_cams_coordinate = filter_new_and_all_cams(onlineCamInfo, dbCamCoordinate)

        # Check if there are any new cameras
        # In case there are no new cctv, remove `not` here to manually run the script
        if not new_cams_info:
            logger.info("[UPDATER] No new cameras found.")
        else:
            logger.info(f"[UPDATER] {len(new_cams_info)} new cameras are found.")

            new_cam_ids = [cam[0] for cam in new_cams_info]
            logger.info(f"[UPDATER] New camera IDs: {', '.join(map(str, new_cam_ids))}\n")

            logger.info(f"[UPDATER] Initializing clustering...")
            
            # Cluster the cameras based on their coordinates (DBSCAN)
            clustered_cams_coordinate = cluster(meters, all_cams_coordinate)

            # Insert new camera records into the database
            add_camRecord(new_cams_info)
            logger.info(f"[UPDATER] Added {len(new_cams_info)} new cameras to the database.")

            # Update the camera clusters in the database
            update_camCluster(clustered_cams_coordinate)
            logger.info(f"[UPDATER] Updated camera clusters in the database.\n")

        logger.info(f"[UPDATER] {len(cctv_list)} cameras are online out of {len(all_cams_coordinate)}")
        logger.info(f"[UPDATER] {len(all_cams_coordinate) - len(cctv_list)} cameras are offline\n")
        logger.info(f"[UPDATER] Starting scraping!\n")
        return cctv_list

    else:
        logger.warning("[UPDATER] Skipping camera update due to failure in retrieving the camera list from BMA Traffic.")
        logger.warning("[UPDATER] Attempting to retrieve CCTV IDs from the database.")
        cctv_list = retrieve_onlineCam()
        if not cctv_list:
            logger.warning("[UPDATER] Failed to retrieve CCTV IDs from the database.")
            return cctv_list
        logger.info(f"[UPDATER] Scraping process initiated for {len(cctv_list)} cameras.")
        return cctv_list
