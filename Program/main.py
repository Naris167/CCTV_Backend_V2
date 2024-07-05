import concurrent.futures
from ImgScraping import scrape
from Database import get_cam_ids
from progress_gui import ProgressGUI

# Configuration
camera_ids = get_cam_ids()      # List of camera IDs from DB
img_per_cam = 1                 # How many images to scrape per camera
sleep_after_connect = 1         # Waiting time after getting session ID
sleep_between_download = 1      # Waiting time between each image download
save_path = "./Images/"         # Save path when save_to_db is set to False
save_to_db = False              # Set to True to save images to the database
img_size = 5120                 # Check for the image size that is less than 5KB (skipping failed images)
multi_threading = True          # For scraping more than 3-4 images per camera, it's recommended to enable this. If scraping fewer than 3-4 images, it's better to disable this for improved time efficiency.
max_workers = 10                # Number of concurrent connection to scrape images
# camera_ids = [7, 11, 1639, 603, 1223]  # Example list of camera IDs

# Create a ProgressGUI instance
progress_gui = ProgressGUI(total_tasks=len(camera_ids))

# Function to scrape for a specific camera ID
def scrape_camera(camera_id):
    scrape(camera_id, img_per_cam, sleep_after_connect, sleep_between_download, save_path, save_to_db, img_size)
    progress_gui.increment_progress()

# Run the scraping tasks with ThreadPoolExecutor
def run_scraping_tasks():
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks to the executor
        futures = [executor.submit(scrape_camera, camera_id) for camera_id in camera_ids]
        # Wait for all task to complete
        concurrent.futures.wait(futures)
    # Close the progress bar after all task finished
    progress_gui.quit()

# Start the progress GUI and run the scraping tasks
progress_gui.run(run_scraping_tasks, ())