global_config = {
    # Image Scraper Setting
    'target_image_count': 1,  # Number of images to scrape per camera
    'download_interval': 4,  # Waiting time (in seconds) between each image download

    # SessionID Scraper Settings
    'json_path': "./cctvSessionTemp/",

    # Golbal Check Setting
    'img_size': 5120,  # Minimum acceptable image size in bytes (images smaller than this will be skipped)
    'max_workers': 80,  # Maximum number of concurrent connections to scrape images (applicable in multi-threading mode)
}

