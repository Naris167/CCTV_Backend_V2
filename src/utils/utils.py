# Standard library imports
import io
import json
import os
import re
import threading
import time
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, getcontext
from pathlib import Path
from threading import Thread
from typing import List, Dict, Any, Tuple, Union, Optional

# Third-party imports
import numpy as np
import psycopg2
from PIL import Image
import tkinter as tk
from tkinter import ttk

# Local/custom imports
from utils.log_config import logger, isDirExist
from script_config import global_config

BASE_URL = "http://www.bmatraffic.com"
JSON_DIRECTORY = Path(global_config['json_path'])

class ThreadingUtils:
    """
    A utility class providing helper methods for managing threaded operations.
    This class offers static methods to simplify common threading patterns
    and provide controlled concurrent execution of functions.
    """
    @staticmethod
    def run_threaded(func, semaphore, *args):
        """
        Executes a given function concurrently across multiple threads with semaphore control.
        
        Args:
            func (callable): The function to be executed in threads. Must accept a semaphore
                           as its first argument, followed by any additional arguments.
            semaphore (threading.Semaphore): A semaphore object to control concurrent access.
            *args (tuple): Variable length argument list where each item is a tuple of arguments 
                         to be passed to the function. Each tuple will be unpacked and passed 
                         to a separate thread execution of the function.
        
        Example:
            semaphore = threading.Semaphore(3)
            def worker(sem, x, y):
                with sem:
                    # do work
                    pass
            
            # Run worker with different args in threads
            ThreadingUtils.run_threaded(worker, semaphore, (1, 2), (3, 4), (5, 6))
        """
        threads = []
        for arg in args:
            thread = Thread(target=func, args=(semaphore, *arg))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

class ImageUtils:
    """
    A utility class for handling image-related operations, including binary conversion,
    file saving, and image selection functions for CCTV data management.
    """
    @staticmethod
    def image_to_binary(image_input):
        """
        Converts an image file or bytes to binary format suitable for database storage.
        
        Args:
            image_input (Union[bytes, str]): Either a path to an image file (str) or image bytes data
        
        Returns:
            psycopg2.Binary: Binary object ready for PostgreSQL database storage
            
        Raises:
            ValueError: If input type is neither bytes nor string
        """
        if isinstance(image_input, bytes):
            return psycopg2.Binary(image_input)
        elif isinstance(image_input, str):
            with open(image_input, 'rb') as file:
                return psycopg2.Binary(file.read())
        else:
            raise ValueError("Invalid input type for image_to_binary function.")

    @staticmethod
    def binary_to_image(binary_data, output_path):
        """
        Saves binary image data to a file at the specified path.
        
        Args:
            binary_data (bytes): Binary image data to be saved
            output_path (str): Destination path where the image will be saved
            
        Raises:
            PermissionError: If writing to output_path is not permitted
            IOError: If there's an error during file writing
        """
        try:
            with open(output_path, 'wb') as file:
                file.write(binary_data)
            print(f"Image saved successfully: {output_path}")
        except PermissionError:
            raise PermissionError(f"Permission denied when writing to {output_path}. Check your write permissions.")
        except IOError as e:
            raise IOError(f"Error writing image file: {str(e)}")

    @staticmethod
    def save_cctv_images(data: List[Tuple[str, Tuple[bytes, ...], Tuple[datetime, ...]]], base_path: str, subfolder_name: str):
        """
        Saves multiple CCTV images with their timestamps in an organized folder structure.
        
        Args:
            data (List[Tuple[str, Tuple[bytes, ...], Tuple[datetime, ...]]]): List of tuples containing
                (cctv_id, images_data, timestamps)
            base_path (str): Base directory path where images will be saved
            subfolder_name (str): Name of the subfolder to create (will be appended with timestamp)
            
        Logs:
            - Success/failure counts
            - Individual file saving status
            - Final save location
        """
        current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        subfolder = f"{subfolder_name}_{current_datetime}"
        save_path = os.path.join(base_path, subfolder)
        os.makedirs(save_path, exist_ok=True)
        
        success = 0
        failed = 0

        for cctv_id, images, timestamps in data:
            try:
                for img_data, timestamp in zip(images, timestamps):
                    filename = f"{cctv_id}_{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.png"
                    full_path = os.path.join(save_path, filename)
                    ImageUtils.binary_to_image(img_data, full_path)
                    logger.info(f"Saved image: {filename} in {save_path}")
                    success += 1
            except Exception as e:
                logger.warning(f"An error occur when saving file to '{full_path}' - {str(e)}")
                failed += 1
        
        logger.info(f"{success} Images successfully saved in {save_path}")
        logger.info(f"{failed} Images failed to saved in {save_path}")

    @staticmethod
    def select_images_and_datetimes(
        images: List[bytes],
        datetimes: List[datetime],
        num_select: int
    ) -> Tuple[List[bytes], List[datetime]]:
        """
        Selects evenly distributed samples from a sequence of images and their corresponding timestamps.
        
        Args:
            images (List[bytes]): List of image binary data
            datetimes (List[datetime]): List of corresponding timestamps
            num_select (int): Number of images to select
            
        Returns:
            Tuple[List[bytes], List[datetime]]: Selected images and their corresponding timestamps
            
        Raises:
            ValueError: If num_select is invalid or lists have different lengths
            
        Note:
            If num_select is 1, returns the middle image and timestamp
            Otherwise, returns evenly distributed samples across the sequence
        """
        
        if not 1 <= num_select <= len(images) or len(images) != len(datetimes):
            raise ValueError("Invalid input: Check number of selections or list lengths.")

        if num_select == 1:
            mid = len(images) // 2
            return [images[mid]], [datetimes[mid]]
        
        selected_images = []
        selected_datetimes = []
        step = (len(images) - 1) / (num_select - 1)
        
        for i in range(num_select):
            index = int(i * step)
            selected_images.append(images[index])
            selected_datetimes.append(datetimes[index])
        
        return selected_images, selected_datetimes


class SortingUtils:
    """
    A utility class providing methods for natural sorting of strings, numbers, 
    and mixed content in various data structures.
    """
    @staticmethod
    def sort_key(item):
        """
        Creates a key for Natural Order Sorting (other sort function use Lexicographical Sort) 
        that handles mixed string-number content.
        
        Args:
            item: Any sortable item that can be converted to string
            
        Returns:
            List: A list where numbers are converted to integers and strings to lowercase,
                 suitable for natural sorting comparison
                 
        Example:
            ['string1', 'string11', 'string2'] will sort as ['string1', 'string2', 'string11']
        """
        return [int(part) if part.isdigit() else part.lower() for part in re.split('([0-9]+)', str(item))]

    @staticmethod
    def sort_results(*args: Union[Dict[str, Any], List[Any]]) -> None:
        """
        Performs in-place natural sorting on dictionaries and lists.
        
        Args:
            *args: Variable number of dictionaries or lists to be sorted
                  - For dictionaries: Sorts by keys
                  - For lists: Sorts items directly, or by first element if items are tuples
                  
        Logs:
            Warning: If an unsupported data type is passed for sorting
            
        Note:
            Modifies the input collections in-place rather than returning new ones
        """
        for i, arg in enumerate(args):
            if isinstance(arg, dict):
                sorted_items = sorted(arg.items(), key=lambda x: SortingUtils.sort_key(x[0]))
                arg.clear()
                arg.update(sorted_items)
            elif isinstance(arg, list):
                arg.sort(key=lambda x: SortingUtils.sort_key(x[0]) if isinstance(x, tuple) else SortingUtils.sort_key(x))
            else:
                logger.warning(f"Unsupported type for sorting: {type(arg)}")

class TimeUtils:
    """
    A utility class for handling time-related conversions and formatting.
    """
    @staticmethod
    def readable_time(total_seconds: int) -> str:
        """
        Converts total seconds into a human-readable time format.
        
        Args:
            total_seconds (int): Number of seconds to convert
            
        Returns:
            str: Formatted string like "2 hours and 30 minutes and 15 seconds"
                or "0 seconds" if total_seconds is 0
                
        Example:
            >>> TimeUtils.readable_time(3665)
            "1 hour and 1 minute and 5 seconds"
        """
        units = [
            (3600, "hour"),
            (60, "minute"),
            (1, "second")
        ]
        parts = []

        for divisor, unit in units:
            value, total_seconds = divmod(total_seconds, divisor)
            if value:
                parts.append(f"{value} {unit}{'s' if value > 1 else ''}")

        return " and ".join(parts) if parts else "0 seconds"

class CCTVUtils:
    """
    A utility class for managing CCTV-related operations including status checking,
    name processing, and motion detection.
    """
    @staticmethod
    def create_cctv_status_dict(cctv_list: List[str], status: bool) -> Dict[str, bool]:
        """
        Creates a dictionary mapping CCTV IDs to a specified status.
        
        Args:
            cctv_list (List[str]): List of CCTV identifiers
            status (bool): Status value to assign to all CCTVs
            
        Returns:
            Dict[str, bool]: Dictionary with CCTV IDs as keys and status as values
        """
        return dict.fromkeys(cctv_list, status)

    @staticmethod
    def select_non_empty(*items: Tuple[Any, str], item_description: str = "item") -> Tuple[Any, str]:
        """
        Selects the first non-empty item from a series of tuples.
        
        Args:
            *items: Variable number of (value, name) tuples to check
            item_description (str): Description of the item type for logging purposes
            
        Returns:
            Tuple[Any, str]: First non-empty (value, name) tuple, or (None, None) if all empty
            
        Logs:
            Info: When a non-empty item is selected
            Error: When all items are empty
        """
        for value, name in items:
            if value:
                logger.info(f"[SELECTOR] Using {name} {item_description} of type {type(value)}")
                return value, name
        
        logger.error(f"[SELECTOR] All {len(items)} {item_description}s are empty.")
        return None, None

    @staticmethod
    def detect_cctv_status(all_cctv_ids, *args):
        """
        Determines online/offline status of CCTVs based on their configuration.
        
        Args:
            all_cctv_ids: List of all CCTV IDs to check
            *args: Variable number of CCTV configuration lists
            
        Returns:
            Tuple[List[str], List[str]]: Sorted lists of (offline_cctvs, online_cctvs)
            
        Note:
            CCTVs are considered offline if they:
            - Are not in all_cctv_ids
            - Have "UNKNOWN" stream method
            - Have empty stream link
        """
        offline_cctvs = set()
        online_cctvs = set()
        all_cctv_ids_set = set(all_cctv_ids)

        for cctv_list in args:
            for cctv in cctv_list:
                cam_id, stream_method, stream_link_1 = cctv[0], cctv[4], cctv[5]
                if cam_id not in all_cctv_ids_set or stream_method == "UNKNOWN" or stream_link_1 == "":
                    offline_cctvs.add(cam_id)
                else:
                    online_cctvs.add(cam_id)

        online_cctvs -= offline_cctvs
        return sorted(list(offline_cctvs), key=SortingUtils.sort_key), sorted(list(online_cctvs), key=SortingUtils.sort_key)

    @staticmethod
    def process_cctv_names(tuple_list):
        """
        Processes and standardizes CCTV names from a list of tuples.
        
        Args:
            tuple_list: List of tuples containing CCTV information where the second element is the name
            
        Returns:
            List[Tuple]: Updated list with processed names
            
        Note:
            Processing includes:
            - Standardizing dashes
            - Removing parenthetical content
            - Handling Thai characters
            - Removing leading identifiers
        """
        def process_name(name):
            name = name.replace("–", "-")
            if re.match(r'^[a-zA-Z\s]+$', name):
                return name
            name = re.sub(r'\([^)]*\)\s*(?:\d+\s*-\s*)?', '', name)
            name = re.sub(r'^[A-Za-z]+\d*-?\d+\s+', '', name)
            if re.match(r'^[\u0E00-\u0E7F]|^\d+\s+[\u0E00-\u0E7F]', name):
                return name.strip()
            return name.strip()

        return [(t[0], process_name(t[1])) + t[2:] for t in tuple_list]

    @staticmethod
    def detect_movement(image_list: List[bytes], threshold_percentage: int = 1, min_changed_pixels: int = 100) -> bool:
        """
        Detects significant movement between consecutive images in a sequence.
        
        Args:
            image_list (List[bytes]): List of image binary data
            threshold_percentage (int): Percentage of total pixels that must change to detect movement
            min_changed_pixels (int): Minimum number of pixels that must change regardless of percentage
            
        Returns:
            bool: True if movement detected, False otherwise
            
        Note:
            - Requires at least 2 images for comparison
            - Converts images to grayscale for comparison
            - Uses pixel difference threshold of 10 for change detection
        """
        if len(image_list) < 2:
            return False
        
        images = [np.array(Image.open(io.BytesIO(img))) for img in image_list]
        gray_images = [img.mean(axis=2).astype(np.uint8) for img in images]
        height, width = gray_images[0].shape
        total_pixels = height * width
        pixels_to_change = max(int(total_pixels * threshold_percentage / 100), min_changed_pixels)
        
        for i in range(1, len(gray_images)):
            diff = np.abs(gray_images[i].astype(np.int16) - gray_images[i-1].astype(np.int16))
            changed_pixels = np.sum(diff > 10)
            if changed_pixels > pixels_to_change:
                return True
        
        return False

class FinalizeUtils:
    """
    A utility class for finalizing and logging CCTV scraping operations, including
    integrity checks and detailed summaries.
    """
    @staticmethod
    def check_cctv_integrity(cctv_working: Dict[str, str], cctv_unresponsive: Dict[str, str], cctv_fail: List[str]) -> Tuple[bool, List[str]]:
        """
        Checks for data integrity issues across CCTV status collections.
        
        Args:
            cctv_working (Dict[str, str]): Dictionary of working CCTVs
            cctv_unresponsive (Dict[str, str]): Dictionary of unresponsive CCTVs
            cctv_fail (List[str]): List of failed CCTV IDs
            
        Returns:
            Tuple[bool, List[str]]: 
                - Boolean indicating if integrity check passed (True) or failed (False)
                - List of detailed integrity issue descriptions
                
        Note:
            Checks for:
            - Duplicate entries across collections
            - Multiple occurrences within the fail list
            - Same key-value pairs in working and unresponsive dictionaries

        Example Usage:
            logger.info(f"[MAIN] Integrity check {'passed' if integrity_passed else 'failed'}.")
            if not integrity_passed:
                for issue in issues:
                    logger.warning(f"[MAIN] {issue}")
        """
        integrity_issues = []
        
        def get_item_info(item: str, source: str, item_type: str) -> str:
            if source == 'cctv_fail':
                count = cctv_fail.count(item)
                return f"is an item in `{source}` list (found {count} occurrence{'s' if count > 1 else ''})"
            else:
                source_dict = cctv_working if source == 'cctv_working' else cctv_unresponsive
                if item_type == 'key':
                    return f"is a key in `{source}` dictionary (key: '{item}', value: '{source_dict[item]}')"
                else:  # value
                    keys = [k for k, v in source_dict.items() if v == item]
                    info = ", ".join([f"(key: '{k}', value: '{item}')" for k in keys])
                    return f"is a value in `{source}` dictionary {info}"

        all_items = defaultdict(set)
        for source, items in [('cctv_working', cctv_working), ('cctv_unresponsive', cctv_unresponsive), ('cctv_fail', cctv_fail)]:
            if isinstance(items, dict):
                for k, v in items.items():
                    all_items[k].add((source, 'key'))
                    all_items[v].add((source, 'value'))
            else:  # list
                for item in items:
                    all_items[item].add((source, 'item'))

        for item, sources in all_items.items():
            if len(sources) > 1 or (len(sources) == 1 and ('cctv_fail', 'item') in sources and cctv_fail.count(item) > 1):
                descriptions = [get_item_info(item, source, item_type) for source, item_type in sources]
                
                for source in ['cctv_working', 'cctv_unresponsive']:
                    if sum(1 for s, _ in sources if s == source) > 1:
                        descriptions.insert(0, f"is duplicated within `{source}` dictionary")
                
                main_description = descriptions.pop(0)
                issue = f"Found '{item}' which {main_description}"
                if descriptions:
                    issue += " and is also found in the following:"
                    for i, desc in enumerate(descriptions):
                        prefix = "└─ " if i == len(descriptions) - 1 else "├─ "
                        issue += f"\n{prefix}{desc}"
                
                integrity_issues.append(issue)

        for key, value in cctv_working.items():
            if key in cctv_unresponsive and cctv_unresponsive[key] == value:
                integrity_issues.append(f"Same key-value pair found in both dictionaries: key '{key}', value '{value}'")

        return len(integrity_issues) == 0, integrity_issues
    
    @staticmethod    
    def log_scrapingHLS_summary(
        total_time: float,
        cctvURL: dict[str, str],
        working_cctv: dict[str, str],
        offline_cctv: dict[str, str],
        image_result: list[tuple[str, tuple[bytes], tuple[datetime]]],
        updated_working_cctv: dict[str, str],
        unresponsive_cctv: dict[str, str],
        logger
    ) -> None:
        """
        Log a detailed summary of CCTV scraping results with performance metrics and statistics.
        
        Flow:
        1. Start with cctvURL (all cameras)
        2. Quick check creates working_cctv and offline_cctv
        3. Scraping working_cctv produces image_result, updated_working_cctv, and unresponsive_cctv
        
        Args:
            total_time (float): Total execution time in seconds
            cctvURL (dict[str, str]): Initial dictionary of all CCTV cameras {id: url}
            working_cctv (dict[str, str]): Dictionary of cameras that passed initial check
            offline_cctv (dict[str, str]): Dictionary of cameras that failed initial check
            image_result (list[tuple]): List of tuples [(camera_id, image_bytes, timestamp)]
            updated_working_cctv (dict[str, str]): Dictionary of cameras successfully scraped
            unresponsive_cctv (dict[str, str]): Dictionary of cameras that failed during scraping
            logger: Logger instance for output
            
        Logs:
            - Initial check statistics
            - Scraping results and success rates
            - Performance metrics
            - Detailed camera status
            - Image capture summary
        """
        # Calculate statistics
        initial_total = len(cctvURL)
        passed_initial_check = len(working_cctv)
        failed_initial_check = len(offline_cctv)
        successfully_scraped = len(image_result)
        final_working = len(updated_working_cctv)
        failed_during_scraping = len(unresponsive_cctv)
        
        # Calculate rates
        initial_check_success_rate = (passed_initial_check / initial_total * 100) if initial_total > 0 else 0
        scraping_success_rate = (successfully_scraped / passed_initial_check * 100) if passed_initial_check > 0 else 0
        overall_success_rate = (successfully_scraped / initial_total * 100) if initial_total > 0 else 0
        avg_time_per_camera = total_time / passed_initial_check if passed_initial_check > 0 else 0
        
        # Header
        logger.info("="*60)
        logger.info("CCTV SCRAPING PIPELINE SUMMARY")
        logger.info("="*60 + "\n")
        
        # Initial check statistics
        logger.info("INITIAL CHECK RESULTS")
        logger.info(f"Total CCTV cameras: {initial_total}")
        logger.info(f"Passed initial check (200 response): {passed_initial_check}")
        logger.info(f"Failed initial check (non-200 response): {failed_initial_check}")
        logger.info(f"Initial check success rate: {initial_check_success_rate:.2f}%" + "\n")
        
        # Scraping statistics
        logger.info("SCRAPING RESULTS")
        logger.info(f"Cameras attempted to scrape: {passed_initial_check}")
        logger.info(f"Successfully scraped images: {successfully_scraped}")
        logger.info(f"Currently working cameras: {final_working}")
        logger.info(f"Failed during scraping: {failed_during_scraping}")
        logger.info(f"Scraping success rate: {scraping_success_rate:.2f}%" + "\n")
        
        # Overall statistics
        logger.info("OVERALL PERFORMANCE")
        logger.info(f"Total execution time: {total_time:.2f} seconds")
        logger.info(f"Average time per camera: {avg_time_per_camera:.4f} seconds")
        logger.info(f"Overall success rate: {overall_success_rate:.2f}%" + "\n")
        
        # Detailed camera status
        logger.info("DETAILED CAMERA STATUS")

        if offline_cctv:
            logger.info("Failed Initial Check:")
            *items, last_item = offline_cctv.items()
            for camera_id, url in items:
                logger.info(f"Camera ID: {camera_id} | URL: {url}")
            last_camera_id, last_url = last_item
            logger.info(f"Camera ID: {last_camera_id} | URL: {last_url}\n")

        if updated_working_cctv:
            logger.info("Successfully Working:")
            *items, last_item = updated_working_cctv.items()
            for camera_id, url in items:
                logger.info(f"Camera ID: {camera_id} | URL: {url}")
            last_camera_id, last_url = last_item
            logger.info(f"Camera ID: {last_camera_id} | URL: {last_url}\n")

        if unresponsive_cctv:
            logger.info("Failed During Scraping:")
            *items, last_item = unresponsive_cctv.items()
            for camera_id, url in items:
                logger.info(f"Camera ID: {camera_id} | URL: {url}")
            last_camera_id, last_url = last_item
            logger.info(f"Camera ID: {last_camera_id} | URL: {last_url}\n")

        # Image result summary
        logger.info("IMAGE RESULT SUMMARY")
        logger.info(f"Total images captured: {len(image_result)}")
        if image_result:  # Only process if there are results
            *items, last_item = image_result
            for camera_id, _, timestamp in items:
                logger.info(f"Camera ID: {camera_id} | Timestamp: {timestamp}")
            last_camera_id, _, last_timestamp = last_item
            logger.info(f"Camera ID: {last_camera_id} | Timestamp: {last_timestamp}\n")
        
        logger.info("STARTING IMAGE SAVE PROCESS")
        logger.info("="*60 + "\n")

    @staticmethod
    def log_scrapingBMA_summary(
        total_time: float,
        cctvSessions: dict[str, str],
        image_result: list[tuple[str, tuple[bytes], tuple[datetime]]],
        working_session: dict[str, str],
        unresponsive_session: dict[str, str],
        logger
    ) -> None:
        """
        Log a detailed summary of session-based CCTV scraping results with performance metrics.
        
        Flow:
        1. Start with cctvSessions (pre-verified cameras with session IDs)
        2. Scraping process produces image_result, working_session, and unresponsive_session
        
        Args:
            total_time (float): Total execution time in seconds
            cctvSessions (dict[str, str]): Initial dictionary of pre-verified cameras {id: session_id}
            image_result (list[tuple]): List of tuples [(camera_id, image_bytes, timestamp)]
            working_session (dict[str, str]): Dictionary of successfully scraped cameras
            unresponsive_session (dict[str, str]): Dictionary of failed cameras
            logger: Logger instance for output
            
        Logs:
            - Scraping statistics and success rates
            - Performance metrics
            - Detailed camera status by session
            - Image capture summary
        """
        # Calculate statistics
        initial_total = len(cctvSessions)
        successfully_scraped = len(image_result)
        final_working = len(working_session)
        failed_during_scraping = len(unresponsive_session)
        
        # Calculate rates
        scraping_success_rate = (successfully_scraped / initial_total * 100) if initial_total > 0 else 0
        avg_time_per_camera = total_time / initial_total if initial_total > 0 else 0
        
        # Header
        logger.info("="*60)
        logger.info("SESSION-BASED CCTV SCRAPING SUMMARY")
        logger.info("="*60 + "\n")
        
        # Scraping statistics
        logger.info("SCRAPING RESULTS")
        logger.info(f"Total cameras with sessions: {initial_total}")
        logger.info(f"Successfully scraped images: {successfully_scraped}")
        logger.info(f"Currently working cameras: {final_working}")
        logger.info(f"Failed during scraping: {failed_during_scraping}")
        logger.info(f"Scraping success rate: {scraping_success_rate:.2f}%" + "\n")
        
        # Performance statistics
        logger.info("PERFORMANCE METRICS")
        logger.info(f"Total execution time: {total_time:.2f} seconds")
        logger.info(f"Average time per camera: {avg_time_per_camera:.4f} seconds" + "\n")
        
        # Detailed camera status
        logger.info("DETAILED CAMERA STATUS")
        
        if working_session:
            logger.info("Successfully Working:")
            *items, last_item = working_session.items()
            for camera_id, session_id in items:
                logger.info(f"Camera ID: {camera_id} | Session ID: {session_id}")
            last_camera_id, last_session_id = last_item
            logger.info(f"Camera ID: {last_camera_id} | Session ID: {last_session_id}\n")
        
        if unresponsive_session:
            logger.info("Failed During Scraping:")
            *items, last_item = unresponsive_session.items()
            for camera_id, session_id in items:
                logger.info(f"Camera ID: {camera_id} | Session ID: {session_id}")
            last_camera_id, last_session_id = last_item
            logger.info(f"Camera ID: {last_camera_id} | Session ID: {last_session_id}\n")
        
        # Image result summary
        logger.info("IMAGE RESULT SUMMARY")
        logger.info(f"Total images captured: {len(image_result)}")
        if image_result:  # Only process if there are results
            *items, last_item = image_result
            for camera_id, _, timestamp in items:
                logger.info(f"Camera ID: {camera_id} | Timestamp: {timestamp}")
            last_camera_id, _, last_timestamp = last_item
            logger.info(f"Camera ID: {last_camera_id} | Timestamp: {last_timestamp}\n")
        
        logger.info("STARTING IMAGE SAVE PROCESS")
        logger.info("="*60 + "\n")

class JSONUtils:
    """
    A utility class for handling JSON operations related to CCTV session data,
    including loading from and saving to files.
    """
    @staticmethod
    def load_latest_cctv_sessions_from_json() -> Optional[Tuple[str, str, Dict[str, str]]]:
        """
        Loads the most recently modified CCTV sessions data from JSON file.
        
        Returns:
            Optional[Tuple[str, str, Dict[str, str]]]: If successful, returns tuple containing:
                - Latest refresh time
                - Latest update time
                - Dictionary of CCTV sessions {camera_id: session_id}
            Returns None if any error occurs
            
        Logs:
            Error: When directory doesn't exist, no JSON files found, or loading fails
            Info: When JSON data is successfully loaded
            
        Note:
            Files are sorted by modification time to get the most recent one
        """
        try:
            if not JSON_DIRECTORY.exists():
                logger.error(f"[JSON] Directory does not exist: {JSON_DIRECTORY}")
                return None

            json_files = sorted(JSON_DIRECTORY.glob('*.json'), key=os.path.getmtime, reverse=True)
            if not json_files:
                logger.error(f"[JSON] No JSON files found in directory: {JSON_DIRECTORY}")
                return None

            latest_file = json_files[0]
            with latest_file.open('r') as json_file:
                data = json.load(json_file)

            logger.info(f"[JSON] Successfully loaded JSON data from file: {latest_file.name}")
            return (
                data.get("latestRefreshTime", ""),
                data.get("latestUpdateTime", ""),
                data.get("cctvSessions", {})
            )

        except (json.JSONDecodeError, FileNotFoundError, OSError) as e:
            logger.error(f"[JSON] Error loading the JSON file: {e}")
            return None

    @staticmethod
    def save_alive_session_to_file(cctv_sessions: Dict[str, str], latest_refresh_time: str, latest_update_time: str) -> None:
        """
        Saves current CCTV session data to a timestamped JSON file.
        
        Args:
            cctv_sessions (Dict[str, str]): Dictionary of active CCTV sessions
            latest_refresh_time (str): Timestamp of last refresh
            latest_update_time (str): Timestamp of last update
            
        Logs:
            Info: When JSON data is successfully written
            Error: If any exception occurs during save process
            
        Note:
            Creates JSON file named 'cctv_sessions_YYYY-MM-DD_HH-MM-SS.json'
        """
        try:
            isDirExist(JSON_DIRECTORY)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = JSON_DIRECTORY / f"cctv_sessions_{timestamp}.json"

            data_to_save = {
                "latestRefreshTime": latest_refresh_time,
                "latestUpdateTime": latest_update_time,
                "cctvSessions": cctv_sessions
            }

            with filename.open("w") as json_file:
                json.dump(data_to_save, json_file, indent=4)

            logger.info(f"[JSON] JSON data has been written to {filename}")
        except Exception as e:
            logger.error(f"Error: {e}")

class ClusteringUtils:

    getcontext().prec = 100  # Set the precision for Decimal calculations

    @staticmethod
    def meters_to_degrees(meters: int) -> Decimal:
        '''
        Converts distance in meters to degrees for geographic calculations.
        
        Args:
            meters (int): Distance in meters to convert
            
        Returns:
            Decimal: Equivalent distance in degrees with high precision
            
        Note:
            - Uses empirically derived conversion factor
            - Precision is ±1-5 meters for distances under 2236 meters
            - Calibrated using reference points:
                pos1 = (13.769741049467855, 100.57298223507024)
                pos2 = (13.789905618799368, 100.57434272643398)
                with known distance of 2235.799051227861 meters
        '''

        # Define the numbers as Decimal types
        numerator = Decimal('2235.799051227861')
        denominator = Decimal('0.00035269290326066755967941712679447618938866071403026580810546874999')

        # Find the ratio of the actual distance in meters to the eps value in degrees
        distance_per_degree = numerator / denominator

        # Convert meters to degrees
        degrees = Decimal(meters) / distance_per_degree

        return degrees

    @classmethod
    def cluster(cls, meters: int, all_cams_coordinate: List[Tuple[str, float, float]]) -> List[Tuple[str, str, float, float]]:
        """
        Performs spatial clustering on CCTV camera locations using DBSCAN algorithm.
        
        Args:
            meters (int): Maximum distance between points in a cluster (eps parameter)
            all_cams_coordinate (List[Tuple]): List of (camera_id, latitude, longitude) tuples
            
        Returns:
            List[Tuple[str, str, float, float]]: List of 
                (camera_id, cluster_label, latitude, longitude) tuples
            
        Note:
            - Uses haversine metric for distance calculations
            - Converts distances to degrees for geographic consistency
            - Sets min_samples=1 to ensure all points are classified
            
        Logs:
            Info: Distance setting and clustering progress
        """

        
        '''PLEASE DO NOT move this import out from this method. It will casue error to HLS scraper'''
        from sklearn.cluster import DBSCAN

        logger.info(f"[CLUSTER] Distance set to {meters} meters")

        # Extract Cam_IDs and coordinates (Latitude, Longitude)
        cam_ids = [cam[0] for cam in all_cams_coordinate]

        coordinates = np.array([(float(cam[1]), float(cam[2])) for cam in all_cams_coordinate], dtype=float)

        # Perform clustering using DBSCAN
        logger.info("[CLUSTER] Starting clustering...")
        eps_in_degrees = float(cls.meters_to_degrees(meters))
        dbscan = DBSCAN(eps=eps_in_degrees, min_samples=1, metric='haversine')
        dbscan.fit(np.radians(coordinates))  # Convert degrees to radians for haversine metric

        # Extract cluster labels
        labels = dbscan.labels_

        # Combine Cam_ID, cluster group, latitude, and longitude into a list of tuples
        clustered_data = [(cam_id, str(label), float(lat), float(lon)) for cam_id, label, (lat, lon) in zip(cam_ids, labels, coordinates)]
        logger.info("[CLUSTER] Clustering completed!")
        
        return clustered_data

class ProgressGUI:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProgressGUI, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        self.initialized = True
        
        self.total_tasks = 0
        self.completed_tasks = 0
        self.root = None
        self.progress_var = None
        self.progress_bar = None
        self.progress_label = None
        self.start_time = None
        self.elapsed_time_var = None
        self.timer_label = None

    def setup(self, total_tasks):
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.root = tk.Tk()
        self.root.title("BMA CCTV Scraping Progress")
        self.root.geometry("350x120")

        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(self.root, maximum=self.total_tasks, variable=self.progress_var)
        self.progress_bar.pack(pady=20)

        self.progress_label = tk.Label(self.root, text=f"Task completed: 0/{self.total_tasks}")
        self.progress_label.pack()

        self.start_time = time.time()
        self.elapsed_time_var = tk.StringVar()
        self.elapsed_time_var.set("Elapsed time: 00:00:00")
        self.timer_label = tk.Label(self.root, textvariable=self.elapsed_time_var)
        self.timer_label.pack()

        self.update_timer()

    def update_timer(self):
        if not self.root:
            return
        elapsed_time = time.time() - self.start_time
        hours, rem = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(rem, 60)
        self.elapsed_time_var.set(f"Elapsed time: {int(hours):02}:{int(minutes):02}:{int(seconds):02}")
        self.root.after(1000, self.update_timer)

    def update_progress(self):
        if not self.root:
            return
        self.progress_var.set(self.completed_tasks)
        self.progress_label.config(text=f"Task completed: {self.completed_tasks}/{self.total_tasks}")
        self.root.update_idletasks()

    def increment_progress(self):
        logger.info("Incrementing progress")
        self.completed_tasks += 1
        if self.root:
            self.root.after(0, self.update_progress)

    def run(self, target, args):
        threading.Thread(target=target, args=args).start()
        self.root.mainloop()

    def quit(self):
        if self.root:
            self.root.quit()
            self.root.destroy()
            self.root = None

    # Function to get the existing ProgressGUI instance
    @classmethod
    def get_instance(cls):
        return cls()

    # Function to setup and get the ProgressGUI instance
    @classmethod
    def initialize(cls, total_tasks):
        instance = cls.get_instance()
        instance.setup(total_tasks)
        return instance
    
    '''
    # Initialize the GUI
    total_tasks = 100
    progress_gui = ProgressGUI.initialize(total_tasks)

    # In your main function or wherever you want to start the GUI
    def main():
        # Your main logic here
        for _ in range(total_tasks):
            # Do some work
            progress_gui.increment_progress()
        
        progress_gui.quit()

    # Run the GUI
    progress_gui.run(target=main, args=())
    '''
