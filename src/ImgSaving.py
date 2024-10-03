from datetime import datetime
import os
from utils.Database import insert_data
from utils.log_config import logger
from utils.scraper_config import config


def save_image_to_file(camera_id: int, image_data: bytes) -> bool:
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"camera_{camera_id}_{current_time}.jpg"
    full_path = os.path.join(config['save_path'], filename)
    try:
        with open(full_path, 'wb') as f:
            f.write(image_data)
        logger.info(f"Image saved as {full_path}")
        return True
    except IOError as e:
        logger.error(f"Error saving image: {e}")
        return False


def save_image_to_db(camera_id: int, image_data: bytes) -> bool:
    table = 'cctv_images'
    columns = ['cam_id', 'image_data', 'captured_at']
    data_to_insert = [(camera_id, image_data, datetime.now())]
    insert_data(table, columns, data_to_insert)
    return True