import streamlit as st
import pandas as pd
import io
from utils.firebase_client import update_fund_config

# --- Auth Check ---
if not st.session_state.get("authenticated", False):
    st.error("You must be logged in to view this page.")
    st.page_link("streamlit_app.py", label="Back to Login")
    st.stop()
# --- End Auth Check ---

# Define the score labels
SCORE_LABELS = {
    1: "1 - No Faith",
    2: "2 - Low Conviction",
    3: "3 - Neutral",
    4: "4 - High Conviction",
    5: "5 - Extremely Optimistic"
}

st.title("Step 1: Portfolio and Thesis Setup")
st.write("Define your fund's investment thesis, industry preferences, and current portfolio.")

# --- NEW: Section for Scoring New Industries ---
if st.session_state.new_industries_to_score:
    st.subheader(":sparkles: New Industries Found to Score")
    st.info("Your last analysis identified the following industries that aren't in your preferences list. Please score them.")
    
    new_scores = {}

    with st.form("new_industry_scores_form"):
        for industry in st.session_state.new_industries_to_score:
            st.write(f"**{industry}**")
            
            # --- FIX: Changed st.slider to st.select_slider ---
            new_scores[industry] = st.select_slider(
                f"Score for {industry}",
                options=[1, 2, 3, 4, 5], # Define the steps
                value=3,
                format_func=lambda x: SCORE_LABELS[x], # Apply labels
                label_visibility="collapsed"
            )
        
        submitted = st.form_submit_button("Save New Scores")
        if submitted:
            # Update the main preferences dict
            st.session_state.industry_preferences.update(new_scores)
            update_fund_config("industry_preferences", st.session_state.industry_preferences) # <-- ADD THIS
            # Clear the "to-score" list
            st.session_state.new_industries_to_score = []
            st.success("New industry preferences saved!")
            st.rerun() # Rerun to hide this section

st.divider()

# --- Investment Thesis (Wrapped in Form) ---
st.header("Investment Thesis")
with st.form("thesis_form"):
    thesis_text = st.text_area(
        "Enter your fund's investment thesis:",
        value=st.session_state.vc_thesis,
        height=150
    )
    if st.form_submit_button("Save Thesis"):
        st.session_state.vc_thesis = thesis_text
        update_fund_config("vc_thesis", thesis_text) # <-- ADD THIS
        st.success("Investment thesis updated!")

st.divider()

# --- NEW: Industry Preferences (Wrapped in Form) ---
st.header("Industry Preferences")
st.write("Manage your scored industries. This list will grow as new analyses are run.")
st.caption("Score Legend: 1 - No Faith, 2 - Low Conviction, 3 - Neutral, 4 - High Conviction, 5 - Extremely Optimistic")

with st.form("industry_pref_form"):
    # 1. Convert dict to a DataFrame for the editor
    pref_df = pd.DataFrame(
        st.session_state.industry_preferences.items(),
        columns=["Industry", "Score (1-5)"]
    )

    # 2. Display the data editor
    edited_df = st.data_editor(
        pref_df,
        num_rows="dynamic",  # Allow adding/deleting rows
        width='stretch',
        column_config={
            "Industry": st.column_config.TextColumn(
                "Industry Name",
                required=True,
            ),
            "Score (1-5)": st.column_config.NumberColumn(
                "Score (1-5)",
                min_value=1,
                max_value=5,
                step=1,
                required=True,
            )
        }
    )

    # 3. Save button to update session state
    if st.form_submit_button("Save Industry Preferences"):
        # Convert DataFrame back to dictionary
        edited_df = edited_df.dropna(subset=["Industry"])
        edited_df["Score (1-5)"] = edited_df["Score (1-5)"].astype(int)
        st.session_state.industry_preferences = dict(
            zip(edited_df["Industry"], edited_df["Score (1-5)"])
        )
        update_fund_config("industry_preferences", st.session_state.industry_preferences) # <-- ADD THIS
        st.success("Industry preferences updated!")

st.divider()

# --- Portfolio Companies (Wrapped in Form) ---
st.header("Portfolio Companies (for Synergy Analysis)")
st.write("Enter your portfolio companies, one per line.")

with st.form("portfolio_form"):
    # Option 1: Text Area
    portfolio_list_text = st.text_area(
        "Enter company names (one per line):",
        value="\n".join(st.session_state.portfolio_cos),
        height=200
    )

    # Option 2: CSV Upload
    uploaded_file = st.file_uploader("Or upload a CSV/TXT file with one company name per row (first column only)")

    if st.form_submit_button("Save Portfolio Companies"):
        new_portfolio_list = []
        if uploaded_file:
            try:
                if uploaded_file.type == "text/csv":
                    df = pd.read_csv(uploaded_file)
                else: # Assume text file
                    string_data = uploaded_file.getvalue().decode("utf-8")
                    df = pd.read_csv(io.StringIO(string_data), header=None)
                
                new_portfolio_list = df.iloc[:, 0].dropna().astype(str).tolist()
                st.session_state.portfolio_cos = list(set(new_portfolio_list)) # Remove duplicates
                update_fund_config("portfolio_cos", st.session_state.portfolio_cos) # <-- ADD THIS
                st.success(f"Portfolio updated from file. Found {len(st.session_state.portfolio_cos)} companies.")
            
            except Exception as e:
                st.error(f"Error processing file: {e}")
        
        elif portfolio_list_text.strip():
            new_portfolio_list = [name.strip() for name in portfolio_list_text.split("\n") if name.strip()]
            st.session_state.portfolio_cos = list(set(new_portfolio_list)) # Remove duplicates
            update_fund_config("portfolio_cos", st.session_state.portfolio_cos) # <-- ADD THIS
            st.success(f"Portfolio updated from text. Found {len(st.session_state.portfolio_cos)} companies.")
        
        else:
            st.warning("No input provided. Portfolio was not updated.")

st.subheader("Current Portfolio")
if st.session_state.portfolio_cos:
    st.dataframe(st.session_state.portfolio_cos, column_config={"value": "Company Name"}, width='stretch')
else:
    st.info("No portfolio companies entered yet.")

st.divider()
st.page_link("pages/2_Run_Analysis.py", label="Next Step: Run New Analysis", icon="➡️")