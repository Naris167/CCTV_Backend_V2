import re
from typing import List, Dict, Any, Tuple, Union
from utils.log_config import logger
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

def process_cctv_names(tuple_list):
    def process_name(name):
        # Replace en dash with hyphen
        name = name.replace("–", "-")

        # Rule 5: If all characters are English, return as is
        if re.match(r'^[a-zA-Z\s]+$', name):
            return name

        # Rule 8 and 9: Remove parenthesis and content inside, along with any numbers and dashes that follow
        name = re.sub(r'\([^)]*\)\s*(?:\d+\s*-\s*)?', '', name)

        # Rule 10: Remove prefix like "CRM-014", "ATC4-03" with more flexible format
        name = re.sub(r'^[A-Za-z]+\d*-?\d+\s+', '', name)

        # Rule 6 and 7: Check if name starts with Thai character or number followed by space and Thai character
        if re.match(r'^[\u0E00-\u0E7F]|^\d+\s+[\u0E00-\u0E7F]', name):
            return name.strip()

        # If none of the rules match, return the original name
        return name.strip()

    # Process the second element of each tuple
    return [(t[0], process_name(t[1])) + t[2:] for t in tuple_list]