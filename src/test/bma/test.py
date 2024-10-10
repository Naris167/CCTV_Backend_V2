import requests
from PIL import Image
from io import BytesIO

# URL of the image to download
image_url = "http://www.bmatraffic.com/show.aspx?image=7&&time=1720080834919"

# Fetch the image
response = requests.get(image_url)
if response.status_code == 200:
    # Convert the response content to an image
    image = Image.open(BytesIO(response.content))
    # Save the image locally
    image.save("downloaded_image.jpg")
    print("Image saved successfully.")
else:
    print(f"Failed to fetch image. HTTP Status Code: {response.status_code}")



