# 🛡️ INDI-GUARD: Multi-Hazard Disaster Warning & Analytics Platform

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://indi-guard.streamlit.app/)

**Indi-Guard** is a high-performance, open-source intelligence platform designed to provide real-time monitoring, predictive analytics, and "What-If" scenario modeling for multi-hazard disasters across India. 

Running on a Streamlit architecture, it bridges the gap between raw meteorological data and actionable civil defense insights.

---

## 🚀 Key Features
* **Live Hazard Mapping:** Real-time visualization of floods, cyclones, and heatwaves across Indian states using Folium/Leafmap.
* **What-If Simulation:** Interactive environment parameters (Rainfall, Wind Speed, Soil Moisture) that allow users to simulate disaster intensity and view impact reports.
* **Impact-Based Analytics:** Dynamic reporting that calculates population vulnerability and infrastructure risk based on simulated environmental shifts.
* **Official India Branding:** UI designed following GIGW (Guidelines for Indian Government Websites) standards.

---

## 🛠️ Tech Stack
* **Frontend/App Framework:** [Streamlit](https://streamlit.io/)
* **Geospatial Analysis:** [Folium](https://python-visualization.github.io/folium/) & [Geopandas](https://geopandas.org/)
* **Data Processing:** Pandas, NumPy
* **Data Sources:** Open-source APIs (IMD/OpenWeather/GDACS)
* **Deployment:** Streamlit Community Cloud / Docker

---

## 📥 Installation & Local Setup

To run this project on your local machine (`localhost:8501`), follow these steps:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/haroon2109/INDI-GUARD.git
   cd INDI-GUARD
   ```

2. **Create a Virtual Environment (Recommended):**
   ```bash
   python -m venv venv
   # On Windows use:
   venv\Scripts\activate
   # On Mac/Linux use:
   # source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the Platform:**
   ```bash
   streamlit run app.py
   ```

---

## 📊 Analytics Framework
The platform utilizes a Risk Matrix approach to categorize hazards:
* **Low Risk:** Routine monitoring.
* **Moderate Risk:** Heightened awareness required.
* **Critical Risk:** Immediate evacuation/action protocols recommended.

---

## 🛤️ Senior Project Roadmap (Future Enhancements)
- [ ] **ISRO Bhuvan Integration:** Direct WMS tile integration for high-res Indian satellite imagery.
- [ ] **Offline Mode:** PWA implementation for low-bandwidth disaster zones.
- [ ] **Multi-Lingual Support:** Regional language toggles (Hindi, Tamil, Bengali, etc.).
- [ ] **CAP Compliance:** Integration with the Common Alerting Protocol for official government sync.

---

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

*Developed with ❤️ for a Resilient India.*
