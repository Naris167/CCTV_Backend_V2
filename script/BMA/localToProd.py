import os
from dotenv import dotenv_values
import psycopg2

# Load environment variables for source database connection
source_credential = dotenv_values('.env.local')

def get_source_db_connection():
    return psycopg2.connect(
        dbname=source_credential['DB_NAME'],
        user=source_credential['DB_USER'],
        password=source_credential['DB_PASSWORD'],
        host=source_credential['DB_HOST'],
        port=source_credential['DB_PORT']
    )

# Load environment variables for destination database connection
destination_credential = dotenv_values('.env.prod')

def get_destination_db_connection():
    return psycopg2.connect(
        dbname=destination_credential['DB_NAME'],
        user=destination_credential['DB_USER'],
        password=destination_credential['DB_PASSWORD'],
        host=destination_credential['DB_HOST'],
        port=destination_credential['DB_PORT']
    )

def copy_cctv_images():
    # Connect to source and destination databases
    source_conn = get_source_db_connection()
    if source_conn:
        print("Connected to source database")

    dest_conn = get_destination_db_connection()
    if dest_conn:
        print("Connected to destination database")

    try:
        source_cursor = source_conn.cursor()
        dest_cursor = dest_conn.cursor()

        # Fetch all data from the source table
        source_cursor.execute('SELECT Cam_ID, Image_data, Captured_at FROM cctv_images')
        rows = source_cursor.fetchall()
        print(f"Number of rows fetched: {len(rows)}")

        # Insert data into the destination table
        insert_query = '''
            INSERT INTO cctv_images (Cam_ID, Image_data, Captured_at)
            VALUES (%s, %s, %s)
        '''
        for row in rows:
            print(f"Inserting row: {row}")
            dest_cursor.execute(insert_query, row)

        # Commit the transaction
        dest_conn.commit()
        print("Transaction committed to the destination database.")

    except Exception as e:
        print(f"An error occurred: {e}")
        dest_conn.rollback()

    finally:
        # Close all connections
        source_cursor.close()
        dest_cursor.close()
        source_conn.close()
        dest_conn.close()

if __name__ == "__main__":
    copy_cctv_images()
