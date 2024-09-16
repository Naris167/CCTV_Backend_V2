import psycopg2
import os
from dotenv import load_dotenv
from log_config import logger
from utils import sort_key
from typing import List, Tuple, Union, Dict


load_dotenv('.env.local')

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )

def retrieve_camID() -> List[str]:
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = "SELECT Cam_ID FROM cctv_locations_preprocessing"
        cur.execute(query)

        cam_ids = [row[0] for row in cur.fetchall()]  # This will return a list of cam_ids
        sorted_cam_ids = sorted(cam_ids, key=sort_key)

        cur.close()
        conn.close()

        return sorted_cam_ids
    
    except Exception as e:
        logger.error(f"[DATABASE] Error retrieve_camID: {e}")
        return []

def retrieve_camLocation() -> List[Tuple[str, float, float]]:
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

        # Close the cursor and connection
        cur.close()
        conn.close()

        return sorted_cam_locations
    
    except Exception as e:
        logger.error(f"[DATABASE] Error retrieve_camLocation: {e}")
        return []

# If this function return empty list, it will cause error to `prepare_create_sessionID_workers()`
def retrieve_onlineCam() -> List[str]:
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


def add_camRecord(
        camera_data: List[Tuple[str, Union[str, None], Union[str, None], Union[str, None], Union[str, None], Union[str, None], Union[float, None], Union[float, None], Union[str, None], Union[str, None]]]
        ) -> None:
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

def update_camCluster(clustered_data: List[Tuple[str, str, float, float]]):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # SQL command to update the Cam_Group based on Cam_ID
        update_query = "UPDATE cctv_locations_preprocessing SET Cam_Group = %s WHERE Cam_ID = %s"

        # Iterate over each camera in the clustered_data
        for cam_id, label, lat, lon in clustered_data:
            cur.execute(update_query, (str(label), str(cam_id)))
            
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

def update_isCamOnline(cctv_data: Union[Dict[str, bool], List[str]]) -> None:
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

