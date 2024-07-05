import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle
import matplotlib.pyplot as plt

# Load the data
file_path = "C:\\Users\\naris\\Desktop\STIU\\2024-1 Internship\\Gistda\\2024-07-01 Image Scraping\\Data\\locationForClustering.xlsx"
df = pd.read_excel(file_path)

# Extract latitude and longitude into a numpy array
coordinates = df[['Latitude', 'Longitude']].values

# Function to calculate the distance between two points
def get_distance(coord1, coord2):
    return great_circle(coord1, coord2).meters

# Calculate distances between all pairs of points
distances = []
for i in range(len(coordinates)):
    for j in range(i + 1, len(coordinates)):
        distances.append(get_distance(coordinates[i], coordinates[j]))

# Plot a histogram of the distances
# plt.hist(distances, bins=50)
# plt.xlabel('Distance (meters)')
# plt.ylabel('Frequency')
# plt.title('Histogram of Distances between CCTV Locations')
# plt.show()

# Choose a smaller eps value based on the histogram
# For example, let's choose the 10th percentile distance as a starting point
eps = np.percentile(distances, 2)  # 10th percentile distance


# Convert eps to radians since DBSCAN with metric='haversine' expects radians
eps_in_radians = eps / 6371000.0  # Earth radius in meters

# Apply DBSCAN
dbscan = DBSCAN(eps=0.00001, min_samples=1, metric='haversine').fit(np.radians(coordinates))

# Add the cluster labels to the DataFrame
df['Group'] = dbscan.labels_

# Save the results to a new Excel file
df.to_excel('clustered_cctv_locations.xlsx', index=False)

print("Clustering complete. Results saved to 'clustered_cctv_locations.xlsx'.")
# print(eps)
# print(eps_in_radians)