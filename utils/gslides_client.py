# FILE: tuning-machines-fr/utils/gslides_client.py
import streamlit as st
import requests
from requests.exceptions import RequestException

# This URL must be set in your Streamlit secrets
GAS_WEB_APP_URL = st.secrets["GAS_WEB_APP_URL"]

def call_gas_action(action: str, mode: str = None):
    """Helper function to call the Google Apps Script web app router."""
    params = {'action': action}
    if mode:
        params['mode'] = mode
    
    try:
        # Set a long timeout; GAS scripts can be slow
        response = requests.get(GAS_WEB_APP_URL, params=params, timeout=120) 
        response.raise_for_status() # Raise an error for bad status codes (4xx or 5xx)
        return response.json()
    except RequestException as e:
        st.error(f"Error calling Google Apps Script: {e}")
        return None