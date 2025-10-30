import streamlit as st
import logging
logging.basicConfig(level=logging.ERROR, filename="app.log")

# Set page config as the first Streamlit command
st.set_page_config(
    page_title="VC Investment Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Hardcoded Password (for internal tools) ---
# TODO: For a real app, use a proper auth service (e.g., Streamlit's built-in 
# st.experimental_user, Okta, Auth0)
# This is a simple placeholder.
VALID_PASSWORD = "123" 

def check_password():
    """Returns `True` if the user has the correct password."""
    if st.session_state.get("authenticated", False):
        return True

    st.title("Automated Investment Analyst Login 🤖")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        st.session_state["authenticated"] = True
        st.rerun()  # Rerun the script to reflect the authenticated state
        # if password == VALID_PASSWORD:
        #     st.session_state["authenticated"] = True
        #     st.rerun()  # Rerun the script to reflect the authenticated state
        # else:
        #     st.error("The password you entered is incorrect.")
    
    return False

# --- Initialize Session State ---
def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "vc_thesis" not in st.session_state:
        # st.session_state["vc_thesis"] = "Set your VC Thesis in the Portfolio Setup tab. (Eg. Our fund invests in early-stage (Seed, Series A) B2B SaaS companies in India with a strong technical founder."
        st.session_state["vc_thesis"] = "Our fund invests in early-stage (Seed, Series A) B2B companies in India with a strong technical founder."
    if "portfolio_cos" not in st.session_state:
        st.session_state["portfolio_cos"] = []
    if "api_response" not in st.session_state:
        st.session_state["api_response"] = None
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "analysis_complete" not in st.session_state:
        st.session_state["analysis_complete"] = False

# --- Main App ---
init_session_state()

if not check_password():
    # If not authenticated, stop the script here.
    # The login form is already shown in check_password().
    st.stop()

# --- Authenticated App ---
# If we are here, the user is authenticated.
st.sidebar.success("You are logged in.")
# st.sidebar.page_link("streamlit_app.py", label="Home / Login")
# st.sidebar.page_link("/", label="Home / Login")
st.sidebar.page_link("streamlit_app.py", label="Home / Login")

st.sidebar.header("Analysis Workflow")
st.sidebar.page_link("pages/1_Portfolio_Setup.py", label="1. Portfolio Setup")
st.sidebar.page_link("pages/2_Run_Analysis.py", label="2. Run New Analysis")
st.sidebar.page_link("pages/3_First_Pass_Report.py", label="3. First Pass Report")
st.sidebar.page_link("pages/4_Founder_Q&A.py", label="4. Founder Q&A")
st.sidebar.page_link("pages/5_Final_Report.py", label="5. Final Report")
# st.sidebar.page_link("pages/6_Generate_Deal_Note.py", label="6. Generate Deal Note")

st.title("Welcome to the Automated Investment Analyst 🤖")
st.write("Use the navigation on the left to start your workflow.")
st.header("Current State")
st.write(f"**Investment Thesis:** {st.session_state.vc_thesis}")
st.write(f"**Portfolio Companies:** {', '.join(st.session_state.portfolio_cos) if st.session_state.portfolio_cos else 'None'}")
st.divider()
st.page_link("pages/1_Portfolio_Setup.py", label="Setup your Portfolio", icon="➡️")

if st.session_state.api_response:
    company = st.session_state.api_response.get('l1_analysis_report', {}).get('company_analysed', 'N/A')
    st.subheader(f"Current Analysis in Memory: :orange[{company}]")
    st.page_link("pages/3_First_Pass_Report.py", label="Go to report")
else:
    st.info("No analysis has been run yet. Go to the 'Run New Analysis' page to start.")