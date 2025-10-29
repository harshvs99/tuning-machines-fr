import streamlit as st

# --- Auth Check ---
if not st.session_state.get("authenticated", False):
    st.error("You must be logged in to view this page.")
    st.page_link("streamlit_app.py", label="Back to Login")
    st.stop()
# --- End Auth Check ---

st.title("Step 5: Final Report")

# --- Data Check ---
if not st.session_state.get("api_response") or not st.session_state.get("analysis_complete", False):
    st.warning("No analysis data found. Please run a new analysis first.")
    st.page_link("pages/2_Run_Analysis.py", label="Run New Analysis")
    st.stop()
# --- End Data Check ---

st.info("This view is similar to the First Pass Report. In a real-world scenario, this page would show an *updated* analysis that incorporates the feedback from the Founder Q&A session. Since your backend doesn't support that 'update' step yet, this page will currently mirror the First Pass Report.")

# --- Re-using the L1 Report Display ---
# (In a real app, this would point to a *new* report, 
#  e.g., `st.session_state.api_response_final`)
l1_report = st.session_state.api_response['l1_analysis_report']
scoring_report = st.session_state.api_response['scoring_report']
company_name = l1_report.get('company_analysed', 'N/A')
st.header(f"Final Analysis for: :orange[{company_name}]")

# Display Tabs for 7 Agents
tab_names = [
    "1. Founder", "2. Industry", "3. Product", 
    "4. Externalities", "5. Competition", "6. Financials", "7. Synergies"
]
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(tab_names)

def display_score(assessment_name: str):
    """Helper to display a score box."""
    try:
        score_data = scoring_report[assessment_name]
        score = score_data.get('score', 'N/A')
        rating = score_data.get('rating', 'N/A')
        rationale = score_data.get('rationale', 'N/A')
        st.subheader(f"Overall Assessment: {score}/5 ({rating})")
        st.caption(rationale)
    except KeyError:
        st.warning(f"No scoring data found for '{assessment_name}'.")

with tab1:
    display_score("founder_assessment")
    st.divider()
    st.json(l1_report.get('founder_analysis'), expanded=True)

with tab2:
    display_score("industry_assessment")
    st.divider()
    st.json(l1_report.get('industry_analysis'), expanded=True)

# ... (repeat for all other tabs) ...

with tab3:
    display_score("product_assessment")
    st.divider()
    st.json(l1_report.get('product_analysis'), expanded=True)

with tab4:
    display_score("externalities_assessment")
    st.divider()
    st.json(l1_report.get('externalities_analysis'), expanded=True)

with tab5:
    display_score("competition_assessment")
    st.divider()
    st.json(l1_report.get('competition_analysis'), expanded=True)

with tab6:
    display_score("financial_assessment")
    st.divider()
    st.json(l1_report.get('financial_analysis'), expanded=True)
    
with tab7:
    display_score("synergy_assessment")
    st.divider()
    st.json(l1_report.get('synergy_analysis'), expanded=True)


st.divider()
st.page_link("pages/6_Generate_Deal_Note.py", label="Next Step: Generate Deal Note", icon="➡️")