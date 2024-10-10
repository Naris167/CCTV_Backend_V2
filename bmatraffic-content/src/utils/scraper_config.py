config = {
    # Image Capture Settings
    'img_per_cam': 1,  # Number of images to scrape per camera

    # Timing Settings
    'sleep_after_connect': 1,  # Waiting time (in seconds) after obtaining the session ID
    'sleep_between_download': 1,  # Waiting time (in seconds) between each image download

    # Storage Settings
    'json_path': "./images_new/",
    'save_path': "./images_new/",  # Directory path to save images when 'save_to_db' is set to False
    'save_to_db': True,  # Set to True to save images to the database

    # Image Quality Settings
    'img_size': 5120,  # Minimum acceptable image size in bytes (images smaller than this will be skipped)

    # Multi-threading Settings
    'max_workers': 2,  # Maximum number of concurrent connections to scrape images (applicable in multi-threading mode)
}

