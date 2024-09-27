import re
from typing import List, Dict, Any, Tuple, Union
from log_config import logger
from collections import defaultdict

BASE_URL = "http://www.bmatraffic.com"

def sort_key(item):
    # Split the string into parts with numeric and non-numeric components
    return [int(part) if part.isdigit() else part.lower() for part in re.split('([0-9]+)', str(item))]

def readable_time(total_seconds: int) -> str:
    units = [
        (3600, "hour"),
        (60, "minute"),
        (1, "second")
    ]
    parts = []

    for divisor, unit in units:
        value, total_seconds = divmod(total_seconds, divisor)
        if value:
            parts.append(f"{value} {unit}{'s' if value > 1 else ''}")

    return " and ".join(parts) if parts else "0 seconds"

def create_cctv_status_dict(cctv_list: List[str], status: bool) -> Dict[str, bool]:
    return dict.fromkeys(cctv_list, status)

def select_non_empty(*items: Tuple[Any, str], item_description: str = "item") -> Tuple[Any, str]:
    for value, name in items:
        if value:
            logger.info(f"[SELECTOR] Using {name} {item_description} of type {type(value)}")
            return value, name
    
    logger.error(f"[SELECTOR] All {len(items)} {item_description}s are empty.")
    return None, None

def detect_cctv_status(all_cctv_ids, *args):
    offline_cctvs = set()
    online_cctvs = set()

    # Convert all_cctv_ids to a set for faster lookup
    all_cctv_ids_set = set(all_cctv_ids)

    for cctv_list in args:
        for cctv in cctv_list:
            cam_id = cctv[0]  # Assuming Cam_ID is always the first element
            stream_method = cctv[4]  # Assuming Stream_Method is always the fifth element
            stream_link_1 = cctv[5]  # Assuming Stream_Link_1 is always the sixth element

            if cam_id not in all_cctv_ids_set or stream_method == "UNKNOWN" or stream_link_1 == "":
                offline_cctvs.add(cam_id)
            else:
                online_cctvs.add(cam_id)

    # Remove any CCTVs that are in both sets (should not happen, but just in case)
    online_cctvs -= offline_cctvs

    offline_cctvs = sorted(list(offline_cctvs), key=sort_key)
    online_cctvs = sorted(list(online_cctvs), key=sort_key)

    return offline_cctvs, online_cctvs