import psycopg2
import os
from dotenv import load_dotenv
from contextlib import contextmanager
from utils.log_config import logger
from utils.utils import sort_key
from typing import List, Tuple, Dict, Optional, Any

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

'''
Without parameters:
query = "SELECT * FROM users"
results = execute_fetch_query(query)

With tuple parameters:
query = "SELECT * FROM users WHERE age > %s AND city = %s"
params = (18, 'New York')
results = execute_fetch_query(query, params)

With dictionary parameters:
query = "SELECT * FROM users WHERE age > %(min_age)s AND city = %(city)s"
params = {'min_age': 18, 'city': 'New York'}
results = execute_fetch_query(query, params)
'''

def execute_db_operation(query: str, operation_type: str, params: Optional[Any] = None):
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                match operation_type:
                    case 'fetch':
                        cur.execute(query, params)
                        return cur.fetchall()
                    case 'insert' | 'update' if params:
                        cur.executemany(query, params)
                        affected_rows = cur.rowcount
                        conn.commit()
                        return affected_rows
                    case 'delete' if params:
                        cur.execute(query, params)
                        affected_rows = cur.rowcount
                        conn.commit()
                        return affected_rows
                    case _:
                        logger.error(f"[DATABASE] Invalid operation_type or missing parameters")
                        return None
        except Exception as e:
            conn.rollback()
            logger.error(f"[DATABASE] Error executing {operation_type} operation: {e}")
            raise

'''
# Example usage
table = 'cctv_locations_general'
columns = ['Cam_ID', 'Location'] # If you want to query for specified clomuns
all_column = ['*'] # If you want to query for all clomuns
condition = {'IsActive': True, 'IsFlood': True} # This param is optional

results = retrieve_data(table, columns, condition)
'''

def retrieve_data(table: str, columns: List[str], conditions: Optional[Dict[str, Any]] = None) -> List[Any]:
    try:
        # Construct the base query
        query = f"SELECT {', '.join(columns)} FROM {table}"
        
        # Add WHERE clause if conditions are provided
        params = {}
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                where_clauses.append(f"{key} = %({key})s")
                params[key] = value
            query += " WHERE " + " AND ".join(where_clauses)

        # Execute the query
        results = execute_db_operation(query, "fetch", params if params else None)

        # Sort the results if 'Cam_ID' is in the columns
        if 'Cam_ID' in columns:
            cam_id_index = columns.index('Cam_ID')
            results = sorted([row[cam_id_index] for row in results], key=sort_key)
        else:
            results = [row for row in results]
        
        logger.info(f"[DATABASE] Successfully retrieved data from {table}")
        return results

    except Exception as e:
        logger.error(f"[DATABASE] Error retrieving data from {table}: {e}")
        return None

'''
# Example usage
table = 'cctv_locations_general'
columns = ['Cam_ID', 'Location', 'IsActive']
data_to_insert = [
    ('CAM001', 'New York', True),
    ('CAM002', 'Los Angeles', False),
    ('CAM003', 'Chicago', True),
    ('CAM004', 'Houston', True),
    ('CAM005', 'Phoenix', False)
]

insert_data(table, columns, data_to_insert)
'''

def insert_data(table: str, columns: List[str], params: List[Tuple[Any, ...]]) -> int:
    try:
        # Construct the base query
        placeholders = ', '.join(['%s' for _ in columns])
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

        # Execute the query
        rows_inserted = execute_db_operation(query, "insert", params)
        logger.info(f"[DATABASE] Successfully inserted {rows_inserted} rows to {table}")
        return

    except Exception as e:
        logger.error(f"[DATABASE] Error inserting data into {table}: {e}")
        return


'''
# Example usage
table = 'cctv_locations_general'
conditions = {'IsActive': True, 'IsFlood': True}

delete_data(table, conditions)
'''


def delete_data(table: str, conditions: Dict[str, Any]) -> int:
    try:
        # Construct the base query
        query = f"DELETE FROM {table}"
        
        # Add WHERE clause
        where_clauses = []
        params = {}
        for key, value in conditions.items():
            where_clauses.append(f"{key} = %({key})s")
            params[key] = value
        
        query += " WHERE " + " AND ".join(where_clauses)

        rows_deleted = execute_db_operation(query, "delete", params)
                
        logger.info(f"[DATABASE] Successfully deleted {rows_deleted} rows from {table}")
        return

    except Exception as e:
        logger.error(f"[DATABASE] Error deleting data from {table}: {e}")
        return


'''
# Example usage 1: Update all records
table = 'cctv_locations_preprocessing'
columns_to_update = ['is_online', 'last_checked']
data_to_update = [(True, '2023-10-03 12:00:00')]


In this case the query will be:
UPDATE cctv_locations_preprocessing 
SET is_online = TRUE, last_checked = '2023-10-03 12:00:00'



# Example usage 2: with multiple columns in WHERE clause
table = 'cctv_locations_preprocessing'
columns_to_update = ['is_online', 'last_checked']
data_to_update = [(True, '2023-10-03 12:00:00')]
columns_to_check_condition = ['cam_id', 'location', 'status']
data_to_check_condition = [
    ['CAM001', 'CAM002', 'CAM003'],  # List of CCTV IDs
    ['New York', 'Los Angeles'],     # List of locations
    'active'                         # Single value for status
]


In this case the query will be:
UPDATE cctv_locations_preprocessing 
SET is_online = TRUE, last_checked = '2023-10-03 12:00:00'
WHERE cam_id = ANY(%s::text[]) 
  AND location = ANY(%s::text[]) 
  AND status = %s
'''

def update_data(
    table: str,
    columns_to_update: List[str],
    data_to_update: List[Tuple],
    columns_to_check_condition: Optional[List[str]] = None,
    data_to_check_condition: Optional[List[Any]] = None
) -> int:
    try:
        # Construct the base query
        set_clause = ", ".join([f"{col} = %s" for col in columns_to_update])
        
        # Construct WHERE clause only if conditions are provided
        where_clause = ""
        if columns_to_check_condition and data_to_check_condition:
            where_conditions = []
            for i, col in enumerate(columns_to_check_condition):
                if isinstance(data_to_check_condition[i], list):
                    where_conditions.append(f"{col} = ANY(%s::text[])")
                else:
                    where_conditions.append(f"{col} = %s")
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"UPDATE {table} SET {set_clause} {where_clause}"

        # Prepare the parameters
        params = []
        for row in data_to_update:
            param_row = list(row)
            if data_to_check_condition:
                for condition in data_to_check_condition:
                    if isinstance(condition, list):
                        param_row.append(condition)
                    else:
                        param_row.append([condition])  # Convert single values to lists
            params.append(tuple(param_row))

        rows_updated = execute_db_operation(query, "update", params)

        logger.info(f"[DATABASE] Successfully updated {rows_updated} records in {table}")
        return rows_updated

    except Exception as e:
        logger.error(f"[DATABASE] Error updating data in {table}: {e}")
        return 0