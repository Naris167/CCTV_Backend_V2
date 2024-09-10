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
from datetime import datetime, timedelta
import numpy as np
from sklearn.cluster import DBSCAN
from readerwriterlock import rwlock
from decimal import Decimal, getcontext

BASE_URL = "http://www.bmatraffic.com"
jsonDirectory = './cctvSessionTemp/'

# Locks for thread safety
alive_sessions_lock = rwlock.RWLockFair()
cctv_fail_lock = rwlock.RWLockFair()

# Define the logger globally
logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

'''
1. Get the cctv list from BMATraffic (return a list of tuple)
2. Get the cctv list (ID and coordinate) from DB
3. Check for duplicate
4. Apply DBSCAN 
5. Insert new data into DB
6. Return the list of online cam
'''

def sort_key(item):
    # Split the string into parts with numeric and non-numeric components
    return [int(part) if part.isdigit() else part for part in re.split('([0-9]+)', item)]

# Logging configuration
def log_setup():
    global logger  # Make sure to refer to the global logger
    
    # Define the directory and log file path
    log_directory = "./logs"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"{log_directory}/updateCamInfo_{timestamp}.log"

    # Check if the directory exists, if not, create it
    if not os.path.exists(log_directory):
        os.makedirs(log_directory, exist_ok=True)

    # Create handlers
    stdout_handler = logging.StreamHandler(sys.stdout)
    stderr_handler = logging.StreamHandler(sys.stderr)
    file_handler = logging.FileHandler(log_filename)

    # Define custom filters for handlers
    class InfoFilter(logging.Filter):
        def filter(self, record):
            return record.levelno < logging.WARNING  # Only log below WARNING (INFO and below)

    class WarningErrorFilter(logging.Filter):
        def filter(self, record):
            return record.levelno >= logging.WARNING  # Only log WARNING and above

    # Set levels for handlers
    stdout_handler.setLevel(logging.DEBUG)  # All levels go to stdout but filtered
    stderr_handler.setLevel(logging.WARNING)  # WARNING and above go to stderr
    file_handler.setLevel(logging.DEBUG)  # All levels go to file

    # Assign filters to handlers
    stdout_handler.addFilter(InfoFilter())
    stderr_handler.addFilter(WarningErrorFilter())

    # Create formatters and add them to handlers
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    stdout_handler.setFormatter(formatter)
    stderr_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Clear existing handlers, if any, to prevent duplication
    if logger.hasHandlers():
        logger.handlers.clear()

    # Add handlers to the logger
    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)
    logger.addHandler(file_handler)

    # Avoid duplicate logs
    logger.propagate = False

    # Example log message to confirm setup
    logger.info("[MAIN] Logging setup completed!")

def initialize():
    if len(sys.argv) > 1:  # Check if an argument is provided
        param = int(sys.argv[1])  # Get the parameter from command-line arguments
    else:
        try:
            param = int(input("Please enter the parameter number: "))
        except ValueError:
            print("Invalid input. Please enter a valid number.", file=sys.stderr)
            sys.exit(1)
    log_setup()

    return param



def save_alive_session_to_file(cctv_sessions: dict, latestRefreshTime: str, latest_update_time: str):
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

    logger.info(f"[INFO] JSON data has been written to {filename}")


'''
THIS IS DATABASE CONNECTION
'''


load_dotenv('.env.local')

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
        sorted_cam_locations = sorted(cam_locations, key=lambda x: sort_key(x[0]))
        print("from database test")
        print(sorted_cam_locations)

        # Close the cursor and connection
        cur.close()
        conn.close()

        return sorted_cam_locations
    
    except Exception as e:
        logger.error(f"[DATABASE] Error retrieve_camLocation: {e}")
        return []

def retrieve_onlineCam():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Query to retrieve Cam_ID where is_online is TRUE
        query = "SELECT Cam_ID FROM cctv_locations_preprocessing WHERE is_online = TRUE"
        cur.execute(query)

        # Fetch all records from the result and return the list of Cam_ID
        cam_list = [str(row[0]) for row in cur.fetchall()]
        sorted_cam_list = sorted(cam_list, key=sort_key)

        # Close the cursor and connection
        cur.close()
        conn.close()

        return sorted_cam_list
    
    except Exception as e:
        logger.error(f"[DATABASE] Error retrieve_onlineCam: {e}")
        return []


def add_camRecord(camera_data: list):
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
            logger.info(f"[DATABASE] {new_cameras_count} new cameras were added to the database.\n")
        else:
            logger.info("[DATABASE] No new cameras were added to the database.\n")

    except Exception as e:
        logger.error(f"[DATABASE] An error occurred add_camRecord: {e}\n")

def update_camCluster(clustered_data: list):
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
                logger.info(f"[DATABASE] Cannot update cluster for Cam[{cam_id}]. Record not found in the database.")

        # Commit the changes to the database
        conn.commit()

    except Exception as e:
        logger.error(f"[DATABASE] Error update_camCluster: {e}")
    finally:
        # Close the cursor and connection
        cur.close()
        conn.close()

def update_isCamOnline(cctv_data):
    try:
        conn = get_db_connection()  # Assuming get_db_connection() returns a connection object
        cur = conn.cursor()

        if isinstance(cctv_data, dict):
            # Case 1: If cctv_data is a dictionary with CCTV IDs as keys and TRUE/FALSE as values
            for cam_id, is_online in cctv_data.items():
                is_online_value = 'TRUE' if is_online else 'FALSE'
                cur.execute("""
                    UPDATE cctv_locations_preprocessing
                    SET is_online = %s
                    WHERE cam_id = %s
                """, (is_online_value, cam_id))
                logger.info(f"[DATABASE] Updated is_online to {is_online_value} for CCTV ID: {cam_id}")

        elif isinstance(cctv_data, list):
            # Case 2: If cctv_data is a list, set the records in the list to TRUE, and others to FALSE

            # First, update all CCTV IDs to FALSE
            cur.execute("""
                UPDATE cctv_locations_preprocessing
                SET is_online = 'FALSE'
            """)
            logger.info(f"[DATABASE] Updated is_online to FALSE for all CCTV IDs")

            if cctv_data:
                # Set all CCTV IDs in the list to TRUE
                cur.execute("""
                    UPDATE cctv_locations_preprocessing
                    SET is_online = 'TRUE'
                    WHERE cam_id = ANY(%s::text[])
                """, (cctv_data,))
                logger.info(f"[DATABASE] Updated is_online to TRUE for CCTV IDs: {cctv_data}")

        # Commit the changes to the database
        conn.commit()

    except Exception as e:
        logger.error(f"[DATABASE] Error update_isCamOnline: {e}")
    finally:
        # Close the cursor and connection
        cur.close()
        conn.close()





'''
THIS IS CCTV CLUSTERING
'''


# Set the precision for Decimal calculations
getcontext().prec = 100  # Set precision high enough for required accuracy

def meters_to_degrees(meters: int):
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


def cluster(meters: int, all_cams_coordinate: list):
    logger.info(f"[CLUSTER] Distance set to {meters} meters")

    # Extract Cam_IDs and coordinates (Latitude, Longitude)
    cam_ids = [cam[0] for cam in all_cams_coordinate]

    coordinates = np.array([(float(cam[1]), float(cam[2])) for cam in all_cams_coordinate], dtype=float)

    # Perform clustering using DBSCAN
    logger.info("[CLUSTER] Starting clustering...")
    dbscan = DBSCAN(eps=float(meters_to_degrees(meters)), min_samples=1, metric='haversine')
    dbscan.fit(np.radians(coordinates))  # Convert degrees to radians for haversine metric

    # Extract cluster labels
    labels = dbscan.labels_

    # Combine Cam_ID, cluster group, latitude, and longitude into a list of tuples
    clustered_data = [(cam_id, int(label), float(lat), float(lon)) for cam_id, label, (lat, lon) in zip(cam_ids, labels, coordinates)]

    logger.info("[CLUSTER] Clustering completed!\n")
    return clustered_data


'''
THIS IS CCTV UPDATE
'''


# Get online CCTV list from BMA Traffic
def retrieve_camInfo_BMA(url=BASE_URL, max_retries=5, delay=5, timeout=120):
    # Return list of tuple or False if failed
    logger.info(f"[UPDATER] Getting camera list from {url}")
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, timeout=timeout)
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

                logger.info("[UPDATER] Successfully retrieved camera list.")
                return processed_data
            else:
                logger.error("[UPDATER] Error parsing camera list.")
                return False

        except requests.RequestException as e:
            retries += 1
            logger.warning(f"[UPDATER] Error retrieving camera list: {e}. Retry {retries}/{max_retries}...")
            time.sleep(delay)  # Wait before retrying

    logger.error(f"[UPDATER] Failed to retrieve camera list after {max_retries} retries.")
    return False

# Compare both online_cam and db_cam.
# Take any duplicate record out from online_cam.
# Return a list of tuple of new CCTV only
# Return a list of tuple of all CCTV (ID, Latitude, and Longitude)

def filter_new_and_all_cams(online_cam_info: list, db_cam_coordinate: list):
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

def startUpdate(meters: int):
    onlineCamInfo = retrieve_camInfo_BMA()
    dbCamCoordinate = retrieve_camLocation()
    cctv_list = []

    if onlineCamInfo:
        cctv_list = sorted([str(t[0]) for t in onlineCamInfo], key=sort_key)
        new_cams_info, all_cams_coordinate = filter_new_and_all_cams(onlineCamInfo, dbCamCoordinate)

        update_isCamOnline(cctv_list)

        # Check if there are any new cameras
        # In case there are no new cctv, remove `not` here to manually run the script
        if not new_cams_info:
            logger.info("[UPDATER] No new cameras found.")
        else:
            logger.info(f"[UPDATER] {len(new_cams_info)} new cameras are found.")

            new_cam_ids = [cam[0] for cam in new_cams_info]
            logger.info(f"[UPDATER] New camera IDs: {', '.join(map(str, new_cam_ids))}\n")

            logger.info(f"[UPDATER] Initializing clustering...")
            
            # Cluster the cameras based on their coordinates (DBSCAN)
            clustered_cams_coordinate = cluster(meters, all_cams_coordinate)

            # Insert new camera records into the database
            add_camRecord(new_cams_info)
            logger.info(f"[UPDATER] Added {len(new_cams_info)} new cameras to the database.")

            # Update the camera clusters in the database
            update_camCluster(clustered_cams_coordinate)
            logger.info(f"[UPDATER] Updated camera clusters in the database.\n")

        logger.info(f"[UPDATER] {len(cctv_list)} cameras are online out of {len(all_cams_coordinate)}")
        logger.info(f"[UPDATER] {len(all_cams_coordinate) - len(cctv_list)} cameras are offline\n")
        logger.info(f"[UPDATER] Starting scraping!\n")
        return cctv_list

    else:
        logger.warning("[UPDATER] Skipping camera update due to failure in retrieving the camera list.")
        logger.warning("[UPDATER] Attempting to retrieve session IDs for cameras from the database.")
        cctv_list = retrieve_onlineCam()
        logger.info(f"[UPDATER] Scraping process initiated for {len(cctv_list)} cameras.")
        return cctv_list


'''
JSON
'''


jsonDirectory = './cctvSessionTemp/'

def load_latest_cctv_sessions_from_json():
    loaded_JSON_latestRefreshTime = ""
    loaded_JSON_latestUpdateTime = ""
    loaded_JSON_cctvSessions = {}

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
# result = load_latest_cctv_sessions_from_json()
# if result:
#     loaded_JSON_latestRefreshTime, loaded_JSON_latestUpdateTime, loaded_JSON_cctvSessions = result
#     print(f"Latest Refresh Time: {loaded_JSON_latestRefreshTime}")
#     print(f"Latest Update Time: {loaded_JSON_latestUpdateTime}")
#     print(f"CCTV Sessions: {loaded_JSON_cctvSessions}")
# else:
#     print("No JSON file found or failed to load.")



'''
PREPARING CCTV SESSIONS
'''


# Function to get a session ID for a specific camera
def get_cctv_session_id(url: str, camera_id: str, max_retries=3, delay=5):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            cookie = response.headers.get('Set-Cookie', '')

            # Check if cookie is present
            if cookie:
                session_id = cookie.split("=")[1].split(";")[0]
                logger.info(f"[{camera_id}] Obtained session ID: {session_id}")
                return session_id
            else:
                logger.warning(f"[{camera_id}] No session cookie found. Retry {retries + 1}/{max_retries}...")
        except requests.RequestException as e:
            logger.error(f"[{camera_id}] Error getting session ID: {e}. Retry {retries + 1}/{max_retries}...")
        
        retries += 1
        time.sleep(delay)

    logger.error(f"[{camera_id}] Failed to obtain session ID after {max_retries} retries.")
    return False

# Function to play video for a camera session
def play_video(camera_id: str, session_id: str, max_retries=3, delay=5):
    url = f"{BASE_URL}/PlayVideo.aspx?ID={camera_id}"
    headers = {
        'Referer': f'{BASE_URL}/index.aspx',
        'Cookie': f'ASP.NET_SessionId={session_id};',
        'Priority': 'u=4'
    }
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, headers=headers, timeout=120)  # Added timeout
            response.raise_for_status()
            logger.info(f"[{camera_id}] Playing video for session ID: {session_id}")
            return True  # Exit function if successful
        except requests.RequestException as e:
            retries += 1
            logger.warning(f"[{camera_id}] Error playing video: {e}. Retry {retries}/{max_retries}...")
            time.sleep(delay)
    logger.error(f"[{camera_id}] Failed to play video after {max_retries} retries.")
    return False

# Get image stream from BMA Traffic
# This function will only be use for refreshing the session ID
def get_image(session_id: str, camera_id: int, max_retries=3, delay=5):
    url = f"{BASE_URL}/show.aspx"
    headers = {
        'Cookie': f'ASP.NET_SessionId={session_id};',
        'Priority': 'u=4'
    }
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, headers=headers, timeout=120)
            response.raise_for_status()
            logging.info(f"[{camera_id}] Image retrieved for session ID: {session_id}")
            return response.content
        except requests.RequestException as e:
            logging.error(f"[{camera_id}] Error getting image: {e}. Retry {retries}/{max_retries}...")
            time.sleep(delay)
    logger.error(f"[{camera_id}] Failed to get image after {max_retries} retries.")  
    return False


# Function to refresh the session ID for a camera
def create_session_id(camera_id: str, alive_session: dict, cctv_fail: list):
    # logging.info(f"Preparing session for camera {camera_id}")
    session_id = get_cctv_session_id(BASE_URL, camera_id)
    if session_id:
        success = play_video(camera_id, session_id)
        if success:
            with alive_sessions_lock.gen_wlock():
                alive_session[camera_id] = session_id
            # logging.info(f"Session ready for camera {camera_id}")
        else:
            with cctv_fail_lock.gen_wlock():
                cctv_fail.append(camera_id)
            logger.warning(f"Added failed camera (play video) to list: {camera_id}")
    else:
        with cctv_fail_lock.gen_wlock():
            cctv_fail.append(camera_id)
        logger.warning(f"Added failed camera (session ID) to list: {camera_id}")


# Function to prepare session for a camera
def prepare_session(camera_id: str, semaphore, alive_session: dict, cctv_fail: list):
    logger.info(f"[PREPARE] Preparing session for camera {camera_id}")
    try:
        create_session_id(camera_id, alive_session, cctv_fail)
        logger.info(f"[PREPARE] Session ready for camera {camera_id}")
    finally:
        semaphore.release()



# Function to manage workers for session preparation
def prepare_session_workers(cctv_list: list, alive_session: dict = None):
    threads = []
    max_workers = 80
    semaphore = Semaphore(max_workers)

    cctv_fail = []
    if alive_session is None:
        alive_session = {}

    logger.info("[INFO] Initializing all session IDs.")
    for camera_id in cctv_list:
        semaphore.acquire()
        thread = threading.Thread(target=prepare_session, args=(camera_id, semaphore, alive_session, cctv_fail))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    alive_session = dict(sorted(alive_session.items(), key=lambda x: sort_key(x[0])))
    cctv_fail = sorted(cctv_fail, key=sort_key)

    return alive_session, cctv_fail


def startGettingNewSessionID(camDistance: int):
    # cctv_list = ['7', '11', '39', '77', '83', '572']
    cctv_list = startUpdate(camDistance)
    alive_session, cctv_fail = prepare_session_workers(cctv_list)
    scraped_cctv = len(cctv_list)
    processed_cctv = len(alive_session)
    fail_to_processed_cctv = len(cctv_fail)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.info(f"\n\n[INFO] Total number of scraped CCTVs: {scraped_cctv}")
    logger.info(f"[INFO] Successfully processed {processed_cctv} CCTVs out of {processed_cctv + fail_to_processed_cctv}.")

    if cctv_fail:
        logger.info(f"[INFO] The following CCTV IDs failed to prepare and will not be available: {cctv_fail}")
        update_isCamOnline(cctv_fail)

    if scraped_cctv != (processed_cctv + fail_to_processed_cctv):
        logger.warning(f"[INFO] number of items in `CCTV_LIST` does not equal to the sum of `processed_cctv` and `fail_to_processed_cctv`")

    
    save_alive_session_to_file(alive_session, current_time, current_time)

    logger.info("[INFO] All session IDs have been successfully prepared and saved.\n\n")


def process_session(camera_id, session_id, semaphore, alive_session, offline_session):
    try:
        retries = 0
        success = False

        while retries < 5:  # Retry up to 5 times
            image_data = get_image(session_id, camera_id, max_retries=3, delay=5)

            if image_data and len(image_data) > 5120:  # If image size > 5120 bytes
                alive_session[camera_id] = session_id
                logger.info(f"[{camera_id}] Success: Image size is greater than 5120 bytes.")
                success = True
                break  # No need to retry if successful
            else:
                retries += 1
                logger.warning(f"[{camera_id}] Failed to retrieve valid image. Attempt {retries}/5.")

        if not success:
            offline_session.append(camera_id)
            logger.error(f"[{camera_id}] Marked as offline after {retries} failed attempts.")

    finally:
        semaphore.release()  # Release the semaphore once the thread finishes

def process_cctv_sessions_multithreaded(loaded_JSON_cctvSessions: dict):
    threads = []
    max_workers = 80
    semaphore = Semaphore(max_workers)
    
    alive_session = {}
    offline_session = []

    logger.info("[INFO] Starting session validation workers.")
    
    for camera_id, session_id in loaded_JSON_cctvSessions.items():
        semaphore.acquire()  # Acquire a slot for this thread
        thread = threading.Thread(target=process_session, args=(camera_id, session_id, semaphore, alive_session, offline_session))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()


    offline_session = sorted(offline_session, key=sort_key)
    alive_session = dict(sorted(alive_session.items(), key=lambda x: sort_key(x[0])))

    alive_count = len(alive_session)
    offline_count = len(offline_session)

    logger.info(f"[INFO] All sessions are validated.")
    logger.info(f"[INFO] Total alive sessions: {alive_count}")
    logger.info(f"[INFO] Alive CCTV IDs: {list(alive_session.keys())}")
    
    logger.info(f"[INFO] Total offline sessions: {offline_count}")
    logger.info(f"[INFO] Offline CCTV IDs: {offline_session}")
    return alive_session, offline_session


def update_cctv_sessions(alive_session: dict, offline_session: list):
    # Call retrieve_camInfo_BMA() to get a list of tuples or False if failed
    result = retrieve_camInfo_BMA()

    if not result:
        logger.error("[ERROR] Failed to retrieve camera info from BMA.")
        return False, None

    # Extract the cam IDs from the result (assuming the tuple format is like (cam_id, some_other_data))
    current_cctv = [cam[0] for cam in result]  # List of current cam IDs

    # Initialize get_session list to store new cam IDs that need sessions
    get_session = []

    # Step 1: Check for cam IDs in current_cctv that are not present in alive_session
    for cam_id in current_cctv:
        if cam_id not in alive_session:
            get_session.append(cam_id)

    # Step 2: Check for cam IDs in alive_session that are not present in current_cctv
    for cam_id in alive_session.keys():
        if cam_id not in current_cctv:
            offline_session.append(cam_id)
            logger.warning(f"[WARNING] CCTV ID {cam_id} is alive but not found in current cam list. Marking as offline for edge case.")

    # Log results
    logger.info(f"[INFO] Total current cam IDs: {len(current_cctv)}")
    logger.info(f"[INFO] Total cams that need new sessions: {len(get_session)}")
    logger.info(f"[INFO] New session needed for cam IDs: {sorted(get_session, key=sort_key)}")
    logger.info(f"[INFO] Total offline cams (including edge cases): {len(offline_session)}")
    logger.info(f"[INFO] Offline CCTV IDs: {offline_session}")

    return get_session, offline_session


def startRefreshingSessionID(loaded_JSON_cctvSessions: dict, loaded_JSON_latestUpdateTime: str):
    alive_session, offline_session = process_cctv_sessions_multithreaded(loaded_JSON_cctvSessions)
    get_session, offline_session = update_cctv_sessions(alive_session, offline_session)
    alive_session, cctv_fail = prepare_session_workers(get_session, alive_session)
    update_isCamOnline(list(alive_session.keys()))
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_alive_session_to_file(alive_session, current_time, loaded_JSON_latestUpdateTime)


def readableTime(total_seconds: int):
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        readable_diff = f"{hours} hours, {minutes} minutes, and {seconds} seconds ago"
    elif minutes > 0:
        readable_diff = f"{minutes} minutes and {seconds} seconds ago"
    else:
        readable_diff = f"{seconds} seconds ago"
    
    return readable_diff



if __name__ == "__main__":
    camDistance = initialize()
    result = load_latest_cctv_sessions_from_json()

    if result:
        loaded_JSON_latestRefreshTime, loaded_JSON_latestUpdateTime, loaded_JSON_cctvSessions = result
        logger.info(f"[INFO] Latest Refresh Time: {loaded_JSON_latestRefreshTime}")
        logger.info(f"[INFO] Latest Update Time: {loaded_JSON_latestUpdateTime}")
        logger.info(f"[INFO] CCTV Sessions: {loaded_JSON_cctvSessions}")

        current_time = datetime.now()
        loaded_JSON_latestUpdateTime_dt = datetime.strptime(loaded_JSON_latestUpdateTime, "%Y-%m-%d %H:%M:%S")
        timeDiff = current_time - loaded_JSON_latestUpdateTime_dt

        total_seconds = int(timeDiff.total_seconds())
        readable_diff = readableTime(total_seconds)

        if timeDiff < timedelta(hours=3):
            logger.info(f"[INFO] The latest update occurred at {loaded_JSON_latestUpdateTime}, which was {readable_diff}.")
            startRefreshingSessionID(loaded_JSON_cctvSessions, loaded_JSON_latestUpdateTime)

        else:
            logger.info("[INFO] The latest update time is older than 3 hours.")
            startGettingNewSessionID(camDistance)
    else:
        logger.warning("[INFO] No JSON file found or failed to load. Fetching all session ID")
        startGettingNewSessionID(camDistance)
        

    
