import concurrent.futures
from typing import Callable, List, Tuple, Dict, Any
from datetime import datetime
import time
import random
import math

def scrape_image_HLS(camera_id: str, HLS_Link: str, 
                     interval: float, target_image_count: int, 
                     timeout: float, max_retries: int) -> Tuple[str, Tuple[bytes, ...], Tuple[datetime, ...]] | None:
    # Simulating some work
    time.sleep(random.uniform(0.1, 0.5))  # Reduced sleep time for faster testing
    
    # Simulating success or failure
    if random.random() > 0.1:  # 90% success rate
        # Return a tuple of (camera_id, image_data, timestamps)
        print(f"[{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}][{camera_id}] working!!!")
        return camera_id, (b'dummy_image',) * target_image_count, (datetime.now(),) * target_image_count
    else:
        # Return None to indicate failure
        print(f"[{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}][{camera_id}] failed!!!")
        return None

def worker_func(func: Callable, camera_id: str, url: str, kwargs: Dict[str, Any]) -> Tuple[str, Any]:
    result = func(camera_id, url, **kwargs)
    return camera_id, result

def run_multiprocessing(func: Callable, 
                        max_concurrent: int,
                        working_cctv: Dict[str, str],
                        **kwargs: Any) -> Dict[str, Any]:
    
    # Determine the number of pools and workers per pool
    num_pools = math.ceil(max_concurrent / 60)  # 60 workers per pool to stay within Windows limits
    workers_per_pool = min(60, max(1, max_concurrent // num_pools))
    
    # Create process pools
    pools = [concurrent.futures.ProcessPoolExecutor(max_workers=workers_per_pool) for _ in range(num_pools)]
    
    # Distribute work among pools
    futures = []
    for i, (camera_id, url) in enumerate(working_cctv.items()):
        pool = pools[i % num_pools]
        futures.append(pool.submit(worker_func, func, camera_id, url, kwargs))
    
    # Collect results
    all_results = []
    for future in concurrent.futures.as_completed(futures):
        all_results.append(future.result())
    
    # Process results
    image_result = []
    updated_working_cctv = {}
    unresponsive_cctv = {}

    for camera_id, result in all_results:
        if result is not None:
            image_result.append(result)
            updated_working_cctv[camera_id] = working_cctv[camera_id]
        else:
            unresponsive_cctv[camera_id] = working_cctv[camera_id]

    # Shutdown all pools
    for pool in pools:
        pool.shutdown()

    return {
        "image_result": image_result,
        "working_cctv": updated_working_cctv,
        "unresponsive_cctv": unresponsive_cctv
    }

if __name__ == "__main__":
    # Configuration and setup
    config = {
        'interval': 1.0,
        'target_image_count': 5,  # Reduced for faster testing
        'timeout': 30.0,
        'max_retries': 3
    }

    # Create 1000 dummy CCTVs
    working_cctv: Dict[str, str] = {f'cam{i}': f'link{i}' for i in range(1, 100001)}

    print(f"Starting scraping for {len(working_cctv)} CCTVs...")
    start_time = time.time()

    # Run the multiprocessing function
    results = run_multiprocessing(
        scrape_image_HLS,
        50000,  # Desired number of concurrent processes
        working_cctv,
        **config
    )

    end_time = time.time()
    total_time = end_time - start_time

    # Process the results
    print(f"\nScraping completed in {total_time:.2f} seconds")
    print(f"Successfully scraped {len(results['image_result'])} cameras")
    print(f"Working CCTV: {len(results['working_cctv'])}")
    print(f"Unresponsive CCTV: {len(results['unresponsive_cctv'])}")

    # Calculate and print statistics
    success_rate = len(results['working_cctv']) / len(working_cctv) * 100
    print(f"\nSuccess rate: {success_rate:.2f}%")
    print(f"Average time per camera: {total_time / len(working_cctv):.4f} seconds")