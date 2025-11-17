# FILE: tuning-machines-fr/pages/6_Generate_Deal_Note.py
import streamlit as st
from utils.gslides_client import call_gas_action # <-- Our new GAS helper
from utils.api_client import run_slide_generation_pipeline 

# --- Auth Check ---
if not st.session_state.get("authenticated", False):
    st.error("You must be logged in to view this page.")
    st.page_link("streamlit_app.py", label="Back to Login")
    st.stop()
# --- End Auth Check ---

st.title("Step 6: Generate Deal Note 📑")
st.info("This process orchestrates 3 network calls: 1 to Google to create a template, 1 to the AI backend to populate it, and 1 to Google to build the final presentation.")

# --- Data Check ---
if not st.session_state.get("api_response") or not st.session_state.get("analysis_complete", False):
    st.warning("No analysis data found. Please run a new analysis first.")
    st.page_link("pages/2_Run_Analysis.py", label="Run New Analysis")
    st.stop()

if "current_company_id" not in st.session_state:
    st.error("No `company_id` found in session state. Please go back to Step 1 or 2.")
    st.stop()
# --- End Data Check ---

company_id = st.session_state.current_company_id
api_data = st.session_state.api_response
company_name = api_data.get('l1_analysis_report', {}).get('company_analysed', company_id)
st.subheader(f"Preparing to generate Deal Note Deck for: {company_name}")


# if st.button(f"Generate Google Slide for {company_name}", type="primary", use_container_width=True):
    
#     try:
#         # --- STEP 1: Call GAS to create the template ---
#         with st.spinner("Step 1/3: Calling Google Apps Script to create template sheet..."):
#             template_result = call_gas_action(action='run', mode='template')
#             if not template_result or template_result.get('status') != 'success':
#                 st.error("Failed to create presentation template.")
#                 st.json(template_result) # Show error details
#                 st.stop()
#         st.write("✅ Step 1 complete: Template sheet created.")

#         # --- STEP 2: Call Python AI backend to populate the sheet ---
#         # This function (run_slide_generation_pipeline) handles its own spinner/polling
#         st.write("Step 2/3: Calling AI backend to populate sheet... (This may take a few minutes)")
#         success = run_slide_generation_pipeline(
#             company_id=company_id,
#             current_analysis=api_data
#         )
#         if not success:
#             st.error("Failed to populate content sheet with AI.")
#             st.stop()
#         st.write("✅ Step 2 complete: Content sheet populated by AI.")

#         # --- STEP 3: Call GAS to generate the final slides ---
#         with st.spinner("Step 3/3: Calling Google Apps Script to generate final presentation..."):
#             slides_result = call_gas_action(action='run', mode='slides')
#             if not slides_result or slides_result.get('status') != 'success' or not slides_result.get('url'):
#                 st.error("Failed to generate the final presentation.")
#                 st.json(slides_result) # Show error details
#                 st.stop()
#         st.write("✅ Step 3 complete: Final presentation generated.")
        
#         # --- SUCCESS ---
#         final_url = slides_result.get('url')
#         st.success(f"**Presentation successfully generated!**")
#         st.markdown(f"## [Click here to open the new presentation]({final_url})")

#     except Exception as e:
#         st.error(f"An unexpected error occurred during the orchestration: {e}")

if st.button(f"Generate Google Slide for {company_name}", type="primary", use_container_width=True):
    
    final_url = run_slide_generation_pipeline(api_data)
        
    if final_url:
        st.success(f"**Presentation successfully generated!**")
        st.markdown(f"## [Click here to open the new presentation]({final_url})")
    else:
        st.error("Failed to generate the presentation. Check the error messages above.")

st.divider()
st.header("Data to be included:")
st.json(api_data, expanded=False)