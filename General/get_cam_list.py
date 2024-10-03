import re
import requests
import os
from utils.log_config import logger
from typing import Optional, Tuple, List, Union
import json
from utils import sort_key

def getCamList_Ubon() -> List[Tuple[str, str, float, float, str, str]]:
    url = "http://183.88.214.137:8000/cctvList.js"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses

        # Get the content of the response
        content = response.text
        
        # Define the regex pattern to extract the required fields
        pattern = r'"name":\s*"([^"]+)",\s*"streamId":\s*"([^"]+)",\s*"lat":\s*"([^"]+)",\s*"lng":\s*"([^"]+)"'
        
        # Find all matches in the content
        matches = re.findall(pattern, content)
        
        # Process the extracted information
        cctv_list = [
            (
                streamId,
                re.sub(r'\s+', ' ', name.replace("\\n", " ").strip()),
                float(lat),
                float(lng),
                "HLS",
                f"http://183.88.214.137:1935/livecctv/{streamId}.stream/playlist.m3u8"
            ) 
            for name, streamId, lat, lng in matches
        ]
        
        # Sort the list based on streamId
        cctv_list = sorted(cctv_list, key=lambda x: sort_key(x[0]))
        return cctv_list

    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []
    except ValueError as e:
        print(f"Error converting data: {e}")
        return []




def getCamList_iTic() -> List[Tuple[str, str, float, float, str, str,
                                    Union[str, None], Union[str, None], Union[str, None], Union[str, None],
                                    Union[str, None], Union[str, None], Union[str, None], Union[str, None],
                                    Union[bool, None], Union[bool, None]]]:
    url = "https://camera.longdo.com/feed/?command=json&callback=longdo.callback.cameras"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Extract JSON data from the response
        json_data = response.text.strip("longdo.callback.cameras(").rstrip(");")
        data = json.loads(json_data)
        
        result = []
        for camera in data:
            hls_url = camera.get("hls_url", "")
            stream_method = "HLS" if hls_url and hls_url.endswith(".m3u8") else "UNKNOWN"
            
            result.append((
                camera.get("camid", "") or "",
                camera.get("title", "") or "",
                float(camera.get("latitude", 0) or 0),
                float(camera.get("longitude", 0) or 0),
                stream_method,
                hls_url or "",
                camera.get("link", "") or "",
                camera.get("vdourl", "") or "",
                camera.get("imgurl", "") or "",
                camera.get("imgurl_specific", "") or "",
                camera.get("overlay_file", "") or "",
                camera.get("organization", "") or "",
                camera.get("sponsertext", "") or "",
                camera.get("lastupdate", "") or "",
                camera.get("incity", "N") == "Y",
                camera.get("motion", "N") == "Y"
            ))
        
        result = sorted(result, key=lambda x: sort_key(x[0]))
        return result
    
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON data: {e}")
        return []
    except KeyError as e:
        print(f"Missing key in JSON data: {e}")
        return []
    except ValueError as e:
        print(f"Error converting data: {e}")
        return []