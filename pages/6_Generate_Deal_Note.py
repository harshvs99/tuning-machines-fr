import streamlit as st
import pandas as pd
from utils.api_client import run_slide_generation # <-- Your existing import

# --- Auth Check ---
if not st.session_state.get("authenticated", False):
    st.error("You must be logged in to view this page.")
    st.page_link("streamlit_app.py", label="Back to Login")
    st.stop()
# --- End Auth Check ---

st.title("📄 Generate Deal Note (Google Slides)")

# --- Data Check ---
if not st.session_state.get("api_response") or not st.session_state.get("analysis_complete", False):
    st.warning("No analysis data found. Please run a new analysis first.")
    st.page_link("pages/2_Run_Analysis.py", label="Run New Analysis")
    st.stop()
    
company_id = st.session_state.get("current_company_id")
if not company_id:
    st.error("Error: No 'current_company_id' found in session. Please load the report from the History page again.")
    st.page_link("pages/0_Analysis_History.py", label="Go to Analysis History")
    st.stop()
# --- End Data Check ---

# --- Load Key Data ---
company_name = st.session_state.api_response.get('l1_analysis_report', {}).get('company_analysed', 'N/A')
api_data = st.session_state.api_response
chat_history = st.session_state.get('chat_history', [])

# --- Main Action Container ---
with st.container(border=True):
    st.subheader(f"Generate Report for: {company_name}")
    st.markdown("""
    This will trigger the complete backend AI pipeline:
    1.  **AI Content Generation:** Agents will generate text for each slide.
    2.  **Sheet Population:** A Google Sheet will be filled with this content.
    3.  **Slide Creation:** Google Apps Script will build the final presentation.

    This process may take **2-3 minutes**. You can monitor the progress below.
    """)

    if st.button(f"🚀 Generate Google Slide for {company_name}", type="primary", width='content'):
        
        presentation_url = None
        with st.status("Generating Deal Note... This may take 2-3 minutes.", expanded=True) as status:
            
            status.write("Submitting job to backend...")
            
            presentation_url = run_slide_generation(
                company_id=company_id,
                current_analysis=api_data
            )
            
            if presentation_url:
                status.update(label="Deal Note generated successfully!", state="complete")
            else:
                status.update(label="Failed to generate Deal Note.", state="error")

        # Display result outside the status box
        if presentation_url:
            st.success(f"Successfully created deal note!")
            st.markdown(f"### [Click here to open the Google Slide]({presentation_url})")
            st.balloons()
        else:
            st.error("Failed to generate deal note. Check the errors above or the backend logs.")

st.divider()

# --- Data Summary Section ---
st.header("Data Summary")
st.caption("This is a preview of the data that will be used to generate the slides.")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("📊 Final Scores (Post-Q&A)")
        scoring_data = api_data.get('scoring_report', {})
        
        # Extract scores into a more readable format
        scores = {
            "Founder": scoring_data.get("founder_assessment", {}).get("score", "N/A"),
            "Industry": scoring_data.get("industry_assessment", {}).get("score", "N/A"),
            "Product": scoring_data.get("product_assessment", {}).get("score", "N/A"),
            "Externalities": scoring_data.get("externalities_assessment", {}).get("score", "N/A"),
            "Competition": scoring_data.get("competition_assessment", {}).get("score", "N/A"),
            "Financials": scoring_data.get("financial_assessment", {}).get("score","NOT_FOUND"),
            "Synergies": scoring_data.get("synergy_assessment", {}).get("score", "N/A"),
        }
        
        scores_df = pd.DataFrame(scores.items(), columns=["Factor", "Score"])
        st.dataframe(
            scores_df,
            width='content',
            hide_index=True,
            column_config={
                "Factor": st.column_config.TextColumn("Factor"),
                "Score": st.column_config.ProgressColumn(
                    "Score",
                    min_value=0,
                    max_value=5,
                    format="%d/5",
                ),
            }
        )

with col2:
    with st.container(border=True):
        st.subheader("💬 Founder Q&A")
        if not chat_history:
            st.info("No Q&A session was run for this analysis.")
        else:
            user_responses = [msg for msg in chat_history if msg.get("role") == "user"]
            st.metric("Total Questions Answered", len(user_responses))
            
            with st.expander("View Full Q&A Transcript"):
                for message in chat_history:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

# Expander for the full raw data, for debugging
with st.expander("View Data for building Deal Note"):
    st.json(api_data)