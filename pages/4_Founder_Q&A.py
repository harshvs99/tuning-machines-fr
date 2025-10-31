import streamlit as st
import time
from utils.api_client import run_update_pipeline # <-- NEW IMPORT

# --- Auth Check ---
if not st.session_state.get("authenticated", False):
    st.error("You must be logged in to view this page.")
    st.page_link("streamlit_app.py", label="Back to Login")
    st.stop()
# --- End Auth Check ---

st.title("Step 4: Founder Q&A")

# --- Data Check ---
if not st.session_state.get("api_response") or not st.session_state.get("analysis_complete", False):
    st.warning("No analysis data found. Please run a new analysis first.")
    st.page_link("pages/2_Run_Analysis.py", label="Run New Analysis")
    st.stop()
# --- End Data Check ---

# --- Q&A State Initialization (from Feature 1 - Unchanged) ---
try:
    if 'qa_questions_list' not in st.session_state:
        discrepancy_report = st.session_state.api_response['discrepancy_report']
        questions = discrepancy_report.get('follow_up_questions', [])
        
        if not questions:
            st.session_state.qa_questions_list = []
            st.session_state.qa_current_index = 0
            st.session_state.qa_complete = True
        else:
            st.session_state.qa_questions_list = questions
            st.session_state.qa_current_index = 0
            st.session_state.qa_complete = False 
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if not st.session_state.chat_history and not st.session_state.qa_complete:
        initial_prompt = "Hello! Based on our initial analysis, we have a few follow-up questions to better understand your business."
        st.session_state.chat_history.append({"role": "assistant", "content": initial_prompt})
        
        first_question = st.session_state.qa_questions_list[0]
        st.session_state.chat_history.append({"role": "assistant", "content": first_question})

except (KeyError, TypeError) as e:
    st.error(f"Could not read follow-up questions from analysis data. Error: {e}")
    st.json(st.session_state.api_response)
    st.stop()


# --- Display Chat Messages (Unchanged) ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Input Logic (from Feature 1 - Unchanged) ---
if st.session_state.qa_complete:
    st.info("You have completed all the follow-up questions.")
    chat_placeholder = "All questions answered. Proceed to the next step."
    is_disabled = True
else:
    chat_placeholder = "Your (the founder's) response..."
    is_disabled = False

if prompt := st.chat_input(chat_placeholder, disabled=is_disabled):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.qa_current_index += 1
    
    if st.session_state.qa_current_index < len(st.session_state.qa_questions_list):
        next_question = st.session_state.qa_questions_list[st.session_state.qa_current_index]
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = next_question
            for chunk in full_response.split():
                message_placeholder.markdown(chunk + " ")
                time.sleep(0.05)
            message_placeholder.markdown(full_response)
        st.session_state.chat_history.append({"role": "assistant", "content": full_response})
    
    else:
        st.session_state.qa_complete = True
        final_message = "Thank you for providing those clarifications. All questions are complete. You can now generate the final report."
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            for chunk in final_message.split():
                message_placeholder.markdown(chunk + " ")
                time.sleep(0.05)
            message_placeholder.markdown(final_message)
        st.session_state.chat_history.append({"role": "assistant", "content": final_message})
        st.rerun()

st.divider()

if st.session_state.qa_complete:
    st.info("The Q&A is complete. Click the button below to generate the final, updated report.")
    
    if st.button("Generate Final Report", type="primary"):
        # Check for the company_id we stored
        if 'current_company_id' not in st.session_state:
            st.error("Error: No company ID found in session. Please reload from history.")
            st.stop()
            
        company_id = st.session_state.current_company_id
        
        with st.status("Submitting Q&A and re-running analysis... This may take a few minutes.", expanded=True) as status_ui:
            success = run_update_pipeline(
                company_id=company_id,
                current_analysis=st.session_state.api_response,
                chat_history=st.session_state.chat_history
            )
        
        if success:
            status_ui.update(label="Final report generated successfully!", state="complete")
            st.success("Final report generated!")
            st.balloons()
            time.sleep(2)
            st.switch_page("pages/5_Final_Report.py")
        else:
            status_ui.update(label="Failed to generate final report.", state="error")
            st.error("Failed to generate the final report. Please check the errors above.")
else:
    st.page_link("pages/5_Final_Report.py", label="Next Step: Go to Final Report", icon="➡️")
    st.caption("Note: The final report will not include Q&A until you complete the session above.")
