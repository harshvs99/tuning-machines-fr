import streamlit as st
from utils.gslides_client import create_deal_note

# --- Auth Check ---
if not st.session_state.get("authenticated", False):
    st.error("You must be logged in to view this page.")
    st.page_link("streamlit_app.py", label="Back to Login")
    st.stop()
# --- End Auth Check ---

st.title("Step 6: Generate Deal Note (Google Slides)")

# --- Data Check ---
if not st.session_state.get("api_response") or not st.session_state.get("analysis_complete", False):
    st.warning("No analysis data found. Please run a new analysis first.")
    st.page_link("pages/2_Run_Analysis.py", label="Run New Analysis")
    st.stop()
# --- End Data Check ---

st.info("""
**Important Setup:** This feature requires a Google Cloud Platform project with the 
Google Slides API enabled. 
1.  Download your `credentials.json` (for a "Desktop App" OAuth 2.0 Client) 
    and place it in the root of this Streamlit app's directory.
2.  The **first time** you click 'Generate', you will be prompted to 
    authenticate in your browser.
3.  This will create a `token.json` file. For deployment, this `token.json` 
    (and your `credentials.json`) must be stored securely, e.g., in Streamlit Secrets.
""")

company_name = st.session_state.api_response.get('l1_analysis_report', {}).get('company_analysed', 'N/A')
chat_history = st.session_state.get('chat_history', [])
api_data = st.session_state.api_response

if st.button(f"Generate Google Slide for {company_name}", type="primary"):
    with st.spinner("Connecting to Google Slides API and generating presentation..."):
        presentation_url = create_deal_note(
            company_name=company_name,
            analysis_data=api_data,
            chat_history=chat_history
        )
    
    if presentation_url:
        st.success(f"Successfully created deal note!")
        st.markdown(f"### [Click here to open the Google Slide]({presentation_url})")
    else:
        st.error("Failed to generate deal note. Check console and auth settings.")

st.divider()
st.header("Data to be included:")

col1, col2 = st.columns(2)
with col1:
    st.subheader("L1/L2 Analysis")
    st.json(api_data, expanded=False)

with col2:
    st.subheader("Founder Q&A Transcript")
    st.json(chat_history, expanded=False)