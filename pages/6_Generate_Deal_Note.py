import streamlit as st
import json
import io
from fpdf import FPDF
from pathlib import Path
from utils.pdf_client import build_deal_note_pdf

# --- Auth Check ---
if not st.session_state.get("authenticated", False):
    st.error("You must be logged in to view this page.")
    st.page_link("streamlit_app.py", label="Back to Login")
    st.stop()
# --- End Auth Check ---

st.title("Step 6: Generate Deal Note")

# --- Data Check ---
if not st.session_state.get("api_response") or not st.session_state.get("analysis_complete", False):
    st.warning("No analysis data found. Please run a new analysis first.")
    st.page_link("pages/2_Run_Analysis.py", label="Run New Analysis")
    st.stop()
# --- End Data Check ---

# st.info("""
# **Important Setup:** This feature requires a Google Cloud Platform project with the 
# Google Slides API enabled. 
# 1.  Download your `credentials.json` (for a "Desktop App" OAuth 2.0 Client) 
#     and place it in the root of this Streamlit app's directory.
# 2.  The **first time** you click 'Generate', you will be prompted to 
#     authenticate in your browser.
# 3.  This will create a `token.json` file. For deployment, this `token.json` 
#     (and your `credentials.json`) must be stored securely, e.g., in Streamlit Secrets.
# """)


# Information about the page
st.info(
    """
Provide a consolidated, exportable deal note PDF generated from the analysis JSON.
The PDF uses clear headings and bullets (markdown-like style) for readability and VC view. 
"""
)

company_name = st.session_state.api_response.get('l1_analysis_report', {}).get('company_analysed', 'N/A')
chat_history = st.session_state.get('chat_history', [])
api_data = st.session_state.api_response

# Button to generate and download
if st.button(f"Generate Deal Note for {company_name}", type="primary"):

    # try:
    pdf_bytes = build_deal_note_pdf(api_data, company_name)
    st.success("PDF generated successfully.")
    st.download_button(
        label="Download Deal Note (PDF)",
        data=pdf_bytes,
        file_name=f"{company_name}_Deal_Note.pdf",
        mime="application/pdf"
    )

st.divider()
st.header("Data to be included:")

col1, col2 = st.columns(2)
with col1:
    st.subheader("L1/L2 Analysis")
    st.json(api_data, expanded=False)

with col2:
    st.subheader("Founder Q&A Transcript")
    st.json(chat_history, expanded=False)