import re
import ast
import requests
import time
from typing import List, Tuple, Union, Literal, Dict

from utils.database import retrieve_data, update_data, insert_data, update_pair_data
from utils.log_config import logger
from utils.utils import BASE_URL, SortingUtils, ClusteringUtils

CamInfo = Tuple[str, Union[str, None], Union[str, None], Union[str, None], Union[str, None], Union[str, None], Union[float, None], Union[float, None], Union[str, None], Union[str, None]]
CamCoordinate = Tuple[str, float, float]

def retrieve_camInfo_BMA(url: str = BASE_URL, max_retries: int = 5, delay: int = 5, timeout: int = 120) -> Union[List[CamInfo], Literal[False]]:
    logger.info(f"[UPDATER] Getting camera list from {url}")
    
    def fetch_data():
        for _ in range(max_retries):
            try:
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logger.warning(f"[UPDATER] Error retrieving camera list: {e}. Retrying...")
                time.sleep(delay)
        return None

    data = fetch_data()
    if not data:
        logger.error(f"[UPDATER] Failed to retrieve camera list after {max_retries} retries.")
        return False

    match = re.search(r"var locations = (\[.*?\]);", data, re.DOTALL)
    if not match:
        logger.error("[UPDATER] Error parsing camera list.")
        return False

    try:
        json_data = ast.literal_eval(match.group(1))
    except (SyntaxError, ValueError) as e:
        logger.error(f"[UPDATER] Error parsing JSON data: {e}")
        return False

    processed_data = []
    for item in json_data:
        code_match = re.match(r'^[A-Z0-9\-]+', item[1])
        code = code_match.group(0) if code_match else None
        cam_name = item[1][len(code):].strip() if code else item[1]
        
        processed_item = (item[0], code, cam_name, *[i or None for i in item[2:9]])
        processed_data.append(processed_item)

    logger.info("[UPDATER] Successfully retrieved camera list.")
    return processed_data

def filter_new_and_all_cams(online_cam_info: Tuple[CamInfo], db_cam_coordinate: List[CamCoordinate]) -> Tuple[Tuple[CamInfo], Tuple[CamCoordinate]]:
    db_cam_ids = {str(cam[0]) for cam in db_cam_coordinate}
    new_cam_info = []
    all_cams_coordinate = set(db_cam_coordinate)

    for cam in online_cam_info:
        cam_id = str(cam[0])
        if cam_id not in db_cam_ids:
            new_cam_info.append(cam)
            all_cams_coordinate.add((cam_id, cam[6], cam[7]))

    return tuple(new_cam_info), tuple(all_cams_coordinate)

def update_cctv_database(meters: int) -> Tuple[List[str], List[str]]:
    onlineCamInfo = retrieve_camInfo_BMA()
    dbCamCoordinate = retrieve_data('cctv_locations_preprocessing', ('cam_id', 'latitude', 'longitude'))
    cctv_list_all_db = [cam_id for cam_id, _, _ in dbCamCoordinate]

    if not onlineCamInfo:
        logger.warning("[UPDATER] Failed to retrieve camera list from BMA Traffic. Falling back to database.")
        cctv_list_online_db = retrieve_data('cctv_locations_preprocessing', ('Cam_ID',), ('is_online',), (True,))
        return cctv_list_online_db, cctv_list_all_db

    cctv_list_bma = sorted([str(t[0]) for t in onlineCamInfo], key=SortingUtils.sort_key)
    new_cams_info, all_cams_coordinate = filter_new_and_all_cams(onlineCamInfo, dbCamCoordinate)

    if not new_cams_info:
        logger.info(f"[UPDATER] {len(new_cams_info)} new cameras found: {(cam[0] for cam in new_cams_info)}")
        logger.info("[UPDATER] Initializing clustering...")
        
        clustered_cams_coordinate = ClusteringUtils.cluster(meters, all_cams_coordinate)
        
        insert_data('cctv_locations_preprocessing',
                    ('cam_id', 'cam_code', 'cam_name', 'cam_name_e', 'cam_location', 'cam_direction', 'latitude', 'longitude', 'ip', 'icon'),
                    new_cams_info
        )

        groups = [coord[1] for coord in clustered_cams_coordinate]
        cam_ids = [coord[0] for coord in clustered_cams_coordinate]

        update_pair_data(
            table="cctv_locations_preprocessing",
            column_to_update="cam_group",
            data_to_update=groups,
            column_to_check_condition="cam_id",
            data_to_check_condition=cam_ids
        )

        logger.info(f"[UPDATER] Added {len(new_cams_info)} new cameras and updated clusters in the database.")
    else:
        logger.info("[UPDATER] No new cameras found.")

    online_count = len(cctv_list_bma)
    total_count = len(all_cams_coordinate)
    logger.info(f"[UPDATER] {online_count} cameras are online out of {total_count}")
    logger.info(f"[UPDATER] {total_count - online_count} cameras are offline")
    logger.info("[UPDATER] Note: Online status doesn't guarantee operational status. Further checks will be initiated.")

    return cctv_list_bma, cctv_list_all_db