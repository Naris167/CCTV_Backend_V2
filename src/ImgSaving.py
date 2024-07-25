from datetime import datetime
import os
from Database import add_image


def save_image_to_file(camera_id: int, image_data: bytes, save_path: str) -> bool:
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"camera_{camera_id}_{current_time}.jpg"
    full_path = os.path.join(save_path, filename)
    try:
        with open(full_path, 'wb') as f:
            f.write(image_data)
        print(f"Image saved as {full_path}")
        return True
    except IOError as e:
        print(f"Error saving image: {e}")
        return False


def save_image_to_db(camera_id: int, image_data: bytes) -> bool:
    add_image(camera_id, image_data, datetime.now())
    return True