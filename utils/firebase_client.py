from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import storage
from logging import Logger
from pytz import timezone
import streamlit as st
import os

Logger = st.logger if hasattr(st, 'logger') else None

# --- Initialize Firebase once ---
# firebase_secrets = dict(st.secrets["firebase"])
firebase_cred_path = st.secrets.get("FIREBASE_CREDENTIALS_PATH", "")
if firebase_cred_path and os.path.exists(firebase_cred_path):
    import json
    with open(firebase_cred_path, 'r') as f:
        firebase_secrets = json.load(f)
else:
    firebase_secrets = dict(st.secrets["firebase"])

# Initialize Firebase
cred = credentials.Certificate(firebase_secrets)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
    "storageBucket": f"{firebase_secrets['project_id']}.firebasestorage.app"
})

db = firestore.client()
bucket = storage.bucket()
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

        # Upload docs to Google Storage
        file_urls = []
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
        if Logger:
            Logger.error(f"Error uploading company and documents: {e}")
        raise e
    return None, []
# --- End File Uploads ---
