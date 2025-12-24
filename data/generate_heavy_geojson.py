import json
import random
import numpy as np

def generate_complex_polygon(center_lat, center_lon, num_points=200, radius=0.1):
    """Generates a complex polygon to simulate high-detail district boundaries."""
    angles = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
    coords = []
    for angle in angles:
        # Add random noise to radius to create complex shapes
        r = radius * (0.8 + 0.4 * random.random())
        lat = center_lat + r * np.sin(angle)
        lon = center_lon + r * np.cos(angle)
        coords.append([lon, lat])
    
    # Close the loop
    coords.append(coords[0])
    return [coords]

def generate_heavy_geojson(output_file='data/india_districts_mock.geojson', num_districts=700):
    """Generates a GeoJSON with many complex polygons."""
    features = []
    
    # Approximate bounding box for India
    lat_min, lat_max = 8.0, 37.0
    lon_min, lon_max = 68.0, 97.0
    
    print(f"Generating {num_districts} mock districts...")
    
    for i in range(num_districts):
        lat = random.uniform(lat_min, lat_max)
        lon = random.uniform(lon_min, lon_max)
        
        # High detail polygon
        poly_coords = generate_complex_polygon(lat, lon, num_points=150, radius=0.15)
        
        feature = {
            "type": "Feature",
            "properties": {
                "district_id": i,
                "name": f"District_{i}",
                "risk_score": random.random()
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": poly_coords
            }
        }
        features.append(feature)
        
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(output_file, 'w') as f:
        json.dump(geojson, f)
    
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    generate_heavy_geojson()
