import pandas as pd
import os

csv_path = 'data/disaster_data.csv'
parquet_path = 'data/disaster_data.parquet'

if os.path.exists(csv_path):
    print(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Converting to {parquet_path}...")
    df.to_parquet(parquet_path, index=False)
    print("Migration successful!")
else:
    print(f"Error: {csv_path} not found.")
