import psycopg2
import re
import numpy as np
from PIL import Image
from datetime import datetime
import io
from typing import List, Dict, Any, Tuple, Union
from utils.log_config import logger
from collections import defaultdict


BASE_URL = "http://www.bmatraffic.com"

def image_to_binary(image_input):
    if isinstance(image_input, bytes):
        return psycopg2.Binary(image_input)
    elif isinstance(image_input, str):
        with open(image_input, 'rb') as file:
            return psycopg2.Binary(file.read())
    else:
        raise ValueError("Invalid input type for image_to_binary function.")

def binary_to_image(binary_data, output_path):
    """Save binary data as an image file."""
    try:
        with open(output_path, 'wb') as file:
            file.write(binary_data)
        print(f"Image saved successfully: {output_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied when writing to {output_path}. Check your write permissions.")
    except IOError as e:
        raise IOError(f"Error writing image file: {str(e)}")

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

def detect_movement(image_list: List[bytes], threshold_percentage: int = 1, min_changed_pixels: int = 100) -> bool:
    """
    Detect movement in a list of CCTV images.
    
    Args:
    image_list (list): List of image data as bytes
    threshold_percentage (float): Percentage of pixels that need to change to detect movement
    min_changed_pixels (int): Minimum number of pixels that need to change to detect movement
    
    Returns:
    bool: True if movement is detected, False otherwise
    """
    if len(image_list) < 2:
        return False
    
    # Convert bytes to numpy arrays
    images = [np.array(Image.open(io.BytesIO(img))) for img in image_list]
    
    # Convert images to grayscale
    gray_images = [img.mean(axis=2).astype(np.uint8) for img in images]
    
    # Get image dimensions
    height, width = gray_images[0].shape
    total_pixels = height * width
    
    # Calculate the number of pixels that need to change based on the percentage
    pixels_to_change = max(int(total_pixels * threshold_percentage / 100), min_changed_pixels)
    
    # Compare consecutive images
    for i in range(1, len(gray_images)):
        diff = np.abs(gray_images[i].astype(np.int16) - gray_images[i-1].astype(np.int16))
        changed_pixels = np.sum(diff > 10)  # Count pixels with difference greater than 10
        if changed_pixels > pixels_to_change:
            return True
    
    return False

def check_cctv_integrity(cctv_working: Dict[str, str], cctv_unresponsive: Dict[str, str], cctv_fail: List[str]) -> Tuple[bool, List[str]]:
    integrity_issues = []
    
    def get_item_info(item: str, source: str, item_type: str) -> str:
        if source == 'cctv_fail':
            count = cctv_fail.count(item)
            return f"is an item in `{source}` list (found {count} occurrence{'s' if count > 1 else ''})"
        else:
            source_dict = cctv_working if source == 'cctv_working' else cctv_unresponsive
            if item_type == 'key':
                return f"is a key in `{source}` dictionary (key: '{item}', value: '{source_dict[item]}')"
            else:  # value
                keys = [k for k, v in source_dict.items() if v == item]
                info = ", ".join([f"(key: '{k}', value: '{item}')" for k in keys])
                return f"is a value in `{source}` dictionary {info}"

    all_items = defaultdict(set)
    for source, items in [('cctv_working', cctv_working), ('cctv_unresponsive', cctv_unresponsive), ('cctv_fail', cctv_fail)]:
        if isinstance(items, dict):
            for k, v in items.items():
                all_items[k].add((source, 'key'))
                all_items[v].add((source, 'value'))
        else:  # list
            for item in items:
                all_items[item].add((source, 'item'))

    for item, sources in all_items.items():
        if len(sources) > 1 or (len(sources) == 1 and ('cctv_fail', 'item') in sources and cctv_fail.count(item) > 1):
            descriptions = [get_item_info(item, source, item_type) for source, item_type in sources]
            
            # Check for internal duplications
            for source in ['cctv_working', 'cctv_unresponsive']:
                if sum(1 for s, _ in sources if s == source) > 1:
                    descriptions.insert(0, f"is duplicated within `{source}` dictionary")
            
            main_description = descriptions.pop(0)
            issue = f"Found '{item}' which {main_description}"
            if descriptions:
                issue += " and is also found in the following:"
                for i, desc in enumerate(descriptions):
                    prefix = "└─ " if i == len(descriptions) - 1 else "├─ "
                    issue += f"\n{prefix}{desc}"
            
            integrity_issues.append(issue)

    for key, value in cctv_working.items():
        if key in cctv_unresponsive and cctv_unresponsive[key] == value:
            integrity_issues.append(f"Same key-value pair found in both dictionaries: key '{key}', value '{value}'")

    return len(integrity_issues) == 0, integrity_issues


def select_images_and_datetimes(
    images: List[bytes],
    datetimes: List[datetime],
    num_select: int
) -> Tuple[List[bytes], List[datetime]]:
    if not 1 <= num_select <= len(images) or len(images) != len(datetimes):
        raise ValueError("Invalid input: Check number of selections or list lengths.")

    if num_select == 1:
        mid = len(images) // 2
        return [images[mid]], [datetimes[mid]]
    
    selected_images = []
    selected_datetimes = []
    step = (len(images) - 1) / (num_select - 1)
    
    for i in range(num_select):
        index = int(i * step)
        selected_images.append(images[index])
        selected_datetimes.append(datetimes[index])
    
    return selected_images, selected_datetimes