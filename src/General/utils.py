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

