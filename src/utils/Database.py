import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from contextlib import contextmanager
from utils.log_config import logger
from typing import List, Tuple, Dict, Optional, Any, Union

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

def execute_db_operation(query: str, operation_type: str, params: Optional[Union[Dict, List, Tuple]] = None, batch_size: int = 1000, fetch_type: str = 'tuple'):
    with get_db_connection() as conn:
        try:
            cursor_factory = RealDictCursor if fetch_type == 'dict' else None
            with conn.cursor(cursor_factory=cursor_factory) as cur:
                match operation_type:
                    case 'fetch':
                        cur.execute(query, params)
                        return cur.fetchall()
                    case 'insert' | 'update' if params:
                        if isinstance(params, (list, tuple)) and params and isinstance(params[0], (dict, tuple, list)):
                            return _execute_batch(cur, query, params, batch_size)
                        else:
                            cur.execute(query, params)
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

def _execute_batch(cur, query: str, params: List[Union[Dict, Tuple]], batch_size: int) -> int:
    total_affected_rows = 0
    for i in range(0, len(params), batch_size):
        batch = params[i:i+batch_size]
        cur.executemany(query, batch)
        total_affected_rows += cur.rowcount
    cur.connection.commit()
    return total_affected_rows


'''
table = 'cctv_locations_general'
columns = ('Cam_ID', 'Location')  # If you want to query for specified columns
# all_columns = ('*',)  # If you want to query for all columns
columns_to_check_condition = ('cam_id', 'location', 'status')
data_to_check_condition = (
    ('CAM001', 'CAM002', 'CAM003'),  # Tuple of CCTV IDs
    ('New York', 'Los Angeles'),     # Tuple of locations
    'active'                         # Single value for status
)

results = retrieve_data(table, columns, columns_to_check_condition, data_to_check_condition)

SELECT Cam_ID, Location 
FROM cctv_locations_general 
WHERE cam_id IN (%s, %s, %s) 
  AND location IN (%s, %s) 
  AND status = %sl
'''

def retrieve_data(
    table: str,
    columns: Tuple[str, ...],
    columns_to_check_condition: Optional[Tuple[str, ...]] = None,
    data_to_check_condition: Optional[Tuple[Any, ...]] = None
) -> Tuple[Tuple[Any, ...], ...]:
    try:
        # Construct the base query
        query = f"SELECT {', '.join(columns)} FROM {table}"
        
        # Add WHERE clause if conditions are provided
        params = ()
        if columns_to_check_condition and data_to_check_condition:
            where_clauses = []
            for col, data in zip(columns_to_check_condition, data_to_check_condition):
                if isinstance(data, tuple):
                    placeholders = ', '.join(['%s'] * len(data))
                    where_clauses.append(f"{col} IN ({placeholders})")
                    params += data
                else:
                    where_clauses.append(f"{col} = %s")
                    params += (data,)
            query += " WHERE " + " AND ".join(where_clauses)

        # Execute the query
        results = execute_db_operation(query, "fetch", params if params else None)
        
        logger.info(f"[DATABASE-RETRIEVE] Successfully retrieved data from {table}")
        return results

    except Exception as e:
        logger.error(f"[DATABASE-RETRIEVE] Error retrieving data from {table}: {e}")
        return tuple()
'''
table = 'cctv_locations_general'
columns = ('Cam_ID', 'Location', 'IsActive')
data_to_insert = (
    ('CAM001', 'New York', True),
    ('CAM002', 'Los Angeles', False),
    ('CAM003', 'Chicago', True),
    ('CAM004', 'Houston', True),
    ('CAM005', 'Phoenix', False)
)

insert_data(table, columns, data_to_insert)

INSERT INTO cctv_locations_general (Cam_ID, Location, IsActive) 
VALUES (%s, %s, %s)
'''

def insert_data(table: str, columns: Tuple[str, ...], data_to_insert: Tuple[Tuple[Any, ...], ...]) -> int:
    try:
        # Construct the base query
        placeholders = ', '.join(['%s' for _ in columns])
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

        # Execute the query
        rows_inserted = execute_db_operation(query, "insert", data_to_insert)
        logger.info(f"[DATABASE-INSERT] Successfully inserted {rows_inserted} rows to {table}")
        return rows_inserted

    except Exception as e:
        logger.error(f"[DATABASE-INSERT] Error inserting data into {table}: {e}")
        return 0


'''
table = 'cctv_locations_general'
columns_to_check_condition = ('cam_id', 'location', 'status')
data_to_check_condition = (
    ('CAM001', 'CAM002', 'CAM003'),  # Tuple of CCTV IDs
    ('New York', 'Los Angeles'),     # Tuple of locations
    'active'                         # Single value for status
)

rows_deleted = delete_data(table, columns_to_check_condition, data_to_check_condition)

DELETE FROM cctv_locations_general 
WHERE cam_id IN (%s, %s, %s) 
  AND location IN (%s, %s) 
  AND status = %s
'''

def delete_data(table: str, columns_to_check_condition: Tuple[str, ...], data_to_check_condition: Tuple[Union[Tuple[Any, ...], Any], ...]) -> int:
    try:
        # Construct the base query
        query = f"DELETE FROM {table}"
        
        # Add WHERE clause
        where_clauses = []
        params = {}
        
        for column, data in zip(columns_to_check_condition, data_to_check_condition):
            if isinstance(data, tuple):
                placeholders = [f"%({column}_{i})s" for i in range(len(data))]
                where_clauses.append(f"{column} IN ({', '.join(placeholders)})")
                params.update({f"{column}_{i}": value for i, value in enumerate(data)})
            else:
                where_clauses.append(f"{column} = %({column})s")
                params[column] = data
        
        query += " WHERE " + " AND ".join(where_clauses)

        rows_deleted = execute_db_operation(query, "delete", params)
                
        logger.info(f"[DATABASE-DELETE] Successfully deleted {rows_deleted} rows from {table}")
        return rows_deleted

    except Exception as e:
        logger.error(f"[DATABASE-DELETE] Error deleting data from {table}: {e}")
        return 0


'''
# Example usage 1: Update all records
table = 'cctv_locations_preprocessing'
columns_to_update = ('is_online', 'last_checked')
data_to_update = (True, '2023-10-03 12:00:00')

results1 = update_data(table, columns_to_update, data_to_update)

UPDATE cctv_locations_preprocessing 
SET is_online = %s, last_checked = %s


# Example usage 2: with multiple columns in WHERE clause
table = 'cctv_locations_preprocessing'
columns_to_update = ('is_online', 'last_checked')
data_to_update = (True, '2023-10-03 12:00:00')
columns_to_check_condition = ('cam_id', 'location', 'status')
data_to_check_condition = (
    ('CAM001', 'CAM002', 'CAM003'),  # Tuple of CCTV IDs
    ('New York', 'Los Angeles'),     # Tuple of locations
    'active'                         # Single value for status
)

results2 = update_data(table, columns_to_update, data_to_update, columns_to_check_condition, data_to_check_condition)

UPDATE cctv_locations_preprocessing 
SET is_online = %s, last_checked = %s
WHERE cam_id = ANY(%s::text[]) 
  AND location = ANY(%s::text[]) 
  AND status = %s
'''

def update_data(
    table: str,
    columns_to_update: Tuple[str, ...],
    data_to_update: Any,
    columns_to_check_condition: Optional[Tuple[str, ...]] = None,
    data_to_check_condition: Optional[Any] = None
) -> int:
    try:
        # Convert generators to lists
        update_data = list(data_to_update)
        logger.info(f"[DATABASE-UPDATE] Update data: {update_data}")
        
        if columns_to_check_condition and data_to_check_condition:
            # Convert condition data to lists
            condition_data = []
            for data in data_to_check_condition:
                if hasattr(data, '__iter__') and not isinstance(data, (str, bytes)):
                    condition_data.append(list(data))
                else:
                    condition_data.append([data])
            
            # Build CASE WHEN for each column to update
            set_clauses = []
            params = []
            
            for col in columns_to_update:
                when_clauses = []
                for i, update_val in enumerate(update_data):
                    # Handle tuple or single value
                    val = update_val[0] if isinstance(update_val, (tuple, list)) else update_val
                    when_clauses.append(f"WHEN {columns_to_check_condition[0]} = %s THEN %s")
                    params.extend([condition_data[0][i], val])
                
                set_clauses.append(
                    f"{col} = (CASE {' '.join(when_clauses)} ELSE {col} END)"
                )
            
            # Construct the query
            query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {columns_to_check_condition[0]} = ANY(%s::text[])"
            params.append(condition_data[0])  # Add the array for ANY clause

            # Debug logs
            logger.info(f"[DATABASE-UPDATE] Query: {query}")
            logger.info(f"[DATABASE-UPDATE] Params: {params}")

            # Execute the query
            rows_updated = execute_db_operation(query, "update", tuple(params))
            
            logger.info(f"[DATABASE-UPDATE] Successfully updated {rows_updated} records in {table}")
            return rows_updated

    except Exception as e:
        logger.error(f"[DATABASE-UPDATE] Error updating data in {table}: {e}")
        # raise