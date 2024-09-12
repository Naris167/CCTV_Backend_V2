import logging
import os
import sys
from datetime import datetime

# Initialize and configure the logger
logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

# Logging configuration
def log_setup():
    global logger  # Make sure to refer to the global logger
    
    # Define the directory and log file path
    log_directory = "./logs"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"{log_directory}/updateCamInfo_{timestamp}.log"

    # Check if the directory exists, if not, create it
    if not os.path.exists(log_directory):
        os.makedirs(log_directory, exist_ok=True)

    # Create handlers
    stdout_handler = logging.StreamHandler(sys.stdout)
    stderr_handler = logging.StreamHandler(sys.stderr)
    file_handler = logging.FileHandler(log_filename)

    # Define custom filters for handlers
    class InfoFilter(logging.Filter):
        def filter(self, record):
            return record.levelno < logging.WARNING  # Only log below WARNING (INFO and below)

    class WarningErrorFilter(logging.Filter):
        def filter(self, record):
            return record.levelno >= logging.WARNING  # Only log WARNING and above

    # Set levels for handlers
    stdout_handler.setLevel(logging.DEBUG)  # All levels go to stdout but filtered
    stderr_handler.setLevel(logging.WARNING)  # WARNING and above go to stderr
    file_handler.setLevel(logging.DEBUG)  # All levels go to file

    # Assign filters to handlers
    stdout_handler.addFilter(InfoFilter())
    stderr_handler.addFilter(WarningErrorFilter())

    # Create formatters and add them to handlers
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    stdout_handler.setFormatter(formatter)
    stderr_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Clear existing handlers, if any, to prevent duplication
    if logger.hasHandlers():
        logger.handlers.clear()

    # Add handlers to the logger
    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)
    logger.addHandler(file_handler)

    # Avoid duplicate logs
    logger.propagate = False

    # Example log message to confirm setup
    logger.info("[MAIN] Logging setup completed!")
