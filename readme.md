# CCTV API Backend

A backend service that provides optimized access to public CCTV streaming metadata. This project focuses on complex data validation and preparation to ensure minimal errors and reduced waiting times for end users.

## Features

- Real-time CCTV metadata processing and validation
- Fast and efficient image scraping with multi-threading
- Automated session management
- Complex data validation and preparation
- Optimized user experience with reduced waiting times

## Prerequisites

Before running this project, make sure you have the following installed:

- [Bun](https://bun.sh/) for running the server
- Python for data processing scripts
- PostgreSQL database

## Installation

1. Install Bun globally:
```bash
npm install -g bun
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the root directory with your database configuration:

```env
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=[your password]
DB_HOST=localhost
DB_PORT=5432
```

**Note**: Make sure to update the database configuration file path in `src/utils/database.py` to match your environment file location.

## Project Components

### 1. Session Management (`sessionID.py`)
- Periodically called by the server to update and validate CCTV information
- Generates JSON output for server consumption
- Ensures data consistency and availability

### 2. Image Scraping (`imageScraper.py`)
- Implements multi-threading and multi-processing for efficient image scraping
- Includes basic image validation and checking
- Optimized for immediate use of scraped images
- Outputs processed and validated images

## Running the Server

To start the server, run:
```bash
bun run ./src/server_main.js
```

## Primary Project Structure

```
├── src/
│   ├── server_main.js      # Main server file
│   ├── utils/
│   │   └── database.py     # Database configuration
│   ├── sessionID.py        # Session management script
│   ├── imageScraper.py     # Image scraping script
│   ├── requirements.txt    # Python dependencies
└── .env                    # Environment configuration
```

## Database Configuration

The project requires a PostgreSQL database connection. Ensure your `.env` file contains the correct database credentials and the database is properly configured before running the server.

## Contributing

If you'd like to contribute to this project, please make sure to:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request
