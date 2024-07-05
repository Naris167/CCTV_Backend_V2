import concurrent.futures
from ImgScraping import scrape

# Configuration
camera_ids = [7, 11, 1639, 603, 1223]  # Example list of camera IDs; replace with your actual list
loops = 10  # How many images to scrape per camera
save_path = "./Images/"  # Change this to your desired save path
sleep_after_connect = 1  # Waiting time after getting session ID
sleep_between_download = 1  # Waiting time between each image download

# Function to scrape for a specific camera ID
def scrape_camera(camera_id):
    scrape(camera_id, loops, sleep_after_connect, sleep_between_download, save_path)

# Create a ThreadPoolExecutor
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:  # Adjust max_workers based on your requirements
    # Submit tasks to the executor
    futures = [executor.submit(scrape_camera, camera_id) for camera_id in camera_ids]

    # Ensure all futures are completed
    concurrent.futures.wait(futures)

print("Main thread continuing to run")
