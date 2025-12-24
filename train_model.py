import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

def train():
    print("Loading data...")
    try:
        df = pd.read_csv('data/disaster_data.csv')
    except FileNotFoundError:
        print("Error: data/disaster_data.csv not found. Run generate_data.py first.")
        return

    # --- PREPROCESSING ---
    print("Preprocessing...")
    
    # Feature Columns
    # Region/City are categorical but maybe too high cardinality for simple encoding? 
    # We'll use them as they convey implicit geo-info.
    feature_cols = ['Region', 'Season', 'Rainfall', 'Temperature', 'Humidity', 
                    'SoilMoisture', 'RiverLevel', 'WindSpeed', 'Pressure', 
                    'PopulationDensity', 'InfrastructureIndex']
    
    X = df[feature_cols].copy()
    y = df['RiskLevel']

    # Encoders
    le_dict = {}
    
    # Encode Categorical
    for col in ['Region', 'Season']:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col])
        le_dict[col] = le
        joblib.dump(le, f'model/{col.lower()}_encoder.pkl')

    # Encode Target
    target_le = LabelEncoder()
    y_encoded = target_le.fit_transform(y)
    joblib.dump(target_le, 'model/target_encoder.pkl')

    # Scale Numerical
    numeric_cols = ['Rainfall', 'Temperature', 'Humidity', 'SoilMoisture', 
                    'RiverLevel', 'WindSpeed', 'Pressure', 'PopulationDensity', 'InfrastructureIndex']
    
    scaler = StandardScaler()
    X[numeric_cols] = scaler.fit_transform(X[numeric_cols])
    joblib.dump(scaler, 'model/scaler.pkl')

    # --- TRAINING ---
    print("Training Random Forest...")
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

    rf = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42)
    rf.fit(X_train, y_train)

    # --- EVALUATION ---
    preds = rf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"Model Accuracy: {acc:.4f}")
    print("\nClassification Report:\n", classification_report(y_test, preds, target_names=target_le.classes_))

    # Save Model
    joblib.dump(rf, 'model/disaster_model.pkl')
    print("All models and encoders saved to model/ folder.")

if __name__ == "__main__":
    train()
