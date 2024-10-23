import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.sql import SQL, Identifier
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
                logger.info(f"[DATABASE-{operation_type.upper()}-QUERY] {query}")
                logger.info(f"[DATABASE-{operation_type.upper()}-PARAMS] {params}")
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
                # Check if data is either a tuple or a list
                if isinstance(data, (tuple, list)):
                    # Create the correct number of placeholders for IN clause
                    placeholders = ','.join(['%s' for _ in data])
                    where_clauses.append(f"{col} IN ({placeholders})")
                    # Extend params with each element of the list/tuple
                    params = params + tuple(data)
                else:
                    where_clauses.append(f"{col} = %s")
                    params = params + (data,)
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
    columns_to_update: Union[Tuple[str, ...], str],
    data_to_update: Union[Tuple[Any, ...], List[Any]],
    columns_to_check_condition: Union[Tuple[str, ...], str],
    data_to_check_condition: Union[Tuple[Any, ...], List[Any]]
) -> Optional[int]:
    """
    Build and execute UPDATE query with dynamic conditions using PostgreSQL's ANY operator.
    Supports both single value updates and multiple row updates.
    """
    try:
        # Convert single string columns to tuples
        if isinstance(columns_to_update, str):
            columns_to_update = (columns_to_update,)
        if isinstance(columns_to_check_condition, str):
            columns_to_check_condition = (columns_to_check_condition,)
            
        # Convert single values to tuples
        if not isinstance(data_to_update, (list, tuple)):
            data_to_update = (data_to_update,)
        if not isinstance(data_to_check_condition, (list, tuple)):
            data_to_check_condition = (data_to_check_condition,)

        # Check if we're doing a multi-row update
        is_multi_row = any(isinstance(val, (list, tuple)) for val in data_to_update)
        
        if is_multi_row:
            """Handle updates where data_to_update contains lists for multiple rows"""
    
            # Validate that all update data lists have the same length
            first_list = next(val for val in data_to_update if isinstance(val, (list, tuple)))
            expected_length = len(first_list)
            
            # Normalize all inputs to lists of the same length
            normalized_data = []
            for val in data_to_update:
                if isinstance(val, (list, tuple)):
                    if len(val) != expected_length:
                        raise ValueError("All input lists must have the same length")
                    normalized_data.append(val)
                else:
                    normalized_data.append([val] * expected_length)
            
            # Build the UPDATE query
            set_clause = ", ".join(f"{col} = %s" for col in columns_to_update)
            where_clause = " AND ".join(f"{col} = %s" for col in columns_to_check_condition)
            
            query = f"""
                UPDATE {table} 
                SET {set_clause}
                WHERE {where_clause}
            """
            
            # Prepare data tuples for batch execution
            data_tuples = []
            for i in range(expected_length):
                row_data = []
                # Add update values
                for col_data in normalized_data:
                    row_data.append(col_data[i])
                # Add condition values
                if isinstance(data_to_check_condition[0], (list, tuple)):
                    for condition_data in data_to_check_condition:
                        row_data.append(condition_data[i])
                else:
                    row_data.extend(data_to_check_condition)
                data_tuples.append(tuple(row_data))
            
            return execute_db_operation(query, 'update', data_tuples)
        else:
            """Handle regular updates with possible ANY conditions"""
    
            # Build SET clause
            set_clause_parts = []
            params: List[Any] = []
            
            for col in columns_to_update:
                set_clause_parts.append(f"{col} = %s")
            params.extend(data_to_update)
            
            query = f"UPDATE {table} SET {', '.join(set_clause_parts)}"
            
            # Build WHERE clause
            where_clause_parts = []
            if columns_to_check_condition and data_to_check_condition:
                for col, value in zip(columns_to_check_condition, data_to_check_condition):
                    if isinstance(value, (list, tuple)):
                        where_clause_parts.append(f"{col}::text = ANY(%s::text[])")
                        params.append(list(map(str, value)))
                    else:
                        where_clause_parts.append(f"{col} = %s")
                        params.append(value)
                
                query += " WHERE " + " AND ".join(where_clause_parts)
            
            return execute_db_operation(query, 'update', tuple(params))
            
    except Exception as e:
        logger.error(f"[UPDATE] Error building update query: {str(e)}")
        raise


    

def update_pair_data(
    table: str,
    column_to_update: str,
    data_to_update: List[Any],
    column_to_check_condition: str,
    data_to_check_condition: List[Any],
    batch_size: int = 1000
) -> tuple[bool, str]:
    """
    Perform optimized batch updates on a PostgreSQL table using value pairs.
    
    Args:
        table (str): Name of the table to update
        column_to_update (str): Column name to be updated
        data_to_update (List[Any]): List of values to update
        column_to_check_condition (str): Column name for WHERE condition
        data_to_check_condition (List[Any]): List of condition values
        batch_size (int): Size of batches for processing (default: 1000)
    
    Returns:
        tuple[bool, str]: (Success status, Message)
    """
    if len(data_to_update) != len(data_to_check_condition):
        return False, "Update and condition data lists must have the same length"
        
    if not data_to_update or not data_to_check_condition:
        return False, "Empty data provided for update"

    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                # Process updates in batches
                for i in range(0, len(data_to_update), batch_size):
                    batch_update = data_to_update[i:i + batch_size]
                    batch_condition = data_to_check_condition[i:i + batch_size]
                    
                    # Create tuples for values
                    value_pairs = list(zip(batch_update, batch_condition))
                    
                    # Construct the VALUES part of the query
                    values_template = ",".join([f"(%s, %s)"] * len(value_pairs))
                    
                    # Construct the complete query
                    query = SQL("""
                        UPDATE {table}
                        SET {update_col} = v.new_value
                        FROM (VALUES {values}) AS v(new_value, condition_value)
                        WHERE {condition_col}::text = v.condition_value
                    """).format(
                        table=Identifier(table),
                        update_col=Identifier(column_to_update),
                        values=SQL(values_template),
                        condition_col=Identifier(column_to_check_condition)
                    )
                    
                    # Flatten the value pairs for the execute parameters
                    flattened_values = [val for pair in value_pairs for val in pair]
                    
                    # Execute the query with the batch
                    cur.execute(query, flattened_values)
                    
                    # Log the batch progress
                    logger.info(f"[DATABASE-UPDATE-PAIR] Processed batch of {len(batch_update)} records")
                
                # Commit the transaction
                conn.commit()
                
                return True, f"Successfully updated {len(data_to_update)} records"
                
        except Exception as e:
            conn.rollback()
            error_msg = f"[DATABASE-UPDATE-PAIR] Error executing update operation: {str(e)}"
            logger.error(error_msg)
            return False, error_msg