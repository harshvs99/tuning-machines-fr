import streamlit as st

# --- Auth Check ---
if not st.session_state.get("authenticated", False):
    st.error("You must be logged in to view this page.")
    st.page_link("streamlit_app.py", label="Back to Login")
    st.stop()
# --- End Auth Check ---

st.title("Step 3: First Pass Analysis Report (L1)")

# --- Data Check ---
if not st.session_state.get("api_response") or not st.session_state.get("analysis_complete", False):
    st.warning("No analysis data found. Please run a new analysis first.")
    st.page_link("pages/2_Run_Analysis.py", label="Run New Analysis")
    st.stop()
# --- End Data Check ---

# Load the reports from session state
try:
    l1_report = st.session_state.api_response['l1_analysis_report']
    scoring_report = st.session_state.api_response['scoring_report']
    company_name = l1_report.get('company_analysed', 'N/A')
    st.header(f"Analysis for: :orange[{company_name}]")
except (KeyError, TypeError) as e:
    st.error(f"Could not read analysis data from session state. Error: {e}")
    st.json(st.session_state.api_response)
    st.stop()

# --- Special Industry Check (Step 4 Requirement) ---
try:
    claimed_industry = l1_report['industry_analysis']['claimed_industry']
    activity_industry = l1_report['industry_analysis']['activity_based_industry']
    portfolio_cos = st.session_state.get('portfolio_cos', [])
    
    # Simple check if the new industry terms are in our portfolio list
    # (which is just names, so this is a proxy check)
    if activity_industry.lower() not in [c.lower() for c in portfolio_cos] and \
       claimed_industry.lower() not in [c.lower() for c in portfolio_cos]:
        
        st.info(
            f"**Synergy Alert:** The industry analysis identified new industries "
            f"('{claimed_industry}', '{activity_industry}') that may not be "
            f"covered by your current portfolio data. \n\n"
            f"You may want to return to the Portfolio Setup to add relevant "
            f"companies for a more accurate synergy analysis.",
            icon="💡"
        )
        st.page_link("pages/1_Portfolio_Setup.py", label="Go to Portfolio Setup")

except (KeyError, TypeError):
    pass # Don't fail if industry data is missing

# --- Display Tabs for 7 Agents ---
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
st.page_link("pages/4_Founder_Q&A.py", label="Next Step: Go to Founder Q&A", icon="➡️")