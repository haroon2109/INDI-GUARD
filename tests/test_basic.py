import os
import sys
import pytest
from app import predict_ibf, model, region_enc, season_enc, scaler

# Ensure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_file_structure():
    """Verify critical files exist."""
    required_files = [
        "app.py",
        "requirements.txt",
        "Dockerfile",
        "README.md",
        "data/live_sources.py"
    ]
    for f in required_files:
        assert os.path.exists(f), f"Missing critical file: {f}"

def test_model_loaded():
    """Verify ML components are loaded."""
    assert model is not None, "Model failed to load"
    assert region_enc is not None, "Region Encoder failed to load"
    assert season_enc is not None, "Season Encoder failed to load"
    assert scaler is not None, "Scaler failed to load"

def test_imports():
    """Verify dependencies are installed."""
    try:
        import streamlit
        import pandas
        import numpy
        import folium
    except ImportError as e:
        pytest.fail(f"Dependency missing: {e}")
