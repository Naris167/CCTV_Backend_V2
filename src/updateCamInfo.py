from Database import retrieve_camLocation, add_camRecord, update_camCluster
import re
import ast
import requests
from GeoCluster import cluster

BASE_URL = "http://www.bmatraffic.com"

'''
1. Get the cctv list from BMATraffic (return a list of tuple)
2. Get the cctv list (ID and coordinate) from DB
3. Check for duplicate
4. Apply DBSCAN 
5. Insert new data into DB
6. Return the list of online cam
'''

# Get online CCTV list from BMA Traffic

def retrieve_camInfo_BMA(url = BASE_URL):
    #Return list of tuple
    print(f"\n[UPDATER] Getting camera list from {url}")
    response = requests.get(url)
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
                item[0],       # ID
                code or None,          # Code
                cam_name or None,      # Cam_Name
                item[2] or None,       # Cam_Name_e
                item[3] or None,       # Cam_Location
                item[4] or None,       # Cam_Direction
                item[5] or None,       # Latitude
                item[6] or None,       # Longitude
                item[7] or None,       # IP
                item[8] or None        # Icon
            )
            processed_data.append(processed_item)
        
        print("[UPDATER] Successfully getting camera list.")
        return processed_data
    else:
        print("[UPDATER] Error getting camera list.")
        return

# Compare both online_cam and db_cam.
# Take any duplicate record out from online_cam.
# Return a list of tuple of new CCTV only
# Return a list of tuple of all CCTV (ID, Latitude, and Longitude)

def filter_new_and_all_cams(online_cam_info, db_cam_coordinate):
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

def startUpdate(meters):
    onlineCamInfo = retrieve_camInfo_BMA()
    dbCamCoordinate = retrieve_camLocation()

    # Get new camera information and all camera coordinates
    new_cams_info, all_cams_coordinate = filter_new_and_all_cams(onlineCamInfo, dbCamCoordinate)

    # Check if there are any new cameras
    if not new_cams_info:
        print("[UPDATER] No new cameras found.")
    else:
        print(f"[UPDATER] {len(new_cams_info)} cameras are found.")

        new_cam_ids = [cam[0] for cam in new_cams_info]
        print(f"[UPDATER] New camera IDs: {', '.join(map(str, new_cam_ids))}\n")

        print(f"[UPDATER] Initializing clustering...")
        
        # Cluster the cameras based on their coordinates (DBSCAN)
        clustered_cams_coordinate = cluster(meters, all_cams_coordinate)

        # Insert new camera records into the database
        add_camRecord(new_cams_info)
        print(f"[UPDATER] Added {len(new_cams_info)} new cameras to the database.")

        # Update the camera clusters in the database
        update_camCluster(clustered_cams_coordinate)
        print(f"[UPDATER] Updated camera clusters in the database.\n")

    # Get only the online camera IDs from the info
    online_camera_ids = [t[0] for t in onlineCamInfo]

    print(f"[UPDATER] {len(online_camera_ids)} cameras are online out of {len(all_cams_coordinate)}")
    print(f"[UPDATER] {len(all_cams_coordinate) - len(online_camera_ids)} cameras are offline\n")
    print(f"[UPDATER] Starting scraping!\n")

    return online_camera_ids
    # print(online_camera_ids)
#     for element in online_camera_ids:
#         print(f'Element: {element}, Type: {type(element)}')

# startUpdate(170)