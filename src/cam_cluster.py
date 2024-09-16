import numpy as np
from sklearn.cluster import DBSCAN
from decimal import Decimal, getcontext
from log_config import logger
from typing import List, Tuple


# Set the precision for Decimal calculations
getcontext().prec = 100  # Set precision high enough for required accuracy

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


def cluster(meters: int, all_cams_coordinate: List[Tuple[str, float, float]]) -> List[Tuple[str, str, float, float]]:
    logger.info(f"[CLUSTER] Distance set to {meters} meters")

    # Extract Cam_IDs and coordinates (Latitude, Longitude)
    cam_ids = [cam[0] for cam in all_cams_coordinate]

    coordinates = np.array([(float(cam[1]), float(cam[2])) for cam in all_cams_coordinate], dtype=float)

    # Perform clustering using DBSCAN
    logger.info("[CLUSTER] Starting clustering...")
    dbscan = DBSCAN(eps=float(meters_to_degrees(meters)), min_samples=1, metric='haversine')
    dbscan.fit(np.radians(coordinates))  # Convert degrees to radians for haversine metric

    # Extract cluster labels
    labels = dbscan.labels_

    # Combine Cam_ID, cluster group, latitude, and longitude into a list of tuples
    clustered_data = [(cam_id, str(label), float(lat), float(lon)) for cam_id, label, (lat, lon) in zip(cam_ids, labels, coordinates)]

    logger.info("[CLUSTER] Clustering completed!\n")
    return clustered_data