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
    firebase_config = st.secrets.firebase
    PROJECT_ID = firebase_config.project_id
    DATABASE_ID = firebase_config.FIRESTORE_DATABASE_ID
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

# 7. Get the storage bucket (uses the initialized app's context)
bucket = storage.bucket(name=BUCKET_NAME)
# --- End Firebase Init ---

# --- End Firebase Init ---

# # --- File Uploads ---
# uploaded_files = st.file_uploader(
#     "Upload Documents (Pitch Decks, Financials, Founder Profile, etc.)",
#     type=["pdf", "docx", "pptx"],
#     accept_multiple_files=True
# )

# Get current time 
# now = datetime.now(timezone.utc)      # timezone-aware UTC datetime
now = datetime.now() 
iso_now = now.isoformat()             # JSON-safe string

def upload_company_and_docs(company_name, uploaded_files):
    """Uploads company info and documents to Firestore and Cloud Storage."""
    try:
        company_ref = db.collection("companies").add({
            "company_analysed": company_name,
            "created_at": iso_now,
            "updated_at": iso_now
        })

        # Get the company id
        company_id = company_ref[1].id if isinstance(company_ref, tuple) else company_ref.id
        # document_name = f"{'_'.join(company_name.split())}_{company_id}"

        # Upload docs to Google Storage
        file_urls = []
        for file in uploaded_files:
            # blob = bucket.blob(f"companies/{company_id}/{file.name}")
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
    
# --- End File Uploads ---
