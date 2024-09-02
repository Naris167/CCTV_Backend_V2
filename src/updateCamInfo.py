import psycopg2
import re
import ast
import requests
import os
import json
import sys
import time
from dotenv import load_dotenv
import threading
from threading import Semaphore
import logging
from datetime import datetime
import numpy as np
from sklearn.cluster import DBSCAN
from readerwriterlock import rwlock
from decimal import Decimal, getcontext

BASE_URL = "http://www.bmatraffic.com"
CCTV_LIST = None
cctv_sessions = {}  # Stores CCTV ID and session ID pairs
cctv_fail = []  # Stores CCTV ID that are failed to prepare

# Locks for thread safety
cctv_sessions_lock = rwlock.RWLockFair()
cctv_fail_lock = rwlock.RWLockFair()

'''
1. Get the cctv list from BMATraffic (return a list of tuple)
2. Get the cctv list (ID and coordinate) from DB
3. Check for duplicate
4. Apply DBSCAN 
5. Insert new data into DB
6. Return the list of online cam
'''


# Logging configuration
def log_setup():
    # Define the directory and log file path
    log_directory = "./logs"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"{log_directory}/updateCamInfo_{timestamp}.log"

    # Check if the directory exists, if not, create it
    if not os.path.exists(log_directory):
        os.makedirs(log_directory, exist_ok=True)

    # Setup logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )

    logging.info("[MAIN] Logging setup completed!")


def save_cctv_sessions_to_file(cctv_sessions):
    # Define the directory and file path
    directory = "./cctvSessionTemp"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{directory}/cctv_sessions_{timestamp}.json"

    # Check if the directory exists; if not, create it
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    # Write the dictionary to a JSON file
    with open(filename, "w") as json_file:
        json.dump(cctv_sessions, json_file, indent=4)
    
    logging.info(f"[INFO] JSON data has been written to {filename}")


'''
THIS IS DATABASE CONNECTION
'''


load_dotenv('.env.prod')

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )

def retrieve_camLocation():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Query to retrieve Cam_ID, Latitude, and Longitude
        query = "SELECT Cam_ID, Latitude, Longitude FROM cctv_locations_preprocessing"

        # Execute the query
        cur.execute(query)

        # Fetch all results
        cam_locations = cur.fetchall()  # This will return a list of tuples

        # Close the cursor and connection
        cur.close()
        conn.close()

        return cam_locations
    
    except Exception as e:
        logging.error(f"[DATABASE] Error: {e}")
        return []

def add_camRecord(camera_data):
    #Accept list of tuple
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Query to check if the camera already exists in the database
        check_query = "SELECT 1 FROM cctv_locations_preprocessing WHERE Cam_ID = %s"
        insert_query = """
            INSERT INTO cctv_locations_preprocessing (
                Cam_ID, Cam_Code, Cam_Name, Cam_Name_e, Cam_Location, 
                Cam_Direction, Latitude, Longitude, IP, Icon
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        new_cameras_count = 0

        for cam in camera_data:
            cam_id, code, cam_name, cam_name_e, cam_location, cam_direction, latitude, longitude, ip, icon = cam

            # Check if the camera already exists
            cur.execute(check_query, (cam_id,))
            exists = cur.fetchone()
            
            if not exists:
                # Insert the new camera data into the database
                cur.execute(insert_query, (cam_id, code, cam_name, cam_name_e, cam_location, cam_direction, latitude, longitude, ip, icon))
                new_cameras_count += 1
                
        # Commit the transaction
        conn.commit()

        # Close the cursor and connection
        cur.close()
        conn.close()

        if new_cameras_count > 0:
            logging.info(f"[DATABASE] {new_cameras_count} new cameras were added to the database.\n")
        else:
            logging.info("[DATABASE] No new cameras were added to the database.\n")

    except Exception as e:
        logging.error(f"[DATABASE] An error occurred: {e}\n")

def update_camCluster(clustered_data):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # SQL command to update the Cam_Group based on Cam_ID
        update_query = "UPDATE cctv_locations_preprocessing SET Cam_Group = %s WHERE Cam_ID = %s"

        # Iterate over each camera in the clustered_data
        for cam_id, label, lat, lon in clustered_data:
            cur.execute(update_query, (str(label), int(cam_id)))
            
            # Check if the update was successful or not
            if cur.rowcount == 0:
                logging.info(f"[DATABASE] Cannot update cluster for Cam[{cam_id}]. Record not found in the database.")

        # Commit the changes to the database
        conn.commit()

    except Exception as e:
        logging.error(f"[DATABASE] Error: {e}")
    finally:
        # Close the cursor and connection
        cur.close()
        conn.close()

def update_isCamOnline(cctv_ids):
    try:
        conn = get_db_connection()  # Assuming get_db_connection() returns a connection object
        cur = conn.cursor()

        # First, update all cctvs to is_online = False
        cur.execute("""
            UPDATE cctv_locations_preprocessing
            SET is_online = FALSE
        """)

        # Then, update the cctvs in the provided list to is_online = True
        if cctv_ids:
            # Cast the array elements to integers
            cur.execute("""
                UPDATE cctv_locations_preprocessing
                SET is_online = TRUE
                WHERE cam_id = ANY(%s::int[])
            """, (cctv_ids,))

        # Commit the changes to the database
        logging.info(f"[DATABASE] Updated is_online to TRUE for CCTV IDs: {cctv_ids}")
        conn.commit()

    except Exception as e:
        logging.error(f"[DATABASE] Error: {e}")
    finally:
        # Close the cursor and connection
        cur.close()
        conn.close()


'''
THIS IS CCTV CLUSTERING
'''


# Set the precision for Decimal calculations
getcontext().prec = 100  # Set precision high enough for required accuracy

def meters_to_degrees(meters):
    """
    This fomular is calculated using brute force method
    It convert a distance in meters to degrees using a known conversion factor.

    This calculation maintains high precision using the Decimal class.
    The precision is +- 1-5 meter in the distance less than 2236 meters
    
    position 1 = 13.769741049467855, 100.57298223507024
    position 2 = 13.789905618799368, 100.57434272643398
    distance in degree = 0.00035269290326066755967941712679447618938866071403026580810546874999
    distance in km (approx) (calculate from given position) = 2235.799051227861
    """

    # Define the numbers as Decimal types
    numerator = Decimal('2235.799051227861')
    denominator = Decimal('0.00035269290326066755967941712679447618938866071403026580810546874999')

    # Find the ratio of the actual distance in meters to the eps value in degrees
    distance_per_degree = numerator / denominator

    # Convert meters to degrees
    degrees = Decimal(meters) / distance_per_degree

    return degrees


def cluster(meters, all_cams_coordinate):
    logging.info(f"[CLUSTER] Distance set to {meters} meters")

    # Extract Cam_IDs and coordinates (Latitude, Longitude)
    cam_ids = [cam[0] for cam in all_cams_coordinate]

    coordinates = np.array([(float(cam[1]), float(cam[2])) for cam in all_cams_coordinate], dtype=float)

    # Perform clustering using DBSCAN
    logging.info("[CLUSTER] Starting clustering...")
    dbscan = DBSCAN(eps=float(meters_to_degrees(meters)), min_samples=1, metric='haversine')
    dbscan.fit(np.radians(coordinates))  # Convert degrees to radians for haversine metric

    # Extract cluster labels
    labels = dbscan.labels_

    # Combine Cam_ID, cluster group, latitude, and longitude into a list of tuples
    clustered_data = [(cam_id, int(label), float(lat), float(lon)) for cam_id, label, (lat, lon) in zip(cam_ids, labels, coordinates)]

    logging.info("[CLUSTER] Clustering completed!\n")
    return clustered_data


'''
THIS IS CCTV UPDATE
'''


# Get online CCTV list from BMA Traffic
def retrieve_camInfo_BMA(url = BASE_URL):
    #Return list of tuple
    logging.info(f"[UPDATER] Getting camera list from {url}")
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
        
        logging.info("[UPDATER] Successfully getting camera list.")
        return processed_data
    else:
        logging.info("[UPDATER] Error getting camera list.")
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
    global CCTV_LIST
    CCTV_LIST = sorted([t[0] for t in onlineCamInfo], key=int)
    new_cams_info, all_cams_coordinate = filter_new_and_all_cams(onlineCamInfo, dbCamCoordinate)

    update_isCamOnline(CCTV_LIST)

    # Check if there are any new cameras
    # In case there are no new cctv, remove `not` here to manually run the script
    if not new_cams_info:
        logging.info("[UPDATER] No new cameras found.")
    else:
        logging.info(f"[UPDATER] {len(new_cams_info)} cameras are found.")

        new_cam_ids = [cam[0] for cam in new_cams_info]
        logging.info(f"[UPDATER] New camera IDs: {', '.join(map(str, new_cam_ids))}\n")

        logging.info(f"[UPDATER] Initializing clustering...")
        
        # Cluster the cameras based on their coordinates (DBSCAN)
        clustered_cams_coordinate = cluster(meters, all_cams_coordinate)

        # Insert new camera records into the database
        add_camRecord(new_cams_info)
        logging.info(f"[UPDATER] Added {len(new_cams_info)} new cameras to the database.")

        # Update the camera clusters in the database
        update_camCluster(clustered_cams_coordinate)
        logging.info(f"[UPDATER] Updated camera clusters in the database.\n")

    logging.info(f"[UPDATER] {len(CCTV_LIST)} cameras are online out of {len(all_cams_coordinate)}")
    logging.info(f"[UPDATER] {len(all_cams_coordinate) - len(CCTV_LIST)} cameras are offline\n")
    logging.info(f"[UPDATER] Starting scraping!\n")

    # return online_camera_ids
    # print(online_camera_ids)
#     for element in online_camera_ids:
#         print(f'Element: {element}, Type: {type(element)}')


'''
PREPARING CCTV SESSIONS
'''


# Function to get a session ID for a specific camera
def get_cctv_session_id(url: str, camera_id: int, max_retries=3, delay=5):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            cookie = response.headers.get('Set-Cookie', '')

            # Check if cookie is present
            if cookie:
                session_id = cookie.split("=")[1].split(";")[0]
                logging.info(f"[{camera_id}] Obtained session ID: {session_id}")
                return session_id
            else:
                logging.warning(f"[{camera_id}] No session cookie found. Retry {retries + 1}/{max_retries}...")
        except requests.RequestException as e:
            logging.error(f"[{camera_id}] Error getting session ID: {e}. Retry {retries + 1}/{max_retries}...")
        
        retries += 1
        time.sleep(delay)

    logging.error(f"[{camera_id}] Failed to obtain session ID after {max_retries} retries.")
    return None

# Function to play video for a camera session
def play_video(camera_id: int, session_id: str, max_retries=3, delay=5):
    retries = 0
    while retries < max_retries:
        try:
            url = f"{BASE_URL}/PlayVideo.aspx?ID={camera_id}"
            headers = {
                'Referer': f'{BASE_URL}/index.aspx',
                'Cookie': f'ASP.NET_SessionId={session_id};',
                'Priority': 'u=4'
            }
            response = requests.get(url, headers=headers, timeout=60)  # Added timeout
            response.raise_for_status()
            logging.info(f"[{camera_id}] Playing video for session ID: {session_id}")
            return True  # Exit function if successful
        except requests.RequestException as e:
            retries += 1
            logging.error(f"[{camera_id}] Error playing video: {e}. Retry {retries}/{max_retries}...")
            time.sleep(delay)  # Wait before retrying
    logging.error(f"[{camera_id}] Failed to play video after {max_retries} retries.")
    return None


# Function to refresh the session ID for a camera
def refresh_session_id(camera_id):
    # logging.info(f"Preparing session for camera {camera_id}")
    session_id = get_cctv_session_id(BASE_URL, camera_id)
    if session_id:
        success = play_video(camera_id, session_id)
        if success:
            with cctv_sessions_lock.gen_wlock():
                cctv_sessions[camera_id] = session_id
            # logging.info(f"Session ready for camera {camera_id}")
        else:
            with cctv_fail_lock.gen_wlock:
                cctv_fail.append(camera_id)
            logging.warning(f"Added failed camera (play video) to list: {camera_id}")
    else:
        with cctv_fail_lock.gen_wlock:
            cctv_fail.append(camera_id)
        logging.warning(f"Added failed camera (session ID) to list: {camera_id}")


# Function to prepare session for a camera
def prepare_session(camera_id, semaphore):
    logging.info(f"[PREPARE] Preparing session for camera {camera_id}")
    try:
        refresh_session_id(camera_id)
        logging.info(f"[PREPARE] Session ready for camera {camera_id}")
    finally:
        semaphore.release()



# Function to manage workers for session preparation
def prepare_session_workers():
    threads = []
    max_workers = 80
    semaphore = Semaphore(max_workers)

    logging.info("[INFO] Initializing all session IDs.")
    for camera_id in CCTV_LIST:
        semaphore.acquire()
        thread = threading.Thread(target=prepare_session, args=(camera_id, semaphore))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    if len(sys.argv) > 1:  # Check if an argument is provided
        param = int(sys.argv[1])  # Get the parameter from command-line arguments
    else:
        try:
            param = int(input("Please enter the parameter number: "))
        except ValueError:
            print("Invalid input. Please enter a valid number.", file=sys.stderr)
            sys.exit(1)

    log_setup()
    startUpdate(param)
    prepare_session_workers()

    # Alternatively, if you want to keep prepare_session_workers in a separate thread,
    # make sure to join it so the script waits for it to finish:
    # worker_thread = threading.Thread(target=prepare_session_workers)
    # worker_thread.start()
    # worker_thread.join()
    
    # Sort the `cctv_sessions` dictionary by keys (camera IDs) in ascending order
    sorted_cctv_sessions = dict(sorted(cctv_sessions.items(), key=lambda item: int(item[0])))


    scraped_cctv = len(CCTV_LIST)
    processed_cctv = len(sorted_cctv_sessions)
    fail_to_processed_cctv = len(cctv_fail)

    logging.info(f"[INFO] Total number of scraped CCTVs: {scraped_cctv}")
    logging.info(f"[INFO] Successfully processed {processed_cctv} CCTVs out of {processed_cctv + fail_to_processed_cctv}.")

    if cctv_fail:
        logging.info(f"[INFO] The following CCTV IDs failed to prepare and will not be available: {cctv_fail}")
        update_isCamOnline(cctv_fail)

    save_cctv_sessions_to_file(sorted_cctv_sessions)

    logging.info("[INFO] All session IDs have been successfully prepared and saved.\n\n")
