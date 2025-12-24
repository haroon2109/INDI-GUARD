import pandas as pd
import numpy as np
import random
from sklearn.preprocessing import minmax_scale

def generate_web_data(n_samples=3000):
    # Specialized Indian Locations
    locations = {
        'Odisha': {'city': 'Bhubaneswar', 'lat': 20.2961, 'lon': 85.8245, 'flood_prone': 0.7, 'cyclone_prone': 0.9},
        'Maharashtra': {'city': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777, 'flood_prone': 0.9, 'cyclone_prone': 0.4},
        'Kerala': {'city': 'Kochi', 'lat': 9.9312, 'lon': 76.2673, 'flood_prone': 0.8, 'cyclone_prone': 0.3},
        'Delhi': {'city': 'New Delhi', 'lat': 28.6139, 'lon': 77.2090, 'flood_prone': 0.2, 'cyclone_prone': 0.0},
        'Assam': {'city': 'Guwahati', 'lat': 26.1445, 'lon': 91.7362, 'flood_prone': 0.95, 'cyclone_prone': 0.1},
        'Tamil Nadu': {'city': 'Chennai', 'lat': 13.0827, 'lon': 80.2707, 'flood_prone': 0.8, 'cyclone_prone': 0.8},
        'West Bengal': {'city': 'Kolkata', 'lat': 22.5726, 'lon': 88.3639, 'flood_prone': 0.7, 'cyclone_prone': 0.8},
        'Gujarat': {'city': 'Ahmedabad', 'lat': 23.0225, 'lon': 72.5714, 'flood_prone': 0.3, 'cyclone_prone': 0.6},
        'Uttarakhand': {'city': 'Dehradun', 'lat': 30.3165, 'lon': 78.0322, 'flood_prone': 0.4, 'cyclone_prone': 0.0}, # Landslide prone
        'Rajasthan': {'city': 'Jaipur', 'lat': 26.9124, 'lon': 75.7873, 'flood_prone': 0.1, 'cyclone_prone': 0.0}  # Drought prone
    }

    seasons = ['Winter', 'Summer', 'Monsoon', 'Post-Monsoon']
    
    data = []

    for _ in range(n_samples):
        region = random.choice(list(locations.keys()))
        meta = locations[region]
        
        lat = meta['lat'] + np.random.uniform(-0.1, 0.1)
        lon = meta['lon'] + np.random.uniform(-0.1, 0.1)
        
        season = random.choice(seasons)

        # --- ENVIRONMENTAL VARIABLES ---
        # Base values
        rainfall = np.random.uniform(0, 50) 
        temperature = np.random.uniform(10, 40)
        humidity = np.random.uniform(20, 80)
        soil_moisture = np.random.uniform(10, 80)
        river_level = np.random.uniform(1, 5)
        wind_speed = np.random.uniform(5, 20)
        
        # Season Effects
        if season == 'Monsoon':
            rainfall = np.random.uniform(200, 800) if meta['flood_prone'] > 0.5 else np.random.uniform(100, 400)
            humidity = np.random.uniform(70, 100)
            river_level += np.random.uniform(2, 6)
            soil_moisture = np.random.uniform(80, 100)
        
        if season == 'Summer':
            temperature = np.random.uniform(35, 48)
            humidity = np.random.uniform(10, 40)
            soil_moisture = np.random.uniform(0, 20)
            
        # Cyclone Simulation (Coastal)
        if meta['cyclone_prone'] > 0.5 and season == 'Post-Monsoon' and random.random() < 0.15:
            wind_speed = np.random.uniform(80, 200)
            rainfall += 300
            pressure = np.random.uniform(950, 990) # Low pressure
        else:
            pressure = np.random.uniform(1000, 1015)

        # --- SOCIO-ECONOMIC ---
        pop_density = np.random.uniform(500, 25000)
        infra_index = np.random.uniform(2, 9)

        # --- RISK LOGIC ---
        risk_score = 0
        hazards = []

        # Flood Risk
        if rainfall > 300 and river_level > 7:
            risk_score += 0.4
            hazards.append('Flood')
        
        # Cyclone Risk
        if wind_speed > 100:
            risk_score += 0.5
            hazards.append('Cyclone')
            
        # Drought Risk
        if season == 'Summer' and rainfall < 10 and soil_moisture < 15:
            risk_score += 0.3
            hazards.append('Drought')
            
        # Base Environmental Load
        risk_score += (rainfall/1000) * 0.2
        risk_score += (wind_speed/200) * 0.2
        
        # Vulnerability Multiplier
        vulnerability = (pop_density / 25000) * 0.5 + (10 - infra_index)/10 * 0.5
        total_risk = min(risk_score * (1 + vulnerability), 1.0)
        
        # Labeling
        if total_risk > 0.75:
            risk_level = 'High'
        elif total_risk > 0.4:
            risk_level = 'Moderate'
        else:
            risk_level = 'Low'
            
        primary_threat = hazards[0] if hazards else 'None'
            
        data.append([
            region, meta['city'], lat, lon, season,
            round(rainfall, 1), round(temperature, 1), round(humidity, 1), 
            round(soil_moisture, 1), round(river_level, 2), round(wind_speed, 1), round(pressure, 1),
            int(pop_density), round(infra_index, 1),
            primary_threat, risk_level
        ])
        
    cols = ['Region', 'City', 'Latitude', 'Longitude', 'Season', 
            'Rainfall', 'Temperature', 'Humidity', 'SoilMoisture', 'RiverLevel', 'WindSpeed', 'Pressure',
            'PopulationDensity', 'InfrastructureIndex', 'PrimaryThreat', 'RiskLevel']
            
    df = pd.DataFrame(data, columns=cols)
    df.to_csv('data/disaster_data.csv', index=False)
    print(f"Indian Disaster Dataset generated: {n_samples} records at data/disaster_data.csv")

if __name__ == "__main__":
    generate_web_data()
