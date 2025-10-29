import streamlit as st
import requests
import time

# URL for your FastAPI backend
# BACKEND_URL = "http://127.0.0.1:8000/analyze/all" 
BACKEND_URL = "https://tuning-machines-457751720656.us-central1.run.app/analyze/all"

def run_analysis_pipeline(company_name: str, doc_urls: list[str]):
    """
    Calls the FastAPI backend to run the investment analysis.
    Stores the result in st.session_state['api_response'].
    """
    payload = {
        "documents_url": doc_urls,
        "company_name": company_name
    }
    
    try:
        response = requests.post(BACKEND_URL, json=payload, timeout=600) # 10 min timeout
        
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        
        # Store the full JSON response in the session state
        st.session_state['api_response'] = response.json()
        
        # Set a flag for successful completion
        st.session_state['analysis_complete'] = True
        return True

    except requests.exceptions.HTTPError as errh:
        st.error(f"API Error: {errh.response.status_code} - {errh.response.text}")
    except requests.exceptions.ConnectionError as errc:
        st.error(f"Connection Error: Could not connect to the backend at {BACKEND_URL}. Is it running?")
    except requests.exceptions.Timeout as errt:
        st.error("Error: The analysis request timed out.")
    except requests.exceptions.RequestException as err:
        st.error(f"An unexpected error occurred: {err}")
    
    st.session_state['analysis_complete'] = False
    st.session_state['api_response'] = None
    return False