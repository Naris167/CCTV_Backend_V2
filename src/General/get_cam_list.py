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
    
