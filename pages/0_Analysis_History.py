# pages/0_Analysis_History.py
import streamlit as st
from utils.firebase_client import get_all_analyses
from datetime import datetime
import time

# --- Auth Check ---
if not st.session_state.get("authenticated", False):
    st.error("You must be logged in to view this page.")
    st.page_link("streamlit_app.py", label="Back to Login")
    st.stop()
# --- End Auth Check ---

st.title("Analysis History")
st.write("Load a previously completed analysis to review its reports.")

analyses = get_all_analyses()

if not analyses:
    st.info("No completed analyses found in the database. Run a new analysis to get started.")
    st.page_link("pages/2_Run_Analysis.py", label="Run New Analysis")
    st.stop()

st.write("Click 'Load Report' to set a company as the active analysis, then use the sidebar to navigate its reports.")
st.divider()

# "earliest at the bottom" means newest at the top, which the query already handles.
for analysis in analyses:
    company_name = analysis.get("company_analysed", "Unknown Company")
    company_id = analysis.get("company_id")
    
    # Parse date for cleaner display, handle potential errors
    try:
        updated_at_str = analysis.get("updated_at")
        if updated_at_str:
            updated_at_dt = datetime.fromisoformat(updated_at_str)
            display_date = updated_at_dt.strftime("%Y-%m-%d %H:%M")
        else:
            display_date = "N/A"
    except (ValueError, TypeError):
        display_date = "Invalid Date"

    # Create the "tile"
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(company_name)
            st.caption(f"Last Analyzed: {display_date}")
        with col2:
            if st.button("Load Report", key=company_id, width='stretch', type="secondary"):
                
                analysis_report = analysis.get("analysis_report")
                if not analysis_report:
                    st.error(f"Failed to load: No analysis data found for {company_name}.")
                    st.stop()

                # --- This is the core logic ---
                # 1. Load the data into session state
                st.session_state['api_response'] = analysis_report
                st.session_state['analysis_complete'] = True
                # 2. Reset chat history for the new company
                st.session_state['chat_history'] = [] 
                
                st.success(f"Loaded report for {company_name}.")
                time.sleep(1) # Give user a moment to see the success
                
                # 3. Navigate to the report page
                st.switch_page("pages/3_First_Pass_Report.py")