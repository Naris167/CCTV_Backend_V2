import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('.env.prod')

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

        # Iterate over the rows of the dataframe and insert/update each row in the database
        for index, row in df.iterrows():
            # Ensure Cam_ID is treated as a string
            cam_id = str(row['Cam_ID'])

            # Determine Latitude and Longitude from 'Correct' or fallback to 'Latitude' and 'Longitude' columns
            if pd.notna(row['Correct']):
                correct_values = row['Correct'].split(', ')
                latitude = float(correct_values[0])
                longitude = float(correct_values[1])
            else:
                latitude = row['Latitude']
                longitude = row['Longitude']

            verify = bool(row['Verify']) if pd.notna(row['Verify']) else False
            
            # Check if Cam_ID exists in the database
            cur.execute("SELECT 1 FROM cctv_locations_preprocessing WHERE Cam_ID = %s", (cam_id,))
            exists = cur.fetchone()

            if exists:
                # Update existing record
                cur.execute("""
                    UPDATE cctv_locations_preprocessing
                    SET Cam_Code = %s, Cam_Group = %s, Cam_Name = %s, Cam_Name_e = %s, 
                        Cam_Location = %s, Cam_Direction = %s, Latitude = %s, Longitude = %s, 
                        IP = %s, Icon = %s, Verify = %s
                    WHERE Cam_ID = %s
                    """, (
                    row['Cam_Code'],
                    row['Group'],
                    row['Cam_Name'],
                    row['Cam_Name_e'],
                    row['Cam_Location'],
                    row['Cam_Direction'],
                    latitude,
                    longitude,
                    row['IP'],
                    row['Icon'],
                    verify,
                    cam_id
                ))
            else:
                # Insert new record
                cur.execute("""
                    INSERT INTO cctv_locations_preprocessing (Cam_ID, Cam_Code, Cam_Group, Cam_Name, Cam_Name_e, Cam_Location, Cam_Direction, Latitude, Longitude, IP, Icon, Verify)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                    cam_id,
                    row['Cam_Code'],
                    row['Group'],
                    row['Cam_Name'],
                    row['Cam_Name_e'],
                    row['Cam_Location'],
                    row['Cam_Direction'],
                    latitude,
                    longitude,
                    row['IP'],
                    row['Icon'],
                    verify
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
excel_file_path = "Data/cctv_locations_master.xlsx"

# Import the data
import_excel_to_db(excel_file_path)