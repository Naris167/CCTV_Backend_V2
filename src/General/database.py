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

def add_camRecord(
        camera_data: List[Tuple[str, Union[str, None], Union[float, None], Union[float, None]]]
        ) -> None:
    with get_db_connection() as conn:
        try:
            check_query = "SELECT Cam_ID FROM cctv_locations_general WHERE Cam_ID = ANY(%s)"
            insert_query = """
                INSERT INTO cctv_locations_general (
                    Cam_ID, Cam_Name, Latitude, Longitude
                ) VALUES (%s, %s, %s, %s)
            """
            cam_ids = [cam[0] for cam in camera_data]
            existing_ids = set(row[0] for row in execute_fetch_query(check_query, (cam_ids,)))
            
            insert_value = [cam for cam in camera_data if cam[0] not in existing_ids]
            if insert_value:
                with conn.cursor() as cur:
                    cur.executemany(insert_query, insert_value)
                conn.commit()
                logger.info(f"[DATABASE] {len(insert_value)} new cameras were added to the database.")
            else:
                logger.info("[DATABASE] No new cameras were added to the database.")
        except Exception as e:
            conn.rollback()
            logger.error(f"[DATABASE] An error occurred in add_camRecord: {e}")