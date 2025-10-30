# utils/api_client.py
import streamlit as st
import requests
import time
from utils.firebase_client import save_analysis_to_firestore # <-- IMPORT

BASE_URL = st.secrets["BACKEND_BASE_URL"]
BACKEND_SUBMIT_URL = f"{BASE_URL}/analyze/all"
BACKEND_STATUS_URL = f"{BASE_URL}/analyze/status/"

# Polling parameters
INITIAL_POLLING_DELAY = 60*4  # Seconds to wait before first status check
POLLING_INTERVAL = 30  # Seconds to wait between status checks
POLLING_TIMEOUT = 600  # 10 minutes total timeout for the whole process

def run_analysis_pipeline(company_id: str, company_name: str, doc_urls: list[str]):
    """
    Calls the FastAPI backend asynchronously and saves the result to Firestore.
    1. Submits the job and gets a job_id.
    2. Polls the status endpoint until the job is "Complete" or "Failed".
    3. Saves the final result to Firestore using company_id.
    Stores the *final result* in st.session_state['api_response'].
    """
    
    # --- UPDATED PAYLOAD ---
    investing_thesis = {"overall_thesis": st.session_state.vc_thesis,
                        "industry_weights": st.session_state.get("industry_preferences", {})}
    payload = {
        "documents_url": doc_urls,
        "company_name": company_name,
        # --- PULL PREFERENCES FROM SESSION STATE ---
        "investing_thesis": investing_thesis,
        "vc_portfolio_information": st.session_state.get("portfolio_cos", [])
    }
    
    start_time = time.time()
    st.session_state['analysis_complete'] = False
    st.session_state['api_response'] = None

    try:
        # --- Step 1: Submit the Job ---
        submit_response = requests.post(BACKEND_SUBMIT_URL, json=payload, timeout=30)
        submit_response.raise_for_status()
        
        if submit_response.status_code != 202:
             st.error(f"Error: Backend did not accept job. Status: {submit_response.status_code}, {submit_response.text}")
             return False
             
        job_id = submit_response.json().get("job_id")
        if not job_id:
            st.error("Error: Backend did not return a job_id.")
            return False

        st.info(f"Job submitted successfully (Job ID: {job_id}). Waiting for results...")
        
        # Waits for the expected time gap
        time.sleep(INITIAL_POLLING_DELAY)
        
        # --- Step 2: Poll for Results ---
        while True:
            # Check for overall timeout
            if time.time() - start_time > POLLING_TIMEOUT:
                st.error("Error: The analysis request timed out while waiting for results.")
                return False

            # Make the status check call
            status_url = f"{BACKEND_STATUS_URL}{job_id}"
            status_response = requests.get(status_url, timeout=30)
            status_response.raise_for_status()
            
            status_data = status_response.json()
            job_status = status_data.get("status")

            if job_status == "Complete":
                # --- SUCCESS ---
                result_data = status_data.get("result")
                
                if result_data is None:
                     st.error("Error: Job completed but no result data was found.")
                     return False
                
                # Store in session
                st.session_state['api_response'] = result_data
                st.session_state['analysis_complete'] = True
                
                # --- NEW: Save to Firestore ---
                save_analysis_to_firestore(company_id, result_data)
                
                return True
                
            elif job_status == "Failed":
                # --- FAILURE ---
                error_message = status_data.get("error", "Unknown analysis failure.")
                st.error(f"Analysis Failed: {error_message}")
                return False
                
            elif job_status == "Pending":
                # --- PENDING ---
                # This is the normal case, wait and poll again
                st.status(f"Analysis in progress... (Status: {job_status}). Checking again in {POLLING_INTERVAL}s.", state="running")
                time.sleep(POLLING_INTERVAL)
                
            else:
                st.error(f"Error: Unknown job status received: {job_status}")
                return False

    except requests.exceptions.HTTPError as errh:
        st.error(f"API Error: {errh.response.status_code} - {errh.response.text}")
    except requests.exceptions.ConnectionError as errc:
        st.error(f"Connection Error: Could not connect to the backend at {BASE_URL}.")
    except requests.exceptions.Timeout as errt:
        st.error("Error: A request timed out. Please try again.")
    except requests.exceptions.RequestException as err:
        st.error(f"An unexpected error occurred: {err}")
    
    return False