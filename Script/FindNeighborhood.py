import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle
import matplotlib.pyplot as plt
import math

# Load the data
file_path = "C:\\Users\\naris\\Desktop\\STIU\\2024-1 Internship\\Gistda\\2024-07-01 Image Scraping\\Data\\cctv_locations_test_coordinate.xlsx"
df = pd.read_excel(file_path)

# Extract latitude and longitude into a numpy array
# coordinates = df[['Latitude', 'Longitude']].values
coordinates = np.array([
    [13.769741049467855, 100.57298223507024],
    [13.769741002681604, 100.57298159489989],
    [13.76948190706499, 100.57287644839684],
    [13.789905618799368, 100.57434272643398]  
    ])


def meters_to_degrees(meters):
    """
    This fomular is calculated using brute force method
    position 1 = 13.769741049467855, 100.57298223507024
    position 2 = 13.789905618799368, 100.57434272643398
    distance in degree = 0.000352692903260668
    distance in km (approx) (calculate from given position) = 2235.799051227861
    """
    
    # Distance per degree as calculated
    distance_per_degree = 2235.799051227861/0.000352692903260668
    # Convert meters to degrees
    degrees = meters / distance_per_degree
    return degrees

# Apply DBSCAN eps=0.00001
dbscan = DBSCAN(eps=meters_to_degrees(100), min_samples=1, metric='haversine').fit(np.radians(coordinates))
print(dbscan.labels_)


# # Add the cluster labels to the DataFrame
# df['Group'] = dbscan.labels_

# # Save the results to a new Excel file
# df.to_excel('clustered_cctv_locations.xlsx', index=False)


# print("Clustering complete. Results saved to 'clustered_cctv_locations.xlsx'.")
# # print(eps)
# # print(eps_in_radians)






