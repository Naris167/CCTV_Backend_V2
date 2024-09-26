import re
import requests
import os
from log_config import logger
from typing import Optional, Tuple, List

def getCamList(url):
    # Make a GET request to fetch the data
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Get the content of the response
        content = response.text
        
        # Define the regex pattern to extract the required fields
        pattern = r'"name":\s*"([^"]+)",\s*"streamId":\s*"([^"]+)",\s*"lat":\s*"([^"]+)",\s*"lng":\s*"([^"]+)"'
        
        # Find all matches in the content
        matches = re.findall(pattern, content)
        
        # Process the extracted information, remove '\n' and extra spaces in the name
        cctv_list = [
            (streamId, re.sub(r'\s+', ' ', name.replace("\\n", " ").strip()), lat, lng) 
            for name, streamId, lat, lng in matches
        ]
        
        # Return the cleaned data
        return cctv_list
    else:
        logger.info("Failed to retrieve the data. Status code:", response.status_code)
        return []
    

def get_m3u8_info(cctv_id: str) -> Optional[Tuple[str, int, str, str, int]]:
    base_url = f"http://183.88.214.137:1935/livecctv/{cctv_id}.stream/playlist.m3u8"
    
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        content = response.text
    except requests.RequestException as e:
        print(f"Failed to retrieve the playlist: {e}")
        return None

    patterns = {
        'chunklist': r'#EXT-X-STREAM-INF:.*\n(.*\.m3u8)',
        'bandwidth': r'BANDWIDTH=(\d+)',
        'codecs': r'CODECS="([^"]+)"',
        'resolution': r'RESOLUTION=(\d+x\d+)',
        'version': r'#EXT-X-VERSION:(\d+)'
    }

    extracted_info = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        extracted_info[key] = match.group(1) if match else None

    if all(extracted_info.values()):
        return (
            extracted_info['chunklist'],
            int(extracted_info['bandwidth']),
            extracted_info['codecs'],
            extracted_info['resolution'],
            int(extracted_info['version'])
        )
    else:
        print("Failed to extract all required information from the playlist.")
        return None
    



def get_media_info(cctv_id: str, current_m3u8: str) -> Optional[Tuple[int, int, int, int, List[Tuple[float, str]]]]:
    base_url = f"http://183.88.214.137:1935/livecctv/{cctv_id}.stream/{current_m3u8}"
    
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        content = response.text
    except requests.RequestException as e:
        print(f"Failed to retrieve the media file: {e}")
        return None

    patterns = {
        'version': r'#EXT-X-VERSION:(\d+)',
        'target_duration': r'#EXT-X-TARGETDURATION:(\d+)',
        'media_sequence': r'#EXT-X-MEDIA-SEQUENCE:(\d+)',
        'discontinuity_sequence': r'#EXT-X-DISCONTINUITY-SEQUENCE:(\d+)',
        'extinf': r'#EXTINF:([\d.]+),\n(.*\.ts)'
    }

    extracted_info = {}
    for key, pattern in patterns.items():
        if key == 'extinf':
            extracted_info[key] = re.findall(pattern, content)
        else:
            match = re.search(pattern, content)
            extracted_info[key] = int(match.group(1)) if match else None

    if all(extracted_info[key] is not None for key in patterns.keys() if key != 'extinf'):
        extinf_tuples = [(float(duration), file_name) for duration, file_name in extracted_info['extinf']]
        return (
            extracted_info['version'],
            extracted_info['target_duration'],
            extracted_info['media_sequence'],
            extracted_info['discontinuity_sequence'],
            *extinf_tuples
        )
    else:
        print("Failed to extract all required information from the media file.")
        return None



def download_ts_file(cctv_id, current_video, save_path="./src/Ubon/downloads"):
    # Construct the URL
    base_url = f"http://183.88.214.137:1935/livecctv/{cctv_id}.stream/{current_video}"
    
    # Make a GET request to download the .ts file
    response = requests.get(base_url, stream=True)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Ensure the save path directory exists
        os.makedirs(save_path, exist_ok=True)
        
        # Construct the file path to save the .ts file
        file_path = os.path.join(save_path, current_video)
        
        # Save the .ts file in chunks to handle large files
        with open(file_path, "wb") as ts_file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    ts_file.write(chunk)
        
        print(f"Downloaded and saved: {file_path}")
    else:
        print("Failed to download the .ts file. Status code:", response.status_code)