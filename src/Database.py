import psycopg2
import os
from dotenv import load_dotenv
from utils import image_to_binary, binary_to_image


# Load environment variables from .env file
load_dotenv('.env.local')

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


def add_image(cam_id, image_input, captured_at):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        binary_data = image_to_binary(image_input)

        cur.execute(
            "INSERT INTO CCTV_images (Cam_ID, Image_data, Captured_at) VALUES (%s, %s, %s)",
            (cam_id, binary_data, captured_at)
        )

        conn.commit()
        cur.close()
        conn.close()
        # print("Image added successfully")

    except Exception as error:
        print(f"[DATABASE] Error: {error}")


def delete_image(img_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM CCTV_images WHERE Img_ID = %s", (img_id,))

        conn.commit()
        cur.close()
        conn.close()
        print("[DATABASE] Image deleted successfully")

    except Exception as error:
        print(f"[DATABASE] Error: {error}")


def retrieve_images(cam_id, start_date_time, end_date_time, output_path):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Fetch image data and captured_at timestamp from the database
        cur.execute("""
            SELECT Img_ID, Image_data, Captured_at 
            FROM cctv_images 
            WHERE Cam_ID = %s AND Captured_at BETWEEN %s AND %s
        """, (cam_id, start_date_time, end_date_time))

        results = cur.fetchall()

        if not results:
            print(f"[DATABASE] No images found for camera ID {cam_id} within the specified time range")
            return

        for result in results:
            img_id, binary_data, captured_at = result

            # Format the filename
            current_time = captured_at.strftime("%Y%m%d_%H%M%S")
            filename = f"camera_{cam_id}_{current_time}.jpg"
            full_path = os.path.join(output_path, filename)

            # Save the binary data to an image file
            binary_to_image(binary_data, full_path)

        cur.close()
        conn.close()
        print("[DATABASE] Images retrieved and saved successfully")

    except Exception as e:
        print(f"[DATABASE] Error: {e}")


def add_camRecord(camera_data):
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
            print(f"[DATABASE] {new_cameras_count} new cameras were added to the database.\n")
        else:
            print("[DATABASE] No new cameras were added to the database.\n")

    except Exception as e:
        print(f"[DATABASE] An error occurred: {e}\n")


def retrieve_camID_DB():
    #Return list of camID
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Query to get all Cam_IDs from CCTV_locations
        query = "SELECT Cam_ID FROM cctv_locations_preprocessing"

        # Execute the query
        cur.execute(query)

        # Fetch all results and store Cam_IDs in a list
        cam_ids = [row[0] for row in cur.fetchall()]

        # Close the cursor and the connection
        cur.close()
        conn.close()

        return cam_ids
    
    except Exception as error:
            print(f"[DATABASE] Error: {error}")


def update_camCluster(clustered_data):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # SQL command to update the Cam_Group based on Cam_ID
        update_query = "UPDATE cctv_locations_preprocessing SET Cam_Group = %s WHERE Cam_ID = %s"

        # Iterate over each camera in the clustered_data
        for cam_id, label, lat, lon in clustered_data:
            cur.execute(update_query, (str(label), int(cam_id)))
            
            # Check if the update was successful or not
            if cur.rowcount == 0:
                print(f"[DATABASE] Cannot update cluster for Cam[{cam_id}]. Record not found in the database.")

        # Commit the changes to the database
        conn.commit()

    except Exception as e:
        print(f"[DATABASE] Error: {e}")
    finally:
        # Close the cursor and connection
        cur.close()
        conn.close()


def retrieve_camLocation():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Query to retrieve Cam_ID, Latitude, and Longitude
        query = "SELECT Cam_ID, Latitude, Longitude FROM cctv_locations_preprocessing"

        # Execute the query
        cur.execute(query)

        # Fetch all results
        cam_locations = cur.fetchall()  # This will return a list of tuples

        # Close the cursor and connection
        cur.close()
        conn.close()

        return cam_locations
    
    except Exception as e:
        print(f"[DATABASE] Error: {e}")
        return []


# Example Usage
    # Add an image
    # add_image(7, ".\\Images\\image1.jpg", datetime.now())

    # Delete an image by ID
    # delete_image(1)

    # Edit an image by ID (either update the image data or the captured time or both)
    # edit_image(1, new_image_path='new_path_to_image.jpg', new_captured_at=datetime.now())

    # Retrieve an image by ID
    # retrieve_image(1, '.\\retrieved_image.jpg')

    # Get Cam_ID
    # cam_ids_list = get_cam_ids_from_db()
    # print(cam_ids_list)



# retrieve_images(11, '2024-07-01 00:00:00', '2024-07-23 00:00:00', "./images/New folder (5)/")