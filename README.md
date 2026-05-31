# Website-Audit B2B Sales Automation Platform

A premium B2B sales outreach automation system. This application crawls US business websites, performs performance/SEO audits (including local HTML parsers and Google PageSpeed Insights), maps weaknesses to B2B design and CRM services, drafts highly personalized cold outreach emails using LLMs (Anthropic, OpenAI, or Google Gemini), and facilitates human-in-the-loop email review and dispatching via a modern glassmorphic React dashboard or a Typer-powered terminal CLI.

---

## Architecture & Tech Stack

- **Backend:** Python 3.10+ / FastAPI / SQLAlchemy (SQLite) / Playwright (Headless Crawler) / BeautifulSoup4 / LangChain (LLM orchestrator)
- **Frontend:** React / Vite / TypeScript / Tailwind CSS v4 / TanStack Query / Recharts / Lucide Icons
- **Integrations:** Google PageSpeed Insights API, Gmail API (OAuth 2.0)

> [!NOTE]
> **Project Documentation Quick Links:**
> - [Step-by-Step User Guide](docs/user_guide.md) – Comprehensive guide on how to use the web app (with screenshots) and terminal CLI.
> - [Database Reset Guide](docs/database_reset_guide.md) – Instructions on how to clear local database data and screenshots to start fresh.
> - [Project Guide & File Directory](docs/project_guide.md) – A complete guide explaining what each file in the project does.
> - [API Keys Setup Guide](docs/api_keys_guide.md) – Configuration instructions for Google PageSpeed, LLMs, and Gmail OAuth.

---

## Project Structure

```
├── config.yaml          # Global non-secret system configurations (timeouts, rules, limits)
├── .env.example         # Template for API keys, secret credentials, and auth tokens
├── requirements.txt     # Python backend dependencies
├── docs/
│   ├── user_guide.md     # Step-by-step user guide with dashboard screenshots
│   ├── database_reset_guide.md # Guide explaining how to reset local database and clear files
│   ├── project_guide.md  # Guide explaining what every file in the project does
│   ├── api_keys_guide.md # Comprehensive API key acquisition and setup guide
│   └── SALES_AUTOMATION_SPEC.md # Product and system specifications document
├── src/
│   ├── main.py          # Terminal CLI entry point (Typer command suite)
│   ├── db.py            # SQLite session management and database models
│   ├── config.py        # Configuration manager merging yaml and .env settings
│   ├── models.py        # Pydantic validation schemas
│   ├── api/
│   │   ├── main.py      # FastAPI application server and REST endpoints
│   │   └── jobs.py      # Async background task runner and SSE streaming channels
│   └── core/            # Ingestion, scraping, audits, LLM drafts, and email services
├── frontend/
│   ├── package.json     # Node frontend project configuration
│   ├── vite.config.ts   # Vite bundler options and backend API proxy rules
│   └── src/
│       ├── App.tsx      # React Single Page Application and views layout
│       └── api/
│           └── client.ts # Front-end API client wrappers
└── tests/               # Backend pytest suite (scraping, mapping, audits, send, and api tests)
```


---

## Prerequisites

Ensure you have the following installed on your machine:
1. **Python 3.10+** (tested and fully compatible with Python 3.14.2)
2. **Node.js 18+** & **npm**

---

## 1. Installation & Environment Setup

### Step A: Clone & Python Virtual Environment
Navigate to the project root directory and set up a Python virtual environment:
```powershell
# Create a virtual environment named .venv
python -m venv .venv

# Activate the virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install all backend Python dependencies
pip install -r requirements.txt

# Install Playwright Chromium headless binaries
playwright install chromium
```

### Step B: Configure Secrets & Credentials
1. Copy the environment template:
   ```powershell
   copy .env.example .env
   ```
2. Open `.env` in a text editor and fill in your API credentials:
   - Set `API_AUTH_TOKEN` (e.g. `my-secure-api-token`). This token authenticates the frontend client dashboard.
   - Insert API keys for your preferred LLMs (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GOOGLE_API_KEY`).
   - Add a `PAGESPEED_API_KEY` (Google Cloud Console) to run live Lighthouse performance audits.
   - (Optional) If you plan to dispatch emails via Gmail, place your OAuth credentials file under `secrets/gmail_oauth.json`.

> [!TIP]
> For detailed instructions on how to acquire each of these API keys, set up Google Cloud OAuth client consent screens, and locate the key files, check out the comprehensive [API Configuration Guide](docs/api_keys_guide.md).

---

## 2. Configuration & Compliance Safeguards

Open `config.yaml` in the root folder. Before running live campaigns, you must verify the compliance settings:

```yaml
email:
  sender_name: "Your Name"
  sender_company: "Your Agency"
  physical_address: "123 Main St, Anytown, USA"        # <-- CRITICAL COMPLIANCE BLOCKER
  unsubscribe_base_url: "http://localhost:8000/unsubscribe" # <-- CRITICAL COMPLIANCE BLOCKER
```

> [!IMPORTANT]
> **CAN-SPAM Compliance Blockers:** The backend email dispatcher will refuse to dispatch live emails if `physical_address` or `unsubscribe_base_url` are missing or contain default placeholders. Live sends are locked into Simulator mode until these values are customized.
>
> **Sending Cap Safeguard:** Live dispatches are capped at a daily limit of **30** emails by default (configured via `send.daily_send_limit` in `config.yaml`) to protect your domain reputation.

---

## 3. Running the FastAPI Backend Server

To start the FastAPI web server, run Uvicorn inside the activated Python environment:
```powershell
# From the root directory:
.venv\Scripts\uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```
- The REST API will be exposed at `http://127.0.0.1:8000`
- You can explore the interactive OpenAPI docs at `http://127.0.0.1:8000/docs`

---

## 4. Running the React Frontend Dashboard

Open a separate terminal window, navigate to the `frontend/` directory, install Node packages, and run the Vite server:

```powershell
# Navigate to the frontend directory
cd frontend

# Install Node.js packages
npm install

# Run the local Vite dev server
npm run dev
```
- Open your browser to `http://localhost:5173` to access the dashboard.
- On your first load, you will be prompted to enter your `API_AUTH_TOKEN` (configured in your `.env` file) to authenticate database requests.

---

## 5. Running the Pipeline via Terminal CLI

You can also run all stages of the automation pipeline directly from the command line:

```powershell
# 1. Ingest leads from a CSV file
.venv\Scripts\python -m src.main ingest --csv data/leads_sample.csv

# 2. Run Playwright Crawler (renders homepage text & saves screenshots to data/screenshots/)
.venv\Scripts\python -m src.main scrape

# 3. Analyze website HTML and sample performance scores
.venv\Scripts\python -m src.main analyze

# 4. Generate LLM cold email drafts (runs grounding checks to prevent hallucinated claims)
.venv\Scripts\python -m src.main generate

# 5. Launch interactive terminal review queue (Approve / Reject / Edit drafts manually)
.venv\Scripts\python -m src.main review

# 6. Execute sending queue (respects daily caps and suppression blacklists)
.venv\Scripts\python -m src.main send

# 7. Check database funnel status statistics
.venv\Scripts\python -m src.main status
```

---

## 6. Running Tests & Verifying the Codebase

### Backend Test Suite
Run pytest to run all unit and integration test fixtures (including scraping semaphores, rule mappers, PageSpeed integrations, compliance validations, and REST API endpoints):
```powershell
# From the project root:
.venv\Scripts\pytest
```

### Frontend Compilation
Run the TypeScript builder inside the `frontend` folder to verify structural and type soundness:
```powershell
cd frontend
npm run build
```
