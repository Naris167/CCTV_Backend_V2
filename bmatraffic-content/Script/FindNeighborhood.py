import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from decimal import Decimal, getcontext

# Load the data
file_path = "Data/cctv_locations_test_coordinate.xlsx"
df = pd.read_excel(file_path)

# Extract latitude and longitude into a numpy array
coordinates = df[['Latitude', 'Longitude']].values

# Test location in BKK
# coordinates = np.array([
#     # [13.769741049467855, 100.57298223507024],
#     [13.770523368582106, 100.5733092832212],
#     [13.76948190706499, 100.57287644839684]
#     # [13.789905618799368, 100.57434272643398]  
#     ])


def meters_to_degrees(meters):
    """
    This fomular is calculated using brute force method
    The precision is +- 1-5 meter in the distance less than 2236 meters
    

    position 1 = 13.769741049467855, 100.57298223507024
    position 2 = 13.789905618799368, 100.57434272643398
    distance in degree = 0.00035269290326066755967941712679447618938866071403026580810546874999
    distance in km (approx) (calculate from given position) = 2235.799051227861
    """
    
    # Set the precision to ensure all significant digits are maintained
    getcontext().prec = 100  # Set higher than the number of significant digits

    # Define the numbers as Decimal types
    numerator = Decimal('2235.799051227861')
    denominator = Decimal('0.00035269290326066755967941712679447618938866071403026580810546874999')

    # Find the ratio of the actual distance in meters to the eps value in degrees
    distance_per_degree = numerator / denominator

    # Convert meters to degrees
    degrees = Decimal(meters) / distance_per_degree

    return degrees

# Apply DBSCAN
meters = 170
print(f'Distance set to {meters} meters')
dbscan = DBSCAN(eps=float(meters_to_degrees(meters)), min_samples=1, metric='haversine').fit(np.radians(coordinates))
# print(dbscan.labels_)

# Add the cluster labels to the DataFrame
df['Group'] = dbscan.labels_

# Save the results to a new Excel file
df.to_excel('clustered_cctv_locations.xlsx', index=False)
print("Clustering complete. Results saved to 'clustered_cctv_locations.xlsx'.")

