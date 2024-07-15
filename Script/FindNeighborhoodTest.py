import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN

def find_eps_value(file_path, target_array, decimal_places=18):
    # Load the data
    df = pd.read_excel(file_path)

    # Extract latitude and longitude into a numpy array
    # coordinates = np.array([
    # [13.769741049467855, 100.57298223507024],
    # [13.769741002681604, 100.57298159489989],
    # [13.76948190706499, 100.57287644839684],
    # [13.789905618799368, 100.57434272643398]  
    # ])

    coordinates = np.array([
    [13.769741049467855, 100.57298223507024],
    [13.789905618799368, 100.57434272643398]  
    ])

    # Initialize eps 0.000007512982
    eps = 0.000352692903260668

    # Loop until we find the correct eps
    while eps < 1:  # Set a reasonable upper limit for eps
        print(f"Testing eps = {eps:.{decimal_places}f}")

        # Apply DBSCAN with the current eps value
        dbscan = DBSCAN(eps=eps, min_samples=1, metric='haversine').fit(np.radians(coordinates))

        # Check if the output matches the target array
        if (dbscan.labels_ == target_array).all():
            print(f"Found matching eps: {eps:.{decimal_places}f}")
            return eps

        # Increase eps by 10^-15
        eps += 10 ** -decimal_places

    # If no matching eps is found
    print("No matching eps value found within the range.")
    return None

# Define the file path
file_path = "C:\\Users\\naris\\Desktop\\STIU\\2024-1 Internship\\Gistda\\2024-07-01 Image Scraping\\Data\\cctv_locations_test_coordinate.xlsx"

# Define the target array we are looking for
target_array = np.array([0, 0])

# Call the function to find the eps value
matching_eps = find_eps_value(file_path, target_array)

# if matching_eps is not None:
#     print(f"The eps value that results in {target_array} is: {matching_eps:.{decimal_places}f}")
# else:
#     print("No matching eps value found.")







