import requests
from datetime import datetime
from requests.auth import HTTPDigestAuth
import re

def capture_cctv_image():
    url = "http://118.174.138.142:1031/stw-cgi/video.cgi?msubmenu=stream&action=view&Profile=1" 

    auth = HTTPDigestAuth('user7', 'rangsit1031') # This must be metch with the port number

    try:
        response = requests.get(url, stream=True, auth=auth, verify=False)
        response.raise_for_status()

        # Pattern to find the start of JPEG image in MJPEG stream
        pattern = b'\xff\xd8\xff'
        
        buffer = b''
        for chunk in response.iter_content(chunk_size=1024):
            buffer += chunk
            start_index = buffer.find(pattern)
            if start_index != -1:
                # Found the start of an image
                buffer = buffer[start_index:]
                end_index = buffer.find(pattern, len(pattern))
                if end_index != -1:
                    # Found the start of the next image, so we have a complete frame
                    image_data = buffer[:end_index]
                    
                    # Generate a filename with current timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"cctv_capture_{timestamp}.jpg"

                    # Save the image
                    with open(filename, 'wb') as f:
                        f.write(image_data)

                    print(f"Image saved as {filename}")
                    break
                
        if not filename:
            print("Failed to capture a complete image frame")

    except requests.exceptions.RequestException as e:
        print(f"Error capturing image: {e}")

if __name__ == "__main__":
    capture_cctv_image()