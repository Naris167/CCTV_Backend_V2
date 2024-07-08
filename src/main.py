import concurrent.futures
from ImgScraping import scrape, scrape_sequential
from Database import get_cam_ids
from progress_gui import ProgressGUI

# Configuration

# Camera Settings
# camera_ids = [7, 11, 1639, 603, 1223]  # Example list of camera IDs
camera_ids = get_cam_ids()       # List of camera IDs from the database
img_per_cam = 1                  # Number of images to scrape per camera

# Timing Settings
sleep_after_connect = 1          # Waiting time (in seconds) after obtaining the session ID
sleep_between_download = 1       # Waiting time (in seconds) between each image download

# Storage Settings
save_path = "./images/"          # Directory path to save images when 'save_to_db' is set to False
save_to_db = False               # Set to True to save images to the database

# Image Quality Settings
img_size = 5120                  # Minimum acceptable image size in bytes (images smaller than this will be skipped)

# Mode Settings
multi_threading = False          # Enable multi-threading for scraping (recommended for >3-4 images per camera)
refresh_interval = 100           # Number of images scraped before refreshing the session ID (applicable in sequential mode)

# Multi-threading Settings
max_workers = 2                  # Maximum number of concurrent connections to scrape images (applicable in multi-threading mode)

# Create a ProgressGUI instance
progress_gui = ProgressGUI(total_tasks=len(camera_ids))

# Function to scrape for a specific camera ID
def scrape_camera(camera_id):
    scrape(camera_id, img_per_cam, sleep_after_connect, sleep_between_download, save_path, save_to_db, img_size)
    progress_gui.increment_progress()

def scrape_sequential_mode(camera_ids):
    scrape_sequential(camera_ids, img_per_cam, sleep_after_connect, sleep_between_download, save_path, save_to_db, img_size, refresh_interval, progress_gui)
    progress_gui.quit()

# Run the scraping tasks with ThreadPoolExecutor
def run_scraping_tasks():
    if multi_threading:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tasks to the executor
            futures = [executor.submit(scrape_camera, camera_id) for camera_id in camera_ids]
            # Wait for all tasks to complete
            concurrent.futures.wait(futures)
        # Close the progress bar after all tasks are finished
        progress_gui.quit()
    else:
        # Run sequential scraping
        scrape_sequential_mode(camera_ids)

# Start the progress GUI and run the scraping tasks
progress_gui.run(run_scraping_tasks, ())
