import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('.env.prod')

# Verify environment variables
# print(f"DB_NAME: {os.getenv('DB_NAME')}")
# print(f"DB_USER: {os.getenv('DB_USER')}")
# print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')}")
# print(f"DB_HOST: {os.getenv('DB_HOST')}")
# print(f"DB_PORT: {os.getenv('DB_PORT')}")

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )


# Define the function to import data from Excel to the database
def import_excel_to_db(excel_file_path):
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file_path)

        # Connect to the database
        conn = get_db_connection()
        cur = conn.cursor()

        # Iterate over the rows of the dataframe and insert each row into the database
        for index, row in df.iterrows():
            cur.execute("""
                INSERT INTO cctv_locations_preprocessing (Cam_ID, Cam_Code, Cam_Group, Status, Cam_Name, Cam_Name_e, Cam_Location, Cam_Direction, Latitude, Longitude, IP, Icon)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                row['Cam_ID'],
                row['Cam_Code'],
                row['Group'],
                row['Status'],
                row['Cam_Name'],
                row['Cam_Name_e'],
                row['Cam_Location'],
                row['Cam_Direction'],
                row['Latitude'],
                row['Longitude'],
                row['IP'],
                row['Icon']
            ))

        # Commit the transaction
        conn.commit()

        # Close the cursor and connection
        cur.close()
        conn.close()

        print("Data imported successfully")

    except Exception as error:
        print(f"Error: {error}")

# Path to your Excel file
excel_file_path = "Data/locationForDB-2.xlsx"

# Import the data
import_excel_to_db(excel_file_path)
