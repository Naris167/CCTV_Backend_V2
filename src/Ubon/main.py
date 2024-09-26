import time
import os
from typing import List, Tuple, Set, Dict
from io import BytesIO
from GetCCTVList import getCamList, get_m3u8_info, get_media_info
from utils import sort_key
from database import add_camRecord
from log_config import logger, log_setup
import requests

def fetch_and_sort_cctv_list(url: str) -> List[Tuple]:
    cctv_list = getCamList(url)
    return sorted(cctv_list, key=lambda x: sort_key(x[0]))

def download_ts_file(cctv_id: str, file_name: str) -> bytes:
    url = f"http://183.88.214.137:1935/livecctv/{cctv_id}.stream/{file_name}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        logger.error(f"Failed to download {file_name}. Status code: {response.status_code}")
        return b''

def save_concatenated_file(cctv_id: str, buffer: BytesIO, start_time: float):
    duration = time.time() - start_time
    file_name = f"{cctv_id}_{int(start_time)}_{int(duration)}s.ts"
    with open(file_name, 'wb') as f:
        f.write(buffer.getvalue())
    logger.info(f"Saved concatenated file: {file_name}")

def monitor_cctv(cctv_id: str, duration: int = 60):
    playlist = get_m3u8_info(cctv_id)
    if not playlist:
        logger.error(f"Failed to get playlist for CCTV ID: {cctv_id}")
        return

    current_m3u8 = playlist[0]
    logger.info(f"Current M3U8: {current_m3u8}")

    downloaded_files: Set[str] = set()
    buffer = BytesIO()
    start_time = time.time()

    while time.time() - start_time < duration:
        media_info = get_media_info(cctv_id, current_m3u8)
        if not media_info or len(media_info) < 5:
            logger.error(f"Failed to get valid media info for CCTV ID: {cctv_id}")
            time.sleep(1)  # Wait a bit before retrying
            continue

        logger.info(f"Media info: {media_info}")

        # Check and download up to two available media files
        for i in range(4, min(6, len(media_info))):
            media_file = media_info[i][1]
            if media_file not in downloaded_files:
                logger.info(f"Downloading new file: {media_file}")
                file_content = download_ts_file(cctv_id, media_file)
                if file_content:
                    buffer.write(file_content)
                    downloaded_files.add(media_file)
            else:
                logger.info(f"File already downloaded: {media_file}")

        # Calculate time to wait before next check
        next_segment_time = float(media_info[4][0])  # Duration of the first segment
        current_time = time.time()
        elapsed_time = current_time - start_time
        time_to_wait = next_segment_time - (elapsed_time % next_segment_time)

        logger.info(f"Waiting {time_to_wait:.2f} seconds before next check")
        time.sleep(max(0.1, time_to_wait))  # Ensure we wait at least 0.1 seconds

    # Save the concatenated file after the monitoring duration
    save_concatenated_file(cctv_id, buffer, start_time)

def main():
    log_setup()
    logger.info("[MAIN] Application started...")

    url = "http://183.88.214.137:8000/cctvList.js"
    cctv_list = fetch_and_sort_cctv_list(url)

    # Uncomment the following lines if you want to print the CCTV list or add it to the database
    # for cctv in cctv_list:
    #     print(cctv)
    add_camRecord(cctv_list)

    cctv_id = "cctvp2c003"
    # monitor_cctv(cctv_id)

if __name__ == "__main__":
    main()