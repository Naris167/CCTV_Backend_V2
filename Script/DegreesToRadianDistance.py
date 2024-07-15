import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from decimal import Decimal, getcontext

"""
This script used brute force method to find the most precise value for `eps` value
that separate 2 coordinates (latitude and longitude).

These 2 coordinates are used 
position 1 = 13.769741049467855, 100.57298223507024
position 2 = 13.789905618799368, 100.57434272643398
distance in km (actual) = 2235.799051227861


distance in degree = 0.00035269290326066755967941712679447618938866071403026580810546874999
"""


def find_eps_value(coordinates, target_array, eps, base_increment, working_precision, decimal_places):
    # Set the precision for decimal operations
    getcontext().prec = decimal_places + 5  # Adding some buffer for calculations

    while working_precision > Decimal(f'1e-{decimal_places}'):
        while eps < 1:
            print(f"Testing eps = {eps}")

            # Apply DBSCAN with the current eps value
            dbscan = DBSCAN(eps=float(eps), min_samples=1, metric='haversine').fit(np.radians(coordinates))

            # Check if the output matches the target array
            if (dbscan.labels_ == target_array).all():
                print(f"Found matching eps segment: {eps}")
                # Decrease the last digit of the found segment
                eps -= base_increment
                # Narrow down the increment for the next precision level
                base_increment = working_precision
                working_precision /= 10  # Move to the next 1 decimal place(s)
                break

            eps += base_increment

        else:
            print("No matching eps value found within the range.")
            return None

    return eps

# Define the coordinates directly
coordinates = np.array([
    [13.769741049467855, 100.57298223507024],
    [13.789905618799368, 100.57434272643398]
    # 0.00035269290326066755967941712679447618938866071403026580810546874999
    # 0.000352991006174028
    # distance = 2235.799051227861
])

# Define the target array we are looking for
target_array = np.array([0, 0])

# Initialize eps
start_eps = Decimal('0.0001')
base_increment = Decimal('0.0001')
working_precision = Decimal('1e-5')
desire_decimal_places = 70

# Call the function to find the eps value
matching_eps = find_eps_value(coordinates, target_array, start_eps, base_increment, working_precision, desire_decimal_places)

