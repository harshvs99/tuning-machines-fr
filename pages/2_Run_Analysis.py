# pages/2_Run_Analysis.py
import streamlit as st
from utils.api_client import run_analysis_pipeline
from utils.firebase_client import upload_company_and_docs
import re

if not st.session_state.get("authenticated", False):
    st.error("You must be logged in to view this page.")
    st.page_link("streamlit_app.py", label="Back to Login")
    st.stop()

st.title("Step 2: Run New Analysis")
st.write("Upload your documents or provide public URLs (e.g., GCS, S3, Dropbox public link).")

URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://' 
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

with st.form("analysis_form"):
    company_name = st.text_input("Company Name", placeholder="e.g., Fabpad")
    
    st.subheader("Document Uploads")
    uploaded_files = st.file_uploader(
        "Upload Documents (Pitch Decks, Financials, etc.)",
        type=["pdf", "docx", "pptx"],
        accept_multiple_files=True
    )
    
    st.subheader("Document URLs")
    st.info("Alternatively, provide public URLs below.")
    doc_urls_text = st.text_area(
        "Enter all document URLs (one per line):",
        height=75,
        placeholder="https://storage.googleapis.com/.../Pitch Deck.pdf\nhttps://storage.googleapis.com/.../Financials.pdf"
    )
    st.caption("**Pitch deck is mandatory for the company analysis.**")
    
    founder_linkedin = st.text_input("Founder LinkedIn URLs (optional, comma-separated)")

    submitted = st.form_submit_button("Run Full Analysis", type="primary")

if submitted:
    if not company_name:
        st.warning("Please enter a company name.")
        st.stop()
        
    doc_urls = [url.strip() for url in doc_urls_text.split("\n") if url.strip()]
    
    if not doc_urls and not uploaded_files:
        st.warning("Please enter at least one document URL or upload files.")
        st.stop()

    # Validate URLs
    invalid_urls = [url for url in doc_urls if not URL_REGEX.match(url)]
    if invalid_urls:
        st.error(f"The following URLs appear to be invalid: {', '.join(invalid_urls)}")
        st.stop()
    
    # --- Step 1: Upload files and create company (MOVED HERE) ---
    company_id = None
    with st.status(f"Uploading files for {company_name}...", expanded=True) as upload_status:
        try:
            # This function now creates the company doc in Firestore
            company_id, file_urls = upload_company_and_docs(company_name, uploaded_files)
            doc_urls.extend(file_urls) # Add uploaded file URLs to the list
            doc_urls = list(set(doc_urls)) # De-duplicate
            
            if not doc_urls:
                 st.error("No valid document URLs found after processing. Please check inputs.")
                 upload_status.update(label="File processing failed.", state="error")
                 st.stop()

            upload_status.update(label="File upload complete!", state="complete")
        except Exception as e:
            upload_status.update(label=f"File upload failed: {e}", state="error")
            st.stop()

    # --- Step 2: Run Analysis Pipeline ---
    with st.status(f"Submitting analysis for {company_name}...", expanded=True) as status_ui:
        # Pass the new company_id to the pipeline
        success = run_analysis_pipeline(company_id, company_name, doc_urls)
    
    if success:
        status_ui.update(label=f"Analysis for {company_name} complete!", state="complete")
        st.success(f"Analysis for {company_name} complete!")
        st.balloons()
        st.info("Redirecting to the First Pass Report...")
        st.switch_page("pages/3_First_Pass_Report.py")
    else:
        status_ui.update(label="Analysis failed.", state="error")
        st.error("Analysis failed. Please see the error message above.")