import streamlit as st
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/presentations"]

# --- THIS IS A COMPLEX SETUP ---
# 1. Go to Google Cloud Console, create a project.
# 2. Enable the "Google Slides API".
# 3. Create "OAuth 2.0 Client IDs" credentials for a "Desktop app".
# 4. Download the JSON file and rename it to `credentials.json` 
#    and place it in the *root* of your `tuning-machines-fr` directory.
#
# 5. The *first time* you run this, you must run it locally in your terminal.
#    It will open a browser window for you to log in and grant permission.
#    It will then save a `token.json` file.
# 6. This `token.json` stores your auth and should be KEPT SECRET.
#    For Streamlit Cloud, you'll need to store the *contents* of 
#    `token.json` and `credentials.json` in Streamlit's secrets.
# ---

CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def get_slides_service():
    """Authenticates and returns a Google Slides service client."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                st.error(f"Failed to refresh token: {e}. Please re-authenticate.")
                os.remove(TOKEN_FILE) # Remove bad token
                return None
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                st.error(f"Missing `credentials.json`. Please download it from GCP and place it in the root directory.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            # Note: This `run_local_server` will block and open a browser.
            # This is problematic for a deployed Streamlit app.
            # For deployment, you must pre-authorize and store the token.json
            # in Streamlit secrets.
            st.warning("Please check your terminal and browser to authenticate with Google.")
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    if creds:
        try:
            service = build('slides', 'v1', credentials=creds)
            return service
        except HttpError as err:
            st.error(f"Failed to build Google Slides service: {err}")
            return None
    return None

def create_deal_note(company_name: str, analysis_data: dict, chat_history: list):
    """
    Creates a new Google Slides presentation and returns its URL.
    This is a SCAFFOLD. You need to build the slide content.
    """
    service = get_slides_service()
    if not service:
        st.error("Failed to get Google Slides service. Cannot create deal note.")
        return None

    # 1. Get the data from your analysis
    # Example:
    l1_report = analysis_data.get('l1_analysis_report', {})
    founder_summary = l1_report.get('founder_analysis', {}).get('summary', 'N/A')
    product_summary = l1_report.get('product_analysis', {}).get('summary', 'N/A')
    
    scoring_report = analysis_data.get('scoring_report', {})
    founder_score = scoring_report.get('founder_assessment', {}).get('score', 0)
    
    # 2. Define the presentation body (Title slide)
    title = f"Deal Note: {company_name}"
    body = {
        'title': title
    }
    
    try:
        # Create the presentation
        presentation = service.presentations().create(body=body).execute()
        presentation_url = presentation.get('presentationUrl')
        presentation_id = presentation.get('presentationId')

        st.success(f"Successfully created presentation: [Open Google Slide]({presentation_url})")

        # 3. --- THIS IS WHERE YOU ADD CONTENT ---
        # Now, you must make batchUpdate requests to add slides and content.
        # This is complex and specific to your desired format.
        # Example: Add a new slide with a title and body
        
        requests_body = [
            {
                'createSlide': {
                    'slideLayoutReference': {
                        'predefinedLayout': 'TITLE_AND_BODY'
                    }
                }
            },
            {
                'insertText': {
                    'objectId': 'SLIDES_API_PRESENTATION_ID_TITLE_1', # You need to get the real IDs
                    'text': 'Founder Analysis'
                }
            },
             {
                'insertText': {
                    'objectId': 'SLIDES_API_PRESENTATION_ID_BODY_1', # You need to get the real IDs
                    'text': f"Score: {founder_score}/5\n\nSummary: {founder_summary}"
                }
            }
        ]
        
        # This part is complex and requires you to get the IDs from the
        # created slide. For a real implementation, you'd create one slide,
        # get its element IDs, then populate them.
        
        # st.info("Slide content generation is a scaffold. See `utils/gslides_client.py` to build it out.")


        return presentation_url

    except HttpError as err:
        st.error(f"An error occurred while creating the Google Slide: {err}")
        return None