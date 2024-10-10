# import os
# import json
# from datetime import datetime
# import logging

# logger = logging.getLogger(__name__)

# def save_cctv_sessions_to_file(cctv_sessions, current_time, latest_update_time):
#     # Define the directory and file path
#     directory = "./cctvSessionTemp"
#     timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#     filename = f"{directory}/TEST_cctv_sessions_{timestamp}.json"

#     # Check if the directory exists; if not, create it
#     if not os.path.exists(directory):
#         os.makedirs(directory, exist_ok=True)

#     # Prepare the data structure for the JSON file
#     data_to_save = {
#         "latestRefreshTime": current_time,
#         "latestUpdateTime": latest_update_time,
#         "cctvSessions": cctv_sessions
#     }

#     # Write the data to a JSON file
#     with open(filename, "w") as json_file:
#         json.dump(data_to_save, json_file, indent=4)

#     logger.info(f"[INFO] JSON data has been written to {filename}")

# # Example usage
# current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# latest_update_time = "2024-09-09 12:00:00"  # Example latest update time
# cctv_sessions = {
#     "7": "jeneudbuvficqr2cqfoca2y3",
#     "11": "cogdw4lep5vqs2sylu55mj2z",
#     "39": "edfb251kapc1pni0odhy20t2",
#     "77": "ssardgtxweg52nhancr0ckrk",
#     "83": "cvx2f5ypvsjwns5glm3dbfpf",
#     "572": "nxsqxexk3u5j5ufjosyokaws"
# }

# save_cctv_sessions_to_file(cctv_sessions, current_time, latest_update_time)


import os
import json
from datetime import datetime

jsonDirectory = './cctvSessionTemp/'

def load_latest_cctv_sessions_from_json():
    # Check if the directory exists
    if not os.path.exists(jsonDirectory):
        return False

    # Get a list of all JSON files in the directory
    json_files = [f for f in os.listdir(jsonDirectory) if f.endswith('.json')]
    if not json_files:
        return False

    # Sort files by modified time to get the latest one
    json_files = sorted(json_files, key=lambda x: os.path.getmtime(os.path.join(jsonDirectory, x)), reverse=True)
    latest_file = os.path.join(jsonDirectory, json_files[0])

    try:
        # Load the data from the latest JSON file
        with open(latest_file, 'r') as json_file:
            data = json.load(json_file)

        # Extract the required values from the JSON
        loaded_JSON_latestRefreshTime = data.get("latestRefreshTime", "")
        loaded_JSON_latestUpdateTime = data.get("latestUpdateTime", "")
        loaded_JSON_cctvSessions = data.get("cctvSessions", {})

        # Return the loaded values
        return loaded_JSON_latestRefreshTime, loaded_JSON_latestUpdateTime, loaded_JSON_cctvSessions

    except (json.JSONDecodeError, FileNotFoundError, OSError) as e:
        print(f"Error loading the JSON file: {e}")
        return False

# Example usage
result = load_latest_cctv_sessions_from_json()
if result:
    loaded_JSON_latestRefreshTime, loaded_JSON_latestUpdateTime, loaded_JSON_cctvSessions = result
    print(f"Latest Refresh Time: {loaded_JSON_latestRefreshTime}")
    print(f"Latest Update Time: {loaded_JSON_latestUpdateTime}")
    print(f"CCTV Sessions: {loaded_JSON_cctvSessions}")
else:
    print("No JSON file found or failed to load.")
