# utils/firebase_client.py

from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud.firestore import Client as FirestoreClient  # <-- Keep this
from google.oauth2 import service_account  # <-- Add this import
import streamlit as st
import os

# --- Use logger instance ---
logger = st.logger.get_logger(__name__) 
# --- End logger instance ---

# --- Initialize Firebase once ---

# 1. Load the credential path from secrets
firebase_cred_path = st.secrets.get("FIREBASE_CREDENTIALS_PATH", "")
if not firebase_cred_path or not os.path.exists(firebase_cred_path):
    logger.error("FIREBASE_CREDENTIALS_PATH not found in secrets or file is missing.")
    st.error("Firebase credentials not found. App cannot start.")
    st.stop()
    
# 2. Load the config strings from the [firebase] section
try:
    PROJECT_ID = st.secrets.firebase.project_id
    DATABASE_ID = st.secrets.FIRESTORE_DATABASE_ID
except Exception as e:
    logger.error(f"Could not load values from [firebase] in secrets: {e}")
    st.error("Firebase configuration is missing from secrets.toml.")
    st.stop()

# BUCKET_NAME = f"{PROJECT_ID}.appspot.com" # Standard Firebase bucket name
BUCKET_NAME = f"{PROJECT_ID}.firebasestorage.app"

# --- Create TWO distinct credential objects ---

# 3. Create the firebase-admin credential (for app init and storage)
cred_firebase = credentials.Certificate(firebase_cred_path)

# 4. Create the google-auth credential (for FirestoreClient)
#    This is the object that FirestoreClient expects.
cred_google_auth = service_account.Credentials.from_service_account_file(firebase_cred_path)

# --- End credential creation ---

# 5. Initialize the Firebase app (using its credential)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred_firebase, {
        "storageBucket": BUCKET_NAME
    })

# --- Get clients ---


# 6. Use FirestoreClient (with the google-auth credential)
db = FirestoreClient(
    project=PROJECT_ID,
    credentials=cred_google_auth, # <-- Use the correct credential object
    database=DATABASE_ID
)

bucket = storage.bucket(name=BUCKET_NAME)
# --- End Firebase Init ---

now = datetime.now() 
iso_now = now.isoformat()             # JSON-safe string

def upload_company_and_docs(company_name, uploaded_files):
    """Uploads company info and documents to Firestore and Cloud Storage."""
    if not company_name:
        raise ValueError("Company name cannot be empty.")
        
    try:
        # Create a document with an initial pending status
        company_ref, doc_ref = db.collection("companies").add({
            "company_analysed": company_name,
            "analysis_status": "Pending",
            "created_at": iso_now,
            "updated_at": iso_now
        })

        # Get the company id
        company_id = doc_ref.id

        # Upload docs to Google Storage
        file_urls = []
        if uploaded_files:
            for file in uploaded_files:
                blob = bucket.blob(f"companies/{company_id}/{file.name}")
                blob.upload_from_file(file, content_type=file.type)

                # Make file public (for demo purposes)
                blob.make_public()
                file_url = blob.public_url
                file_urls.append(file_url)

                # Save file metadata in Firestore
                db.collection("companies").document(company_id).collection("documents").add({
                    "file_name": file.name,
                    "file_type": file.type,
                    "storage_url": file_url,
                    "uploaded_at": iso_now
                })
        return company_id, file_urls
    except Exception as e:
        logger.error(f"Error uploading company and documents: {e}")
        raise e

# --- NEW FUNCTION 1: Save Analysis ---
def save_analysis_to_firestore(company_id: str, analysis_data: dict):
    """
    Saves the completed analysis JSON blob to the company's Firestore document.
    """
    try:
        company_ref = db.collection("companies").document(company_id)
        company_ref.update({
            "analysis_report": analysis_data,  # Save the whole JSON blob
            "analysis_status": "Complete",     # Mark as complete
            "updated_at": datetime.now().isoformat()
        })
        logger.info(f"Successfully saved analysis for company {company_id}")
    except Exception as e:
        # Log the error but don't stop the app. The user still has the
        # analysis in their session.
        logger.error(f"Error saving analysis to Firestore for {company_id}: {e}")
        st.error(f"Note: Could not save analysis to database. Error: {e}")

# --- NEW FUNCTION 2: Get Analyses ---
def get_all_analyses():
    """
    Fetches all companies with completed analyses, ordered by
    last updated (newest first).
    """
    try:
        companies_ref = db.collection("companies")
        
        # Create a query to get completed analyses, ordered by 'updated_at'
        query = companies_ref.where(
            filter=firestore.FieldFilter("analysis_status", "==", "Complete")
        ).order_by(
            "updated_at", direction=firestore.Query.DESCENDING
        )
        
        docs = query.stream()
        
        analyses = []
        for doc in docs:
            data = doc.to_dict()
            data["company_id"] = doc.id  # Add the doc ID for keying
            analyses.append(data)
            
        return analyses
    except Exception as e:
        logger.error(f"Error fetching all analyses: {e}")
        st.error(f"Could not load analysis history: {e}")
        return []