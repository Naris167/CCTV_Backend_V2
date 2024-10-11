import os
import json
from datetime import datetime
from typing import Tuple, Dict, Optional
from pathlib import Path
from script_config import config
from utils.log_config import isDirExist, logger

JSON_DIRECTORY = Path(config['json_path'])

def load_latest_cctv_sessions_from_json() -> Optional[Tuple[str, str, Dict[str, str]]]:
    try:
        if not JSON_DIRECTORY.exists():
            logger.error(f"[JSON] Directory does not exist: {JSON_DIRECTORY}")
            return None

        json_files = sorted(JSON_DIRECTORY.glob('*.json'), key=os.path.getmtime, reverse=True)
        if not json_files:
            logger.error(f"[JSON] No JSON files found in directory: {JSON_DIRECTORY}")
            return None

        latest_file = json_files[0]
        with latest_file.open('r') as json_file:
            data = json.load(json_file)

        logger.info(f"[JSON] Successfully loaded JSON data from file: {latest_file.name}")
        return (
            data.get("latestRefreshTime", ""),
            data.get("latestUpdateTime", ""),
            data.get("cctvSessions", {})
        )

    except (json.JSONDecodeError, FileNotFoundError, OSError) as e:
        logger.error(f"[JSON] Error loading the JSON file: {e}")
        return None

def save_alive_session_to_file(cctv_sessions: Dict[str, str], latest_refresh_time: str, latest_update_time: str) -> None:
    try:
        isDirExist(JSON_DIRECTORY)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = JSON_DIRECTORY / f"cctv_sessions_{timestamp}.json"

        data_to_save = {
            "latestRefreshTime": latest_refresh_time,
            "latestUpdateTime": latest_update_time,
            "cctvSessions": cctv_sessions
        }

        with filename.open("w") as json_file:
            json.dump(data_to_save, json_file, indent=4)

        logger.info(f"[JSON] JSON data has been written to {filename}")
    except Exception as e:
        logger.error(f"Error: {e}")
    


# Example usage
# result = load_latest_cctv_sessions_from_json()
# if result:
#     loaded_JSON_latestRefreshTime, loaded_JSON_latestUpdateTime, loaded_JSON_cctvSessions = result
#     print(f"Latest Refresh Time: {loaded_JSON_latestRefreshTime}")
#     print(f"Latest Update Time: {loaded_JSON_latestUpdateTime}")
#     print(f"CCTV Sessions: {loaded_JSON_cctvSessions}")
# else:
#     print("No JSON file found or failed to load.")