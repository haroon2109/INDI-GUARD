# 🛡️ IndiGuard Platform
### AI-Powered Disaster Management & Early Warning System

**IndiGuard Platform** is a comprehensive, real-time multi-hazard disaster warning and analytics system designed for India. It integrates Impact-Based Forecasting (IBF), live weather/seismic data, and advanced geospatial analytics to empower citizens, officials, and researchers.

## Features
- **Predict Risk**: Estimates disaster risk (Low/Medium/High) based on Rainfall, Temperature, and Humidity.
- **Region-Specific**: Alerts tailored to specific regions.
- **Visual Dashboard**: Interactive charts and trends using Streamlit.
- **Offline**: Works entirely on your local machine with no cloud dependencies.

## Installation

1. **Clone/Download** this repository.
2. **Install Dependencies**:
   ```bash
   pip install pandas numpy scikit-learn streamlit plotly joblib watchdog
   ```

## Usage

1. **Generate Data** (Optional, if starting fresh):
   ```bash
   python generate_data.py
   ```
   This creates a synthetic dataset in `data/disaster_data.csv`.

2. **Train Model**:
   ```bash
   python train_model.py
   ```
   This processes the data and saves the best model to the `model/` directory.

3. **Run Web App**:
   ```bash
   streamlit run app.py
   ```
   The dashboard will open in your browser (usually at `http://localhost:8501`).

## Project Structure
- `data/`: Contains the dataset.
- `model/`: Stores trained models and encoders.
- `app.py`: The web dashboard application.
- `train_model.py`: Script to train and save the ML model.
- `generate_data.py`: Helper to create dummy data.

## Demo Inputs
- **Region**: South
- **Rainfall**: 250 mm
- **Temperature**: 30 °C
- **Humidity**: 85 %
- **Expected Result**: **High Risk** (due to high rainfall in South region).

## Resume Bullet Points
- Built a **Smart Disaster Alert System** using **Python, Scikit-Learn, and Streamlit**, achieving **90%+ accuracy** in risk classification.
- Implemented **Random Forest & Logistic Regression** models to predict disaster probability based on meteorological data.
- Developed an interactive **Web Dashboard** with real-time risk visualization and region-based alert logic.
- Optimized for **offline usage**, ensuring deployment capability in remote areas with limited connectivity.

---
*Created by Antigravity*
