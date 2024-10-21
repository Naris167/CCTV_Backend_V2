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
from script_config import config

BASE_URL = "http://www.bmatraffic.com"
JSON_DIRECTORY = Path(config['json_path'])

class ThreadingUtils:
    @staticmethod
    def run_threaded(func, semaphore, *args):
        threads = []
        for arg in args:
            thread = Thread(target=func, args=(semaphore, *arg))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

class ImageUtils:
    @staticmethod
    def image_to_binary(image_input):
        if isinstance(image_input, bytes):
            return psycopg2.Binary(image_input)
        elif isinstance(image_input, str):
            with open(image_input, 'rb') as file:
                return psycopg2.Binary(file.read())
        else:
            raise ValueError("Invalid input type for image_to_binary function.")

    @staticmethod
    def binary_to_image(binary_data, output_path):
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
    @staticmethod
    def sort_key(item):
        return [int(part) if part.isdigit() else part.lower() for part in re.split('([0-9]+)', str(item))]

    @staticmethod
    def sort_results(*args: Union[Dict[str, Any], List[Any]]) -> None:
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
    @staticmethod
    def readable_time(total_seconds: int) -> str:
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
    @staticmethod
    def create_cctv_status_dict(cctv_list: List[str], status: bool) -> Dict[str, bool]:
        return dict.fromkeys(cctv_list, status)

    @staticmethod
    def select_non_empty(*items: Tuple[Any, str], item_description: str = "item") -> Tuple[Any, str]:
        for value, name in items:
            if value:
                logger.info(f"[SELECTOR] Using {name} {item_description} of type {type(value)}")
                return value, name
        
        logger.error(f"[SELECTOR] All {len(items)} {item_description}s are empty.")
        return None, None

    @staticmethod
    def detect_cctv_status(all_cctv_ids, *args):
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

    @staticmethod
    def check_cctv_integrity(cctv_working: Dict[str, str], cctv_unresponsive: Dict[str, str], cctv_fail: List[str]) -> Tuple[bool, List[str]]:
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

class JSONUtils:
    @staticmethod
    def load_latest_cctv_sessions_from_json() -> Optional[Tuple[str, str, Dict[str, str]]]:
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
        """
        This fomular is calculated using brute force method
        It convert a distance in meters to degrees using a known conversion factor.

        This calculation maintains high precision using the Decimal class.
        The precision is +- 1-5 meter in the distance less than 2236 meters
        
        position 1 = 13.769741049467855, 100.57298223507024
        position 2 = 13.789905618799368, 100.57434272643398
        distance in degree = 0.00035269290326066755967941712679447618938866071403026580810546874999
        distance in km (approx) (calculate from given position) = 2235.799051227861
        """

        # Define the numbers as Decimal types
        numerator = Decimal('2235.799051227861')
        denominator = Decimal('0.00035269290326066755967941712679447618938866071403026580810546874999')

        # Find the ratio of the actual distance in meters to the eps value in degrees
        distance_per_degree = numerator / denominator

        # Convert meters to degrees
        degrees = Decimal(meters) / distance_per_degree

        return degrees

    @staticmethod
    def cluster(cls, meters: int, all_cams_coordinate: List[Tuple[str, float, float]]) -> List[Tuple[str, str, float, float]]:
        logger.info(f"[CLUSTER] Distance set to {meters} meters")
        from sklearn.cluster import DBSCAN

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
        clustered_data = None
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
