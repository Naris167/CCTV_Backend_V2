import logging
import os
import sys
from datetime import datetime
import errno

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
def log_setup(log_directory: str, log_name: str):
    global logger  # Make sure to refer to the global logger
    
    # Define the directory and log file path
    # log_directory = "./logs/CameraScraper"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"{log_directory}/{log_name}_{timestamp}.log"
    # log_filename = f"{log_directory}/CameraScraper_{timestamp}.log"

    # Check if the directory exists, if not, create it
    try:
        isDirExist(log_directory)
    except Exception as e:
        print(f"Error: {e}")
        return

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


def isDirExist(directory: str):
    try:
        # Check if the directory exists
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # Check if the directory is writable
        test_file = os.path.join(directory, 'test_write.tmp')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except IOError as e:
            raise IOError(f"Directory {directory} is not writable: {e}")
        
        print(f"Directory {directory} exists and is writable.")
        return True
    
    except PermissionError:
        raise PermissionError(f"No permission to create or write to directory: {directory}")
    except OSError as e:
        if e.errno == errno.ENOSPC:
            raise OSError(f"No space left on device to create directory: {directory}")
        elif e.errno == errno.ENAMETOOLONG:
            raise OSError(f"File name too long: {directory}")
        else:
            raise OSError(f"Error creating or accessing directory {directory}: {e}")