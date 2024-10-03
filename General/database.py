import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv
from contextlib import contextmanager
from log_config import logger
from utils import sort_key
from typing import List, Tuple, Union, Dict

load_dotenv('.env.local')

@contextmanager
def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    try:
        yield conn
    finally:
        conn.close()

def execute_fetch_query(query, params=None):
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
        except Exception as e:
            conn.rollback()
            logger.error(f"[DATABASE] Error executing query: {e}")
            raise

def retrieve_camID() -> List[str]:
    try:
        query = "SELECT Cam_ID FROM cctv_locations_general"
        return sorted([row[0] for row in execute_fetch_query(query)], key=sort_key)
    except Exception as e:
        logger.error(f"[DATABASE] Error retrieve_camID: {e}")
        return []

def update_stream_status():
    # Check if Stream_Link_1 is empty and update is_online accordingly.
    with get_db_connection() as conn:
        try:
            update_query = """
                UPDATE cctv_locations_general
                SET is_online = CASE
                    WHEN Stream_Link_1 IS NOT NULL AND Stream_Link_1 != '' THEN TRUE
                    ELSE FALSE
                END
            """
            with conn.cursor() as cur:
                cur.execute(update_query)
                conn.commit()
                logger.info(f"Updated {cur.rowcount} rows.")
        except Exception as e:
            conn.rollback()
            logger.error(f"[DATABASE] Error updating stream status: {e}")


def update_isCamOnline(cctv_data: Union[Dict[str, bool], List[str]]) -> None:
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                if isinstance(cctv_data, dict):
                    # Case 1: If cctv_data is a dictionary with CCTV IDs as keys and TRUE/FALSE as values
                    if not cctv_data:
                        logger.warning("[DATABASE] Empty dictionary provided to update_isCamOnline. No updates performed.")
                        return
                    update_query = "UPDATE cctv_locations_general SET is_online = %s WHERE cam_id = %s"
                    update_value = [(is_online, cam_id) for cam_id, is_online in cctv_data.items()]
                    cur.executemany(update_query, update_value)
                    logger.info(f"[DATABASE] Updated is_online status for CCTV IDs: {cctv_data}")
                elif isinstance(cctv_data, list):
                    # Case 2: If cctv_data is a list, set the records in the list to TRUE, and others to FALSE
                    if not cctv_data:
                        logger.warning("[DATABASE] Empty list provided to update_isCamOnline. No updates performed.")
                        return
                    cur.execute("UPDATE cctv_locations_general SET is_online = FALSE")
                    cur.execute("UPDATE cctv_locations_general SET is_online = TRUE WHERE cam_id = ANY(%s::text[])", (cctv_data,))
                    logger.info(f"[DATABASE] Updated is_online status: Set to TRUE for CCTV IDs {cctv_data}, and FALSE for all others")
                else:
                    logger.error("[DATABASE] Invalid data type provided to update_isCamOnline. Expected dict or list.")
                    return
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"[DATABASE] Error in update_isCamOnline: {e}")

def add_camRecord_Ubon(
        camera_data: List[Tuple[str, str, float, float, str, str]]
        ) -> None:
    with get_db_connection() as conn:
        try:
            check_query = "SELECT Cam_ID FROM cctv_locations_general WHERE Cam_ID = ANY(%s)"
            insert_query = """
                INSERT INTO cctv_locations_general (
                    Cam_ID, Cam_Name, Latitude, Longitude, Stream_Method, Stream_Link_1
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            cam_ids = [cam[0] for cam in camera_data]
            existing_ids = set(row[0] for row in execute_fetch_query(check_query, (cam_ids,)))
            
            insert_value = [cam for cam in camera_data if cam[0] not in existing_ids]
            if insert_value:
                with conn.cursor() as cur:
                    cur.executemany(insert_query, insert_value)
                conn.commit()
                logger.info(f"[DATABASE_Ubon] {len(insert_value)} new cameras were added to the database.")
            else:
                logger.info("[DATABASE_Ubon] No new cameras were added to the database.")
        except Exception as e:
            conn.rollback()
            logger.error(f"[DATABASE_Ubon] An error occurred in add_camRecord: {e}")

def add_camRecord_iTic(
        camera_data: List[Tuple[str, str, float, float, str, str,
                                Union[str, None], Union[str, None], Union[str, None], Union[str, None],
                                Union[str, None], Union[str, None], Union[str, None], Union[str, None],
                                Union[bool, None], Union[bool, None]]]
        ) -> None:
    with get_db_connection() as conn:
        try:
            check_query = "SELECT Cam_ID FROM cctv_locations_general WHERE Cam_ID = ANY(%s)"
            insert_query = """
                INSERT INTO cctv_locations_general (
                    Cam_ID, Cam_Name, Latitude, Longitude, Stream_Method, Stream_Link_1,
                    Stream_Link_2, Stream_Link_3, Stream_Link_4, Stream_Link_5,
                    Stream_Link_6, Organization, SponsorText, LastUpdate, is_inCity, is_motion
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cam_ids = [cam[0] for cam in camera_data]
            existing_ids = set(row[0] for row in execute_fetch_query(check_query, (cam_ids,)))
            
            insert_value = [cam for cam in camera_data if cam[0] not in existing_ids]
            if insert_value:
                with conn.cursor() as cur:
                    cur.executemany(insert_query, insert_value)
                conn.commit()
                logger.info(f"[DATABASE_iTic] {len(insert_value)} new cameras were added to the database.")
            else:
                logger.info("[DATABASE_iTic] No new cameras were added to the database.")
        except Exception as e:
            conn.rollback()
            logger.error(f"[DATABASE_iTic] An error occurred in add_camRecord: {e}")