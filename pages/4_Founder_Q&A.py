import streamlit as st
import time

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

# --- Load Follow-up Questions ---
try:
    discrepancy_report = st.session_state.api_response['discrepancy_report']
    questions = discrepancy_report.get('follow_up_questions', [])
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Initialize chat history with the follow-up questions
    if not st.session_state.chat_history:
        initial_prompt = "Hello! Based on our initial analysis, we have a few follow-up questions to better understand your business:\n\n"
        for i, q in enumerate(questions, 1):
            initial_prompt += f"{i}. {q}\n"
        
        st.session_state.chat_history.append({"role": "assistant", "content": initial_prompt})

except (KeyError, TypeError) as e:
    st.error(f"Could not read follow-up questions from analysis data. Error: {e}")
    st.json(st.session_state.api_response)
    st.stop()

# --- Display Chat Messages ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Input ---
if prompt := st.chat_input("Your (the founder's) response..."):
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Dummy Assistant Response ---
    # In a real app, you might send this 'prompt' back to a 
    # generative AI model to get a smart reply.
    # For now, we'll just acknowledge receipt.
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = "Thank you for providing that clarification. We are noting this down."
        
        # Simulate stream of response with milliseconds delay
        for chunk in full_response.split():
            message_placeholder.markdown(chunk + " ")
            time.sleep(0.05)
        message_placeholder.markdown(full_response)
        
    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
    
st.divider()
st.page_link("pages/5_Final_Report.py", label="Next Step: Go to Final Report", icon="➡️")