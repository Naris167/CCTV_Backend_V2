# Image Scraping from BMATraffic CCTV

This project scrapes images from the [BMATraffic CCTV website](http://www.bmatraffic.com) and stores them in a database. It utilizes Python scripts for data processing, image scraping, and database interactions. The project is organized into several directories and files, each serving a specific purpose.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Image Scraping Process](#image-scraping-process)
4. [Usage](#usage)
5. [Files and Directories](#files-and-directories)

## Prerequisites

Before you begin, ensure you have met the following requirements:

- You have installed Python 3.12.4 and pip.
- You have a PostgreSQL database setup.
- You have access to the [BMATraffic CCTV website](http://www.bmatraffic.com).

## Installation

### Install and Setup

1. Clone this repository:

```bash
git https://github.com/Naris167/bmatraffic_cctv_scraping.git
```

2. Go to root directory of the project and run the following command to install the required libraries:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file and add your database credentials:

```
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=your_db_port
```

4. Ensure your PostgreSQL database is running and accessible.

## How this Script Work?

1. Connect to [BMATraffic](http://www.bmatraffic.com) to obtain a session ID.
2. Request a specific video with the camera ID and session ID.
3. Download the streaming images from the backend of BMATraffic based on the requested camera ID.

## Usage

The configuration for the scraping process is set in `main.py`. Key settings include:

- **Camera Settings**: List of camera IDs and the number of images to scrape per camera.
- **Timing Settings**: Delays between connections and image downloads.
- **Storage Settings**: Directory path for saving images or saving images to the database.
- **Image Quality Settings**: Minimum acceptable image size in bytes.
- **Mode Settings**: Multi-threading options and session ID refresh intervals.

Example configuration in `main.py`:

```python
# Camera Settings
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
```

> **Warning:** ⚠️ 
> Setting the `max_workers` too high might result in an IP ban from the server. Use multi-threading with caution and consider the server's capacity and policies.

To run the scraping tasks, execute:

```bash
python src/main.py
```

## Files and Directories
- `.env`: Stores database credentials.
- `requirements.txt`: Lists the required libraries for the project.
- **data/**: Information about the CCTV camera stored in Excel file
  - `locations.xlsx`: Excel file containing CCTV location information.
- **script/**: Contains utility scripts for data conversion, neighborhood finding, and database insertion.
  - `ConvertDataToExcel.py`: Converts JSON data to Excel format.
  - `FindNeighborhood.py`: Finds cameras near each other using latitude and longitude.
  - `InsertDataToDB.py`: Inserts data from the Excel file into the database.
- **src/**: Contains the core scripts for database interactions and image scraping.
  - `Database.py`: Manages database connections and operations.
  - `ImgScraping.py`: Handles image scraping logic.
  - `main.py`: Configures and initiates the scraping process.
  - `progress_gui.py`: Provides a GUI for tracking scraping progress.
- **test/**: Contains test scripts, including `prototype.py`, the basic image scraping script.

## Database Structure

```sql
-- Create the cctv_locations_preprocessing table
CREATE TABLE cctv_locations_preprocessing (
    Cam_ID INT PRIMARY KEY NOT NULL,
    Cam_Code VARCHAR(50),
	Cam_Group VARCHAR(50),
    Status VARCHAR(255),
    Cam_Name TEXT,
    Cam_Name_e TEXT,
    Cam_Location TEXT,
    Cam_Direction TEXT,
    Latitude DOUBLE PRECISION,
    Longitude DOUBLE PRECISION,
    IP VARCHAR(50),
    Icon VARCHAR(100)
);

-- Create the CCTV_images table with a foreign key to CCTV_locations
CREATE TABLE cctv_images (
    Img_ID SERIAL PRIMARY KEY NOT NULL,
    Cam_ID INT NOT NULL REFERENCES cctv_locations_preprocessing(Cam_ID),
    Image_data BYTEA,
    Captured_at TIMESTAMP
);
```