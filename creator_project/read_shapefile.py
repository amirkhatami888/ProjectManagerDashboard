import os
import json
import shapefile
from django.conf import settings

def extract_province_boundaries():
    """
    Extract province boundaries from shapefile.
    Returns a dictionary mapping province names to their boundary points.
    """
    try:
        shapefile_path = os.path.join(settings.BASE_DIR, 'static', 'mapfiles', 'province.shp')
        reader = shapefile.Reader(shapefile_path, encoding='latin1')
        
        province_boundaries = {}
        
        # Get the field index for province name
        field_names = [field[0] for field in reader.fields[1:]]  # Skip the first field (DeletionFlag)
        name_field_index = field_names.index('NAME') if 'NAME' in field_names else 0
        
        for sr in reader.shapeRecords():
            # Get province name
            province_name = sr.record[name_field_index]
            if isinstance(province_name, bytes):
                try:
                    province_name = province_name.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        province_name = province_name.decode('latin1')
                    except UnicodeDecodeError:
                        province_name = str(province_name)
            
            # Get shape points
            points = []
            for point in sr.shape.points:
                # Extract longitude and latitude
                lon, lat = point
                points.append([lon, lat])
            
            # Store in dictionary
            province_boundaries[province_name] = points
        
        # Save to a JSON file for later use
        output_path = os.path.join(settings.BASE_DIR, 'static', 'mapfiles', 'province_boundaries.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(province_boundaries, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully extracted boundaries for {len(province_boundaries)} provinces.")
        return province_boundaries
    
    except Exception as e:
        print(f"Error extracting province boundaries: {str(e)}")
        return {}

if __name__ == "__main__":
    # This allows running the script directly
    from django.conf import settings
    extract_province_boundaries() 