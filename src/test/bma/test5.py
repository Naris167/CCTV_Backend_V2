import math
from decimal import Decimal, getcontext

def meters_to_degrees(distance_meters, latitude):
    """
    Convert a distance in meters to degrees.

    Parameters:
    distance_meters (float): The distance in meters.
    latitude (float): The latitude at which the conversion is to be done.

    Returns:
    float: The equivalent distance in degrees.
    """
    # Conversion factor for latitude (approximate)
    lat_conversion_factor = 111320.0  # meters per degree of latitude
    
    # Conversion factor for longitude based on latitude
    lon_conversion_factor = 111320.0 * math.cos(math.radians(latitude))
    
    # Use the average of the latitudinal and longitudinal conversion factors
    average_conversion_factor = (lat_conversion_factor + lon_conversion_factor) / 2
    
    # Convert meters to degrees
    degrees = distance_meters / average_conversion_factor
    
    return degrees

def meters_to_degree(meters):
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


# Example usage
distance_meters = 2236  # distance in meters
latitude = 13.736717  # example latitude (BKK)
degrees = meters_to_degrees(distance_meters, latitude)
degree = float(meters_to_degree(distance_meters))

print(f"{distance_meters} meters is approximately {degrees} degrees at latitude {latitude}")
print(f"{distance_meters} meters is approximately {degree} degrees")
