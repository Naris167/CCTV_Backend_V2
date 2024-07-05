import pandas as pd
import psycopg2

# Define the function to get a database connection
def get_db_connection():
    return psycopg2.connect("dbname=postgres user=postgres password=Pass@1373")

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
                INSERT INTO CCTV_locations (Cam_ID, Cam_Code, Cam_Group, Status, Cam_Name, Cam_Name_e, Cam_Location, Cam_Direction, Latitude, Longitude, IP, Icon)
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
excel_file_path = "C:\\Users\\naris\\Desktop\STIU\\2024-1 Internship\\Gistda\\2024-07-01 Image Scraping\\Data\\locationForDB.xlsx"

# Import the data
import_excel_to_db(excel_file_path)
