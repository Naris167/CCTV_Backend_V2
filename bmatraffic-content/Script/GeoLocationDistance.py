from geopy.distance import geodesic

# Coordinates in (latitude, longitude) format
point1 = (13.769741049467855, 100.57298223507024)
point2 = (13.789905618799368, 100.57434272643398)

point3 = (13.759625321601407, 90.3026838154741)
point4 = (13.758667982019684, 99.56228101389775)

point5 = (13.769741002681604, 100.57298159489989)
point6 = (13.76948190706499, 100.57287644839684)


# Calculate the distance
distance1 = geodesic(point1, point2).meters
distance2 = geodesic(point3, point4).meters
distance3 = geodesic(point5, point6).meters


print(distance1)
print(distance2)
print(distance3)