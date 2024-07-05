import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

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

def image_to_binary(image_input):
    if isinstance(image_input, bytes):
        # If image_input is already in bytes, return it directly
        return psycopg2.Binary(image_input)
    elif isinstance(image_input, str):
        # If image_input is a string (file path), read the file and return the binary data
        with open(image_input, 'rb') as file:
            return psycopg2.Binary(file.read())
    else:
        raise ValueError("Invalid input type for image_to_binary function.")


def binary_to_image(binary_data, output_path):
    with open(output_path, 'wb') as file:
        file.write(binary_data)

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
        print(f"Error: {error}")

def delete_image(img_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM CCTV_images WHERE Img_ID = %s", (img_id,))

        conn.commit()
        cur.close()
        conn.close()
        print("Image deleted successfully")

    except Exception as error:
        print(f"Error: {error}")

# def edit_image(img_id, new_image_input=None, new_captured_at=None):
#     try:
#         conn = get_db_connection()
#         cur = conn.cursor()

#         if new_image_input:
#             binary_data = image_to_binary(new_image_input)
#             cur.execute("UPDATE CCTV_images SET Image_data = %s WHERE Img_ID = %s", (binary_data, img_id))

#         if new_captured_at:
#             cur.execute("UPDATE CCTV_images SET Captured_at = %s WHERE Img_ID = %s", (new_captured_at, img_id))

#         conn.commit()
#         cur.close()
#         conn.close()
#         print("Image updated successfully")

#     except Exception as error:
#         print(f"Error: {error}")

def retrieve_image(img_id, output_path):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT Image_data FROM CCTV_images WHERE Img_ID = %s", (img_id,))
        binary_data = cur.fetchone()[0]

        binary_to_image(binary_data, output_path)

        cur.close()
        conn.close()
        print("Image retrieved and saved successfully")

    except Exception as error:
        print(f"Error: {error}")

def get_cam_ids():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Query to get all Cam_IDs from CCTV_locations
        query = "SELECT Cam_ID FROM CCTV_locations"

        # Execute the query
        cur.execute(query)

        # Fetch all results and store Cam_IDs in a list
        cam_ids = [row[0] for row in cur.fetchall()]

        # Close the cursor and the connection
        cur.close()
        conn.close()

        return cam_ids
    
    except Exception as error:
            print(f"Error: {error}")



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
    # cam_ids_list = get_cam_ids()
    # print(cam_ids_list)