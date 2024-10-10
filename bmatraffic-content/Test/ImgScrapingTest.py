import requests
from PIL import Image
from io import BytesIO
import time
from bs4 import BeautifulSoup

def fetch_and_save_image(camera_id):
    session = requests.Session()
    base_url = f"http://www.bmatraffic.com/PlayVideo.aspx?ID={camera_id}"
    response = session.get(base_url)
    
    if response.status_code == 200:
        for _ in range(4):  # Try fetching the image 4 times
            # Parse the HTML response
            soup = BeautifulSoup(response.text, 'html.parser')
            img_tag = soup.find('img', {'id': 'webcamera'})
            
            if img_tag and 'src' in img_tag.attrs:
                image_url = img_tag['src']
                if not image_url.startswith('http'):
                    image_url = f"http://www.bmatraffic.com/{image_url}"
                
                # Fetch the image
                image_response = session.get(image_url)
                if image_response.status_code == 200:
                    # Convert the response content to an image
                    image = Image.open(BytesIO(image_response.content))
                    # Save the image locally
                    image.save(f"camera_{camera_id}_{int(time.time())}.jpg")
                    print(f"Image from camera {camera_id} saved successfully.")
                else:
                    print(f"Failed to fetch image from camera {camera_id}. HTTP Status Code: {image_response.status_code}")
            else:
                print(f"Failed to find the image URL in the HTML response for camera {camera_id}.")
            
            time.sleep(1)  # Wait for 1 second before fetching the next image
    else:
        print(f"Failed to load the page for camera {camera_id}. HTTP Status Code: {response.status_code}")

# Fetch and save image from camera with ID 7
fetch_and_save_image("7")
