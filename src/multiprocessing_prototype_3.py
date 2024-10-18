'''
This implementation has logger that can send logging back to main process
But this one cause a lot of error under high concurrency.
'''

import concurrent.futures
from typing import Callable, List, Tuple, Dict, Any, Optional
from datetime import datetime
import time
import math
import multiprocessing
import logging
from logging.handlers import QueueHandler, QueueListener

# Global variable to hold the cv2 module
cv2 = None

def safe_import_cv2():
    global cv2
    if cv2 is None:
        import cv2 as cv2_imported
        cv2 = cv2_imported

class LoggingProcess(multiprocessing.Process):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def run(self):
        root_logger = logging.getLogger()
        root_logger.handlers = []
        handler = QueueHandler(self.log_queue)
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.DEBUG)
        self.run_process()

    def run_process(self):
        pass

class MultiprocessingImageScraper:
    def __init__(self, logger):
        self.logger = logger
        self.log_queue = multiprocessing.Queue()
        self.queue_listener = QueueListener(self.log_queue, *logger.handlers)

    def start_logging(self):
        self.queue_listener.start()

    def stop_logging(self):
        self.queue_listener.stop()

    class WorkerProcess(LoggingProcess):
        def __init__(self, log_queue, func, camera_id, url, kwargs):
            super().__init__(log_queue)
            self.func = func
            self.camera_id = camera_id
            self.url = url
            self.kwargs = kwargs
            self.result = None

        def run_process(self):
            safe_import_cv2()
            self.result = self.func(self.camera_id, self.url, **self.kwargs)

    def run_multiprocessing(self, func: Callable, 
                            max_concurrent: int,
                            working_cctv: Dict[str, str],
                            **kwargs: Any) -> Dict[str, Any]:
        
        self.start_logging()

        all_results = []
        processes = []

        for camera_id, url in working_cctv.items():
            process = self.WorkerProcess(self.log_queue, func, camera_id, url, kwargs)
            processes.append(process)
            process.start()

            if len(processes) >= max_concurrent:
                for p in processes:
                    p.join()
                    if p.result is not None:
                        all_results.append((p.camera_id, p.result))
                processes = []

        # Handle any remaining processes
        for p in processes:
            p.join()
            if p.result is not None:
                all_results.append((p.camera_id, p.result))

        image_result = []
        updated_working_cctv = {}
        unresponsive_cctv = {}

        for camera_id, result in all_results:
            if result is not None:
                image_result.append(result)
                updated_working_cctv[camera_id] = working_cctv[camera_id]
            else:
                unresponsive_cctv[camera_id] = working_cctv[camera_id]

        self.stop_logging()

        return {
            "image_result": image_result,
            "working_cctv": updated_working_cctv,
            "unresponsive_cctv": unresponsive_cctv
        }

# The capture_screenshots and scrape_image_HLS functions remain the same as in the previous versions
