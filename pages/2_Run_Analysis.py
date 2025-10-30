import streamlit as st
from utils.api_client import run_analysis_pipeline
from utils.firebase_client import upload_company_and_docs
import re
from utils.firebase_client import upload_company_and_docs
Logger = st.logger if hasattr(st, 'logger') else None

# --- Auth Check ---
if not st.session_state.get("authenticated", False):
    st.error("You must be logged in to view this page.")
    st.page_link("streamlit_app.py", label="Back to Login")
    st.stop()
# --- End Auth Check ---

st.title("Step 2: Run New Analysis")
st.write("Provide the company name and public URLs to its documents (e.g., GCS, S3, Dropbox public link).")

# URL regex for basic validation
URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://' # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
    r'localhost|' # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?' # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

with st.form("analysis_form"):
    company_name = st.text_input("Company Name", placeholder="e.g., Fabpad")
    
    st.subheader("Document URLs")
    st.info("Your backend is configured to download files from public URLs. Please provide the links below.")
    # --- File Uploads ---

    uploaded_files = st.file_uploader(
        "Upload Documents (Pitch Decks, Financials, Founder Profile, etc.)",
        type=["pdf", "docx", "pptx"],
        accept_multiple_files=True
    )

    doc_urls_text = st.text_area(
        "Enter all document URLs (one per line):",
        height=150,
        placeholder="https://storage.googleapis.com/.../Pitch Deck.pdf\nhttps://storage.googleapis.com/.../Financials.pdf"
    )
    st.caption("**Pitch deck is mandatory for the company analysis.**")
    
    # Optional: LinkedIn URLs (your schema has it, but API doesn't take it)
    # We can add this later if you update your backend to accept founder_linkedin_urls
    founder_linkedin = st.text_input("Founder LinkedIn URLs (optional, comma-separated)")

    if uploaded_files:
        # Upload files to Firebase Storage and get their public URLs
        try:
            company_id, file_urls = upload_company_and_docs(company_name, uploaded_files)
            doc_urls_text += "\n" + "\n".join(file_urls)
            st.success(f"Uploaded {len(uploaded_files)} files for {company_name}.")
        except Exception as e:
            st.error(f"Error uploading files: {e}")
            file_urls = []
    submitted = st.form_submit_button("Run Full Analysis", type="primary")

if submitted:
    if not company_name:
        st.warning("Please enter a company name.")
        st.stop()
        
    doc_urls = [url.strip() for url in doc_urls_text.split("\n") if url.strip()]
    
    if not doc_urls:
        st.warning("Please enter at least one document URL or upload files.")
        st.stop()

    # Validate URLs
    invalid_urls = [url for url in doc_urls if not URL_REGEX.match(url)]
    if invalid_urls:
        st.error(f"The following URLs appear to be invalid: {', '.join(invalid_urls)}")
        st.stop()
        
    # # All checks passed, run the analysis
    # # with st.spinner(f"Running analysis for {company_name}... This may take a few minutes."):
    # st.info(f"Running analysis for {company_name}... This may take a few minutes.")
    # success = run_analysis_pipeline(company_name, doc_urls)
    # print(st.session_state['api_response'])
    
    # if success:
    #     st.success(f"Analysis for {company_name} complete!")
    #     st.balloons()
    #     st.info("Redirecting to the First Pass Report...")
    #     st.switch_page("pages/3_First_Pass_Report.py")
    # else:
    #     st.error("Analysis failed. Please see the error message above.")


    # All checks passed, run the analysis
    # Use st.status for a spinner that can be updated by the client
    with st.status(f"Submitting analysis for {company_name}...", expanded=True) as status_ui:
        success = run_analysis_pipeline(company_name, doc_urls)
    
    if success:
        status_ui.update(label=f"Analysis for {company_name} complete!", state="complete")
        st.success(f"Analysis for {company_name} complete!")
        st.balloons()
        st.info("Redirecting to the First Pass Report...")
        st.switch_page("pages/3_First_Pass_Report.py")
    else:
        status_ui.update(label="Analysis failed.", state="error")
        st.error("Analysis failed. Please see the error message above.")