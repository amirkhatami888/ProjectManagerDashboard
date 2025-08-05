import os
import json
from math import radians, cos, sin, asin, sqrt
from django.conf import settings
from .read_shapefile import extract_province_boundaries

# Try to load province boundaries from the JSON file
PROVINCE_BOUNDARIES = {}
json_path = os.path.join(settings.BASE_DIR, 'static', 'mapfiles', 'province_boundaries.json')
try:
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            PROVINCE_BOUNDARIES = json.load(f)
            print(f"Loaded boundaries for {len(PROVINCE_BOUNDARIES)} provinces.")
    else:
        # If the JSON file doesn't exist, extract boundaries from shapefile
        PROVINCE_BOUNDARIES = extract_province_boundaries()
except Exception as e:
    print(f"Error loading province boundaries: {str(e)}")

# Province centers for distance-based validation (fallback)
PROVINCE_CENTERS = {
    'البرز': [50.97, 35.82],
    'آذربایجان شرقی': [46.27, 38.08],
    'آذربایجان غربی': [45.08, 37.55],
    'بوشهر': [51.20, 29.26],
    'چهارمحال و بختیاری': [50.86, 32.33],
    'فارس': [52.53, 29.61],
    'گیلان': [49.59, 37.28],
    'گلستان': [54.44, 36.84],
    'همدان': [48.51, 34.80],
    'هرمزگان': [56.28, 27.18],
    'ایلام': [46.42, 33.64],
    'اصفهان': [51.67, 32.65],
    'کرمان': [57.08, 30.28],
    'کرمانشاه': [47.06, 34.31],
    'خراسان شمالی': [57.33, 37.47],
    'خراسان رضوی': [59.62, 36.30],
    'خراسان جنوبی': [59.22, 32.86],
    'خوزستان': [48.69, 31.33],
    'کهگیلویه و بویراحمد': [51.60, 30.66],
    'کردستان': [47.00, 35.31],
    'لرستان': [48.35, 33.58],
    'مرکزی': [49.70, 34.09],
    'مازندران': [52.35, 36.23],
    'قزوین': [49.85, 36.27],
    'قم': [50.88, 34.64],
    'سمنان': [54.30, 35.57],
    'سیستان و بلوچستان': [60.86, 29.50],
    'تهران': [51.42, 35.70],
    'یزد': [54.36, 31.89],
    'زنجان': [48.48, 36.67],
    'کیش': [54.01, 26.52],
}

# Function to calculate distance between two points using Haversine formula
def haversine(lon1, lat1, lon2, lat2):
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

# Check if a point is within a polygon using ray casting algorithm
def is_point_in_polygon(point, polygon):
    x, y = point
    n = len(polygon)
    if n < 3:  # Polygon needs at least 3 points
        return False
        
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside

# Check if coordinates are in the specified province
def is_point_in_province(longitude, latitude, province_name):
    try:
        # Convert to float
        longitude = float(longitude)
        latitude = float(latitude)
        
        # First, check if coordinates are within Iran
        iranLongMin = 44.0
        iranLongMax = 63.5
        iranLatMin = 25.0
        iranLatMax = 40.0
        
        if longitude < iranLongMin or longitude > iranLongMax or latitude < iranLatMin or latitude > iranLatMax:
            return False, "مختصات وارد شده خارج از محدوده ایران است."
        
        # Try to match province name
        # Some provinces might be named differently in the shapefile
        province_key = province_name
        
        # Check if we have the polygon data for this province
        if province_key in PROVINCE_BOUNDARIES:
            polygon = PROVINCE_BOUNDARIES[province_key]
            if is_point_in_polygon((longitude, latitude), polygon):
                return True, "مختصات در محدوده استان تأیید شد."
            else:
                return False, "مختصات وارد شده در محدوده استان انتخاب شده قرار ندارد."
        
        # Fallback to distance-based validation if we don't have polygon data
        if province_name in PROVINCE_CENTERS:
            # Calculate distance to province center
            center_lon, center_lat = PROVINCE_CENTERS[province_name]
            distance = haversine(longitude, latitude, center_lon, center_lat)
            
            # If distance is greater than 100km (rough province radius), it's likely not in the province
            if distance > 100:
                return False, "مختصات وارد شده احتمالاً خارج از استان انتخاب شده قرار دارد."
            return True, "مختصات در محدوده استان قرار دارد."
        else:
            # If we don't have center data for this province, just return True
            return True, "عدم امکان بررسی دقیق - مختصات پذیرفته شد."
    
    except Exception as e:
        return False, f"خطا در بررسی مختصات: {str(e)}" 