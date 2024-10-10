import numpy as np
from PIL import Image
import io
from typing import List

def detect_movement(image_list: List[bytes], threshold_percentage: int = 1, min_changed_pixels: int = 100) -> bool:
    """
    Detect movement in a list of CCTV images.
    
    Args:
    image_list (list): List of image data as bytes
    threshold_percentage (float): Percentage of pixels that need to change to detect movement
    min_changed_pixels (int): Minimum number of pixels that need to change to detect movement
    
    Returns:
    bool: True if movement is detected, False otherwise
    """
    if len(image_list) < 2:
        return False
    
    # Convert bytes to numpy arrays
    images = [np.array(Image.open(io.BytesIO(img))) for img in image_list]
    
    # Convert images to grayscale
    gray_images = [img.mean(axis=2).astype(np.uint8) for img in images]
    
    # Get image dimensions
    height, width = gray_images[0].shape
    total_pixels = height * width
    
    # Calculate the number of pixels that need to change based on the percentage
    pixels_to_change = max(int(total_pixels * threshold_percentage / 100), min_changed_pixels)
    
    # Compare consecutive images
    for i in range(1, len(gray_images)):
        diff = np.abs(gray_images[i].astype(np.int16) - gray_images[i-1].astype(np.int16))
        changed_pixels = np.sum(diff > 10)  # Count pixels with difference greater than 10
        if changed_pixels > pixels_to_change:
            return True
    
    return False