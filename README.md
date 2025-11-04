# 🚀 AI Analyst for Startup Evaluation

An **AI-powered analyst platform** that helps investors evaluate startups by synthesizing founder materials and public data into **concise, actionable deal notes and dashboards**. Built with **Streamlit, Firebase, and Google Gemini**. You can access the website [here](https://tuning-machines.uc.r.appspot.com/)

---

## 📌 Features

* **Company Registration**

  * Add startups with details like sector, stage, HQ, and founder profiles.
  * Store structured data in Firebase Firestore.

* **Document Ingestion**

  * Upload pitch decks, revenue decks, or resumes.
  * Extract text using OCR and parse into structured insights.

* **Automated Analysis**

  * Founder strengths & gaps
  * Industry & product positioning
  * Competition mapping
  * Financial benchmarks
  * External risks & sensitivities

* **Interactive Dashboard**

  * Select a company from the database
  * View structured analysis, risks, and summaries
  * Key metrics displayed with visual indicators

* **Chat with the Data** 💬

  * Ask natural-language questions about the company’s analysis
  * Powered by **Gemini 1.5 Flash**

---

## 🛠️ Tech Stack

* **Frontend & UI**: [Streamlit](https://streamlit.io/)
* **Database**: [Firebase Firestore](https://firebase.google.com/docs/firestore)
* **Authentication & Storage**: Firebase Admin SDK
* **LLM**: [Google Gemini API](https://ai.google.dev/) (`gemini-1.5-flash`)

<!-- ---

## 📂 Project Structure

```
.
├── app.py                   # Main Streamlit app
├── pages/                   # Multi-page Streamlit UI
│   ├── 1_Register_Company.py
│   ├── 2_Dashboard.py
│   └── 3_Chat.py
├── requirements.txt         # Python dependencies
├── README.md                # Project docs
└── .streamlit/
    └── secrets.toml         # Secrets for Firebase & Gemini
```

--- -->

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/ai-analyst.git
cd ai-analyst
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure secrets

Create `.streamlit/secrets.toml` with:

```toml
GOOGLE_API_KEY = "your-gemini-api-key"

FIREBASE_KEY = """
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk@your-project.iam.gserviceaccount.com",
  ...
}
"""
```

### 4. Run locally

```bash
streamlit run app.py
```

---

## 🤝 Contributing

PRs welcome! If you’d like to add features (benchmarking, risk scoring, portfolio synergies), open a pull request.

---