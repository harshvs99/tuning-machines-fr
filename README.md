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

## 📂 Project Structure

``` bash
TUNING-MACHINES-FR/
├── .devcontainer/                # Dev container configuration for reproducible environments
├── .github/                      # GitHub workflows and CI/CD actions
├── .streamlit/                   # Streamlit configuration files (secrets.toml, theme, etc.)
├── dejavu-ttf/                   # Custom fonts (e.g., DejaVuSans.ttf for PDF generation)
├── env/                          # Local virtual environment (ignored in git)
│
├── pages/                        # Streamlit multi-page app modules
│   ├── 0_Analysis_History.py     # View past analyses and stored company evaluations
│   ├── 1_Portfolio_Setup.py      # Configure investor portfolio and fund setup
│   ├── 2_Run_Analysis.py         # Trigger startup analysis pipeline (API + AI calls)
│   ├── 3_First_Pass_Report.py    # Display first-level automated analysis summary
│   ├── 4_Founder_Q&A.py          # Capture Q&A or follow-ups with founders
│   ├── 5_Final_Report.py         # Final review and synthesis of results
│   ├── 6_Generate_Deal_Note.py   # Generate formatted deal note PDF from analysis JSON
│
├── utils/                        # Utility and client modules
│   ├── api_client.py             # Handles API calls to analysis and data services
│   ├── firebase_client.py        # Firestore and Firebase setup helpers
│   ├── gslides_client.py         # Integration with Google Slides (presentation generation)
│   └── pdf_client.py             # PDF generation utilities for deal notes and reports
│
├── streamlit_app.py               # Main entry point for running the Streamlit app
│
├── app.yaml                       # GCP deployment configuration for Cloud Run/App Engine
├── Dockerfile                     # Container build for deployment
├── requirements.txt                # Python dependencies
├── LICENSE                         # License information
├── README.md                       # Project documentation
├── app.log                         # Runtime logs (gitignored)
├── .gitignore                      # Ignore unnecessary files in Git
└── .gcloudignore                   # Ignore files during GCP deployment

```

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