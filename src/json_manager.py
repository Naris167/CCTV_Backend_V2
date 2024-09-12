import os
import json
from datetime import datetime
from typing import Literal, Tuple, Dict

from log_config import logger


jsonDirectory = './cctvSessionTemp/'


def load_latest_cctv_sessions_from_json() -> Tuple[str, str, Dict[str, str], str] | Literal[False]:
    loaded_JSON_latestRefreshTime = ""
    loaded_JSON_latestUpdateTime = ""
    loaded_JSON_cctvSessions = {}

    # Check if the directory exists
    if not os.path.exists(jsonDirectory):
        logger.error(f"[JSON] Directory does not exist: {jsonDirectory}")
        return False

    # Get a list of all JSON files in the directory
    json_files = [f for f in os.listdir(jsonDirectory) if f.endswith('.json')]
    if not json_files:
        logger.error(f"[JSON] No JSON files found in directory: {jsonDirectory}")
        return False

    # Sort files by modified time to get the latest one
    json_files = sorted(json_files, key=lambda x: os.path.getmtime(os.path.join(jsonDirectory, x)), reverse=True)
    latest_file = json_files[0]
    latest_file_path = os.path.join(jsonDirectory, latest_file)

    try:
        # Load the data from the latest JSON file
        with open(latest_file_path, 'r') as json_file:
            data = json.load(json_file)

        # Extract the required values from the JSON
        loaded_JSON_latestRefreshTime = data.get("latestRefreshTime", "")
        loaded_JSON_latestUpdateTime = data.get("latestUpdateTime", "")
        loaded_JSON_cctvSessions = data.get("cctvSessions", {})

        logger.info(f"[JSON] Successfully loaded JSON data from file: {latest_file}")

        # Return the loaded values and the filename
        return loaded_JSON_latestRefreshTime, loaded_JSON_latestUpdateTime, loaded_JSON_cctvSessions

    except (json.JSONDecodeError, FileNotFoundError, OSError) as e:
        logger.error(f"[JSON] Error loading the JSON file {latest_file}: {e}")
        return False









# Example usage
# result = load_latest_cctv_sessions_from_json()
# if result:
#     loaded_JSON_latestRefreshTime, loaded_JSON_latestUpdateTime, loaded_JSON_cctvSessions = result
#     print(f"Latest Refresh Time: {loaded_JSON_latestRefreshTime}")
#     print(f"Latest Update Time: {loaded_JSON_latestUpdateTime}")
#     print(f"CCTV Sessions: {loaded_JSON_cctvSessions}")
# else:
#     print("No JSON file found or failed to load.")


def save_alive_session_to_file(cctv_sessions: Dict[str, str], latestRefreshTime: str, latest_update_time: str) -> None:
    # Define the directory and file path
    directory = "./cctvSessionTemp"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{directory}/cctv_sessions_{timestamp}.json"

    # Check if the directory exists; if not, create it
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    # Prepare the data structure for the JSON file
    data_to_save = {
        "latestRefreshTime": latestRefreshTime,
        "latestUpdateTime": latest_update_time,
        "cctvSessions": cctv_sessions
    }

    # Write the data to a JSON file
    with open(filename, "w") as json_file:
        json.dump(data_to_save, json_file, indent=4)

    logger.info(f"[JSON] JSON data has been written to {filename}")
