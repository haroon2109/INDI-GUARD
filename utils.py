import pandas as pd
import plotly.express as px
import streamlit as st

def get_risk_chart(probs, classes):
    """
    Generates a bar chart for risk probabilities.
    """
    prob_df = pd.DataFrame({
        'Risk Level': classes,
        'Probability': probs
    })
    
    # Custom color mapping
    input_color_map = {'High':'red', 'Medium':'orange', 'Low':'green'}
    # Ensure mapping matches present keys if partial
    
    fig = px.bar(prob_df, x='Risk Level', y='Probability', color='Risk Level', 
                 color_discrete_map=input_color_map)
    return fig

def get_trend_chart(region_name):
    """
    Generates a dummy trend chart for the region.
    In a real app, this would query historical DB.
    """
    # Dummy data
    history = pd.DataFrame({
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'Avg Risk Score': [0.2, 0.3, 0.5, 0.7, 0.4, 0.2]
    })
    fig = px.line(history, x='Month', y='Avg Risk Score', 
                  title=f"Risk Trend in {region_name}", markers=True)
    return fig
