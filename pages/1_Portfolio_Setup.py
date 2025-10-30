import streamlit as st
import pandas as pd
import io

# --- Auth Check ---
if not st.session_state.get("authenticated", False):
    st.error("You must be logged in to view this page.")
    st.page_link("streamlit_app.py", label="Back to Login")
    st.stop()
# --- End Auth Check ---

st.title("Step 1: Portfolio and Thesis Setup")
st.write("Define your fund's investment thesis and current portfolio to enable synergy analysis.")

# --- Investment Thesis ---
st.header("Investment Thesis")
thesis_text = st.text_area(
    "Enter your fund's investment thesis:",
    value=st.session_state.vc_thesis,
    height=150
)
if st.button("Save Thesis"):
    st.session_state.vc_thesis = thesis_text
    st.success("Investment thesis updated!")

# --- Portfolio Companies ---
st.header("Portfolio Companies (for Synergy Analysis)")
st.write("Enter your portfolio companies, one per line.")

# Option 1: Text Area
portfolio_list_text = st.text_area(
    "Enter company names (one per line):",
    value="\n".join(st.session_state.portfolio_cos),
    height=200
)

# Option 2: CSV Upload
uploaded_file = st.file_uploader("Or upload a CSV/TXT file with one company name per row (first column only)")

if st.button("Save Portfolio Companies"):
    new_portfolio_list = []
    if uploaded_file:
        try:
            # Check if text or csv
            if uploaded_file.type == "text/csv":
                df = pd.read_csv(uploaded_file)
            else: # Assume text file
                string_data = uploaded_file.getvalue().decode("utf-8")
                df = pd.read_csv(io.StringIO(string_data), header=None)
            
            new_portfolio_list = df.iloc[:, 0].dropna().astype(str).tolist()
            st.session_state.portfolio_cos = list(set(new_portfolio_list)) # Remove duplicates
            st.success(f"Portfolio updated from file. Found {len(st.session_state.portfolio_cos)} companies.")
        
        except Exception as e:
            st.error(f"Error processing file: {e}")
    
    elif portfolio_list_text.strip():
        new_portfolio_list = [name.strip() for name in portfolio_list_text.split("\n") if name.strip()]
        st.session_state.portfolio_cos = list(set(new_portfolio_list)) # Remove duplicates
        st.success(f"Portfolio updated from text. Found {len(st.session_state.portfolio_cos)} companies.")
    
    else:
        st.warning("No input provided. Portfolio was not updated.")

st.subheader("Current Portfolio")
if st.session_state.portfolio_cos:
    st.dataframe(st.session_state.portfolio_cos, column_config={"value": "Company Name"}, use_container_width=True)
else:
    st.info("No portfolio companies entered yet.")

st.divider()
st.page_link("pages/2_Run_Analysis.py", label="Next Step: Run New Analysis", icon="➡️")