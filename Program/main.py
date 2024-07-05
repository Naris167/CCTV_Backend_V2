import concurrent.futures
from ImgScraping import scrape
from Database import get_cam_ids

# Configuration
camera_ids = get_cam_ids()              # List of camera IDs from DB
loops = 5                              # How many images to scrape per camera
sleep_after_connect = 1                 # Waiting time after getting session ID
sleep_between_download = 1              # Waiting time between each image download
save_path = "./Images/"                 # Save path when `save_to_db` is set to False
save_to_db = True                       # Set to True to save images to the database
img_size = 10240                        # Check if the image size is less than 10KB (skipping failed images)
max_workers = 5                         # Number of concurrent connection to scrape images
# camera_ids = [7, 11, 1639, 603, 1223]   # Example list of camera IDs



# Function to scrape for a specific camera ID
def scrape_camera(camera_id):
    scrape(camera_id, loops, sleep_after_connect, sleep_between_download, save_path, save_to_db, img_size)

# Create a ThreadPoolExecutor
with concurrent.futures.ThreadPoolExecutor(max_workers) as executor:
    # Submit tasks to the executor
    futures = [executor.submit(scrape_camera, camera_id) for camera_id in camera_ids]

    # Ensure all futures are completed
    concurrent.futures.wait(futures)

print("Main thread continuing to run")
