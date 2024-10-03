import logging
import os
import sys
from datetime import datetime

# Custom StreamHandler to support encoding
class CustomStreamHandler(logging.StreamHandler):
    def __init__(self, stream=None, encoding=None):
        super().__init__(stream)
        self.encoding = encoding

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            if hasattr(self, 'encoding') and self.encoding:
                stream.write(msg.encode(self.encoding, errors="replace").decode(self.encoding) + self.terminator)
            else:
                stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

# Initialize and configure the logger
logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

# Logging configuration
def log_setup():
    global logger  # Make sure to refer to the global logger
    
    # Define the directory and log file path
    log_directory = "./logs/GeneralCamLogs"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"{log_directory}/GeneralCamInfo_{timestamp}.log"

    # Check if the directory exists, if not, create it
    if not os.path.exists(log_directory):
        os.makedirs(log_directory, exist_ok=True)

    # Create handlers with UTF-8 encoding
    stdout_handler = CustomStreamHandler(sys.stdout, encoding='utf-8')
    stderr_handler = CustomStreamHandler(sys.stderr, encoding='utf-8')
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')

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
