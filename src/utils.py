import re
from typing import List, Dict

BASE_URL = "http://www.bmatraffic.com"

def sort_key(item):
    # Split the string into parts with numeric and non-numeric components
    return [int(part) if part.isdigit() else part for part in re.split('([0-9]+)', item)]

def readableTime(total_seconds: int) -> str:
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        readable_time = f"{hours} hours, {minutes} minutes, and {seconds} seconds ago"
    elif minutes > 0:
        readable_time = f"{minutes} minutes and {seconds} seconds ago"
    else:
        readable_time = f"{seconds} seconds ago"
    
    return readable_time

def create_cctv_status_dict(cctv_list: List[str], status: bool) -> Dict[str, bool]:
    return {cctv_id: status for cctv_id in cctv_list}


