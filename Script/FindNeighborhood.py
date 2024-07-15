import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle
import matplotlib.pyplot as plt
import math
from decimal import Decimal, getcontext

# Load the data
file_path = "C:\\Users\\naris\\Desktop\\STIU\\2024-1 Internship\\Gistda\\2024-07-01 Image Scraping\\Data\\cctv_locations_test_coordinate.xlsx"
df = pd.read_excel(file_path)

# Extract latitude and longitude into a numpy array
# coordinates = df[['Latitude', 'Longitude']].values

# BKK
coordinates = np.array([
    # [13.769741049467855, 100.57298223507024],
    [13.770523368582106, 100.5733092832212],
    [13.76948190706499, 100.57287644839684]
    # [13.789905618799368, 100.57434272643398]  
    ])

# CNX
# coordinates = np.array([
#     [18.810971713057405, 98.99538475142329], #0
#     [18.810745946644577, 98.99726633357682], #200
#     [18.810522868108485, 98.99915329666307], #400
#     [18.810087754258326, 99.00292757329737] #800
#     ])

# Russia
# coordinates = np.array([
#     # 9161 meter error
#     # actual distance = 1,004,091 meters
#     # in formula = 1001000
#     [72.53022086909561, 108.09147977067974], #0
#     [72.59892904426592, 138.42442021172437]  #1000000
#     ])

# equator
# coordinates = np.array([
#     # 6223 meter error
#     # actual distance = 1,001,323 meters
#     # in formula = 995100
#     [13.759625321601407, 90.3026838154741], #0
#     [13.758667982019684, 99.56228101389775]  #1000000
#     # 0.156963217031847915294839879152277717366814613342285156250000000000
#     ])

# Test rama 9
# coordinates = np.array([
#     [13.769741049467855, 100.57298223507024],
#     [13.789905618799368, 100.57434272643398]
#     # 0.00035269290326066755967941712679447618938866071403026580810546874999
# ])

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

    # Perform the division
    distance_per_degree = numerator / denominator
    # distance_per_degree = 2235.799051227861/0.00035269290326066755967941712679447618938866071403026580810546874999


    # Convert meters to degrees
    degrees = Decimal(meters) / distance_per_degree
    # degrees = meters / distance_per_degree
    return degrees

# Apply DBSCAN eps=0.00001
meters = 128
print(meters)
dbscan = DBSCAN(eps=float(meters_to_degrees(meters)), min_samples=1, metric='haversine').fit(np.radians(coordinates))
print(dbscan.labels_)


# # Add the cluster labels to the DataFrame
# df['Group'] = dbscan.labels_

# # Save the results to a new Excel file
# df.to_excel('clustered_cctv_locations.xlsx', index=False)


# print("Clustering complete. Results saved to 'clustered_cctv_locations.xlsx'.")
# # print(eps)
# # print(eps_in_radians)






