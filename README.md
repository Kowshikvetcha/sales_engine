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
├── config.yaml               # Global configurations (timeouts, throttle limits, compliance details)
├── .env.example              # Template for local environment variables and secret API keys
├── requirements.txt          # Python packages and backend dependencies list
├── reset_project.ps1         # PowerShell script to clean and initialize database and screenshots
├── reset_project.sh          # Unix shell script to clean and initialize database and screenshots
├── run_pipeline.ps1          # PowerShell automation script executing all pipeline stages consecutively
├── run_pipeline.sh           # Unix shell automation script executing all pipeline stages consecutively
├── agents.md                 # Agent handoff log and feature registry for developer context
├── data/                     # Local data files and assets storage directory
│   ├── leads.db              # SQLite database containing funnel status and lead records
│   └── screenshots/          # Folder storing browser screenshots of lead sites captured by Playwright
├── secrets/                  # Secure directory storing sensitive Google API keys and credentials
│   ├── gmail_oauth.json      # Client secrets JSON file downloaded from Google API console
│   └── gmail_token.json      # Generated credentials token file after authorizing Gmail OAuth
├── docs/                     # Documentation manuals and specification guides
│   ├── images/               # Screenshots and image assets used in documentation
│   ├── api_keys_guide.md     # Setup guide explaining how to acquire API keys and configure credentials
│   ├── database_reset_guide.md # Instructions explaining how to clean lead funnel database entries
│   ├── project_guide.md      # Detailed file-by-file directory explanation of the backend core
│   ├── user_guide.md         # Full user manual with visual UI workflows and CLI parameters
│   └── SALES_AUTOMATION_SPEC.md # Original product and system specification document
├── src/                      # Backend Python source code
│   ├── main.py               # Typer-powered terminal CLI entrypoint
│   ├── db.py                 # SQLAlchemy session engine and database table schemas
│   ├── config.py             # Configuration loader merging yaml settings and environment variables
│   ├── models.py             # Pydantic schemas validating API request and response data payloads
│   ├── api/                  # FastAPI web server module
│   │   ├── main.py           # REST endpoints, CORS policies, and global authentication middleware
│   │   └── jobs.py           # Async job worker enqueuing pipeline stages and broadcasting SSE updates
│   ├── core/                 # Pipeline execution stage modules
│   │   ├── ingest.py         # Parses, normalizes, validates, and imports leads from CSV records
│   │   ├── scrape.py         # Playwright crawler extracting body text and taking screenshots
│   │   ├── analyze.py        # Runs local HTML audits, broken links check, and PageSpeed scores
│   │   ├── service_map.py    # Service mapper mapping website audits findings to sold packages
│   │   ├── generate.py       # LLM generation coordinator writing drafts and checking grounding
│   │   ├── review.py         # Terminal-based interactive leads approval workflow
│   │   └── send.py           # Delivery queue manager with compliance safeguards and limits throttling
│   ├── integrations/         # External service connectors
│   │   ├── pagespeed.py      # Client wrapper fetching Google PageSpeed metrics
│   │   ├── sender_base.py    # Abstract base interface class for email provider senders
│   │   └── gmail_sender.py   # Gmail API implementation class utilizing OAuth tokens
│   ├── llm/                  # Language model integrations
│   │   ├── client.py         # LangChain dynamic chat model loader supporting OpenAI/Anthropic/Gemini
│   │   ├── prompts.py        # System prompt templates enforcing strict copy structure and schema rules
│   │   ├── validate.py       # Grounding auditor checking written emails for hallucinated claims
│   │   └── bakeoff.py        # Performance comparison engine testing multiple models side-by-side
│   └── utils/                # Helper modules
│       ├── logging.py        # Structured logging configuration setup
│       └── url.py            # URL cleaner, normalizer, and domain extraction utility methods
├── frontend/                 # Frontend React client codebase
│   ├── package.json          # Node dependencies and scripts
│   ├── vite.config.ts        # Vite build tool and API proxy forwarding setup
│   └── src/                  # React application source code
│       ├── main.tsx          # Frontend React DOM entrypoint
│       ├── App.css           # Global custom typography and theme overrides
│       ├── index.css         # Tailwind v4 import rules and theme configurations
│       ├── App.tsx           # Dashboard view layouts, modals, state hooks, and routing shell
│       └── api/              # Frontend API client
│           └── client.ts     # Custom fetch wrapper fetching backend endpoints
└── tests/                    # Pytest test suite modules
    ├── test_api.py           # Integration tests validating FastAPI REST endpoints and SSE streams
    ├── test_grounding.py     # Assertions checking LLM email grounding validation loops
    ├── test_ingest.py        # Unit tests validating CSV ingestion parser and URL cleaners
    ├── test_scrape.py        # Assertions testing Playwright web scraping and subpage crawlers
    ├── test_send_dryrun.py   # Tests checking suppression checks and daily send caps
    └── test_service_map.py   # Table-driven testing validating mapper rules and thresholds
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
.venv\Scripts\uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```
- The REST API will be exposed at `http://127.0.0.1:8000`
- You can explore the interactive OpenAPI docs at `http://127.0.0.1:8000/docs`

> [!WARNING]
> **Windows/Playwright compatibility:** Do NOT include the `--reload` flag on Windows. Uvicorn's reload manager forces the use of `SelectorEventLoop`, which causes a `NotImplementedError` when Playwright attempts to launch its crawler subprocess.

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
