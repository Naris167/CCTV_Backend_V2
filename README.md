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
camera_ids = startUpdate(170)    # List of online CCTV IDs + update CCTV info in DB + distance in meter for clustering
img_per_cam = 1                  # Number of images to scrape per camera

# Timing Settings
sleep_after_connect = 1          # Waiting time (in seconds) after obtaining the session ID
sleep_between_download = 1       # Waiting time (in seconds) between each image download

# Storage Settings
save_path = "./images/"          # Directory path to save images when 'save_to_db' is set to False
save_to_db = True               # Set to True to save images to the database

# Image Quality Settings
img_size = 5120                  # Minimum acceptable image size in bytes (images smaller than this will be skipped)

# Mode Settings
multi_threading = True          # Enable multi-threading for scraping (recommended for >3-4 images per camera)
refresh_interval = 100           # Number of images scraped before refreshing the session ID (applicable in sequential mode)

# Multi-threading Settings
max_workers = 20                  # Maximum number of concurrent connections to scrape images (applicable in multi-threading mode)
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
  - `GeoCluster.py`: Apply DBSCAN to cluster CCTV location
  - `ImgSaving.py`: Function manage image saving
  - `ImgScraping.py`: Handles image scraping logic.
  - `main.py`: Configures and initiates the scraping process.
  - `progress_gui.py`: Provides a GUI for tracking scraping progress.
  - `updateCamInfo.py`: Managing updating CCTV list process 
  - `utils.py`: Other functions
- **test/**: Contains test scripts, including `prototype.py`, the basic image scraping script.

## Database Structure

```sql
-- Create the cctv_locations_preprocessing table
CREATE TABLE cctv_locations_preprocessing (
   Cam_ID VARCHAR(50) PRIMARY KEY NOT NULL,
   Cam_Code VARCHAR(50),
	Cam_Group VARCHAR(50),
   Cam_Name TEXT,
   Cam_Name_e TEXT,
   Cam_Location TEXT,
   Cam_Direction TEXT,
   Latitude DOUBLE PRECISION,
   Longitude DOUBLE PRECISION,
   IP VARCHAR(50),
   Icon VARCHAR(100),
   Verify BOOLEAN DEFAULT FALSE,
   is_online BOOLEAN DEFAULT FALSE,
   is_flooded BOOLEAN DEFAULT FALSE,
   is_usable BOOLEAN DEFAULT TRUE
);

-- Create the CCTV_images table with a foreign key to CCTV_locations
CREATE TABLE cctv_images (
   Img_ID SERIAL PRIMARY KEY NOT NULL,
   Cam_ID VARCHAR(50) NOT NULL REFERENCES cctv_locations_preprocessing(Cam_ID),
   Image_data BYTEA,
   Captured_at TIMESTAMP
);
```


# Summary of Approach for Converting `eps` Value for DBSCAN

## Purpose:
The script `FindOptimalEPS.py` is used to accurately determine the `eps` value for the DBSCAN clustering algorithm in meters when working with `latitude` and `longitude` coordinates. The conversion method provides a precision of approximately ±1-5 meters for distances less than 2236 meters. This precision value is approximated and can vary slightly depending on the specific coordinates and distances involved.

## Reason for Complexity:
1. **Precision Requirements:** Direct conversion between geographic coordinates (latitude and longitude) and meters requires high precision for accurate clustering in small scale like in the range of 1000 meters.
2. **Brute Force Method:** Simple Euclidean distance formulas and standard conversion factors didn't provide the required precision. Therefore, a brute force method was used to find the most precise `eps` value.
3. **Reason for Not Using Standard Conversion Factors:** Standard methods using approximate conversion factors for latitude (111320.0 meters per degree) and longitude (111320.0 * cos(latitude)) were not accurate enough for the required precision. The brute force method provided a more precise `eps` value by iteratively testing and refining the conversion.

## Steps Taken:

1. **Define Coordinates and Known Distance:**
   - Two specific coordinates (latitude and longitude) were used.
      - Coordinate 1 = 13.769741049467855, 100.57298223507024
      - Coordinate 2 = 13.789905618799368, 100.57434272643398
      - Actual Distance in Km = 2235.799051227861

2. **Brute Force Method to Find `eps`:**
   - Incrementally tested different `eps` values to find the one that correctly separates the given coordinates.
   - Used DBSCAN with the Haversine metric to ensure the clustering result matched the expected output.

3. **Determine Conversion Ratio (Distance Per Degree):**
   - Once the optimal `eps` value was found, the ratio of the actual distance in meters to the `eps` value in degrees was calculated.
   - This ratio, referred to as `distance_per_degree`, is used to convert any distance in meters to the corresponding value in degrees.

4. **Implementation of Conversion Function:**
   - Created a function that converts a distance in meters to degrees using the `distance_per_degree` ratio.
   - Ensured high precision in the calculations using Python’s `decimal` module.

## Key Terms:
- **Optimal `eps` Value:** The precise `eps` value in degrees found through the brute force method that can precisely separate 2 coordinate.
- **Distance Per Degree (Ratio):** The ratio used to convert any distance in meters to degrees, ensuring accurate clustering with DBSCAN.

