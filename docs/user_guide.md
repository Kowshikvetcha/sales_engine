# Website-Audit Sales Automation Platform: Step-by-Step User Guide

This guide provides a comprehensive, step-by-step walkthrough of how to use both the **React Frontend Dashboard** and the **Terminal Command Line Interface (CLI)** to run B2B sales automation campaigns.

---

## Table of Contents
1. [Prerequisites & Initial Setup](#1-prerequisites--initial-setup)
2. [Step-by-Step Web Application Guide](#2-step-by-step-web-application-guide)
   * [Step 1: Dashboard Login & Token Authentication](#step-1-dashboard-login--token-authentication)
   * [Step 2: Importing Leads (CSV Ingestion)](#step-2-importing-leads-csv-ingestion)
   * [Step 3: Crawler & Website Audits (Dashboard & Leads Tab)](#step-3-crawler--website-audits-dashboard--leads-tab)
   * [Step 4: Reviewing and Editing Email Drafts (Review Queue)](#step-4-reviewing-and-editing-email-drafts-review-queue)
   * [Step 5: Dispatching Campaigns (Send Console)](#step-5-dispatching-campaigns-send-console)
   * [Step 6: LLM A/B Model Comparisons (Bake-Off Console)](#step-6-llm-ab-model-comparisons-bake-off-console)
3. [Step-by-Step Terminal CLI Guide](#3-step-by-step-terminal-cli-guide)
4. [Compliance Safeguards & Simulation Mode](#4-compliance-safeguards--simulation-mode)

---

## 1. Prerequisites & Initial Setup

Before running the application, make sure you have installed all dependencies and configured your environment files:
* **Backend Virtual Environment:** Run `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Mac/Linux) and install dependencies using `pip install -r requirements.txt`.
* **Playwright Scraping Binaries:** Run `playwright install chromium` to install headless crawler engines.
* **Secrets Setup:** Set up your `.env` file with `API_AUTH_TOKEN` and your respective LLM & Google PageSpeed API keys. Follow [API Keys Setup Guide](api_keys_guide.md) for step-by-step acquisition directions.
* **Server Execution:**
  * Start the FastAPI backend: `.venv\Scripts\uvicorn src.api.main:app --reload` (runs on `http://127.0.0.1:8000`).
  * Start the React UI: `cd frontend && npm run dev` (runs on `http://localhost:5173`).

---

## 2. Step-by-Step Web Application Guide

### Step 1: Dashboard Login & Token Authentication
When you open `http://localhost:5173` in your browser for the first time, you will be prompted with a secure login dialog.
1. Enter the `API_AUTH_TOKEN` value configured in your `.env` file.
2. Click **Submit**. The dashboard will store this session token securely and grant access to the application data.

---

### Step 2: Importing Leads (CSV Ingestion)
To feed businesses into your campaign pipeline, start by importing a CSV lead sheet.
1. Navigate to the **Import Leads** tab on the navigation bar.
2. Drag and drop your `.csv` file or click to choose a file.
3. The table will instantly preview the first few rows of your CSV.
4. **Header Mapping:** Use the dropdown selectors to map your CSV columns to the required database fields:
   * **Company Name** (required)
   * **Website URL** (required)
   * **Target Email** (required)
   * **Contact Name** (optional)
5. Click **Import Leads**. A background task will parse, normalize URLs, check the suppression opt-out blacklist, and ingest new prospects while omitting duplicates.

---

### Step 3: Crawler & Website Audits (Dashboard & Leads Tab)
Once leads are imported, they start in the `imported` state. The background worker processes them through scraping and auditing.
1. Navigate to the main **Dashboard** tab. Here, you will see a visual representation of your leads funnel:
   * **Funnel Statistics:** Cards showing counts for Pending Crawler, Pending Audits, Drafted, Approved, Sent, and Failed leads.
   * **Lead Conversion Chart:** A visual timeline graph illustrating conversion success rates.
   * **Active Run Logs:** A stream showing live task indicators.
2. Navigate to the **Leads Table** tab to search, page, and filter prospects.
3. Click on any row to open the **Lead Inspector Panel** sliding in from the right:
   * View raw crawled text.
   * Preview full-page desktop screenshots captured by Playwright.
   * Review performance Lighthouse metrics (Performance, SSL status, missing SEO tags, analytics tracker alerts).

![Dashboard UI Mockup](images/dashboard_mockup.png)

---

### Step 4: Reviewing and Editing Email Drafts (Review Queue)
After audits complete, the system automatically uses LLMs (under guidelines defined in `config.yaml` and prompt instructions) to write highly personalized cold outreach emails. These drafts land in the **Review Queue**.
1. Navigate to the **Review Queue** tab.
2. The UI splits into a **two-pane editor**:
   * **Left Pane:** A list of leads currently in the `drafted` state, highlighting their domains.
   * **Right Pane:** The detailed review pane for the selected lead, displaying:
     * Audited website weaknesses and mapped service offerings (e.g. Design, CRM integration, SEO fixes).
     * Subject Line and Email Body editor textareas.
     * Model parameters (e.g., system temperature, provider choice).
3. Review the draft. You can make manual corrections directly in the text editor.
4. Click **Approve** to move the lead to `approved` (ready to send) or **Reject** to discard the draft.

![Review Queue UI Mockup](images/review_queue_mockup.png)

---

### Step 5: Dispatching Campaigns (Send Console)
The **Send Console** acts as the campaign cockpit, controlling sending rates, mode variables, and tracking live API integrations.
1. Navigate to the **Send Console** tab.
2. Review the following UI widgets:
   * **Sending Gauge:** A dynamic circular gauge showing current daily caps utilization (defaulting to a safety ceiling of 30 sends/day).
   * **Simulator Mode Toggle:** A switch choosing between simulated dry-run sends (emails written to database logs without emailing clients) and live Google Workspace/Gmail API dispatches.
   * **Trigger Dispatcher:** Click **Start Sending Job** to spin up the background delivery worker.
3. **Live SSE Terminal Logs:** Watch the console terminal box scroll in real-time as the worker verifies CAN-SPAM compliance headers, enforces rate-limiting delays between dispatches, verifies blacklists, and completes deliveries.

![Send Console UI Mockup](images/send_console_mockup.png)

---

### Step 6: LLM A/B Model Comparisons (Bake-Off Console)
To optimize your copywriting and compare providers, run model bake-offs:
1. Navigate to the **Model Bake-Off** tab.
2. Select a target lead sample and choose which model APIs to run side-by-side (e.g., Anthropic Claude, OpenAI GPT, Google Gemini).
3. Click **Execute Comparison**.
4. The screen renders a side-by-side evaluation layout:
   * Each column represents a model's draft, complete with speed/latency tracking (e.g., 1.4s), estimated generation cost based on token length, subject lines, and draft bodies.
   * Green visual labels mark the **Fastest** and **Cheapest** drafts to help you select the ideal model for scale.

![Model Bake-Off UI Mockup](images/bakeoff_mockup.png)

---

## 3. Step-by-Step Terminal CLI Guide

If you prefer operating from the terminal or want to set up automated cron jobs, you can execute the pipeline end-to-end using Python CLI subcommands:

### 1. Ingest Leads
Import prospects from a local CSV sheet:
```powershell
.venv\Scripts\python -m src.main ingest --csv data/leads_sample.csv
```

### 2. Crawl Websites
Activate Playwright to scrape homepage texts and capture screenshots:
```powershell
.venv\Scripts\python -m src.main scrape
```

### 3. Run SEO & PageSpeed Audits
Analyze local page criteria and fetch API metrics:
```powershell
.venv\Scripts\python -m src.main analyze
```

### 4. Generate Email Drafts
Draft grounded emails using your default LLM:
```powershell
.venv\Scripts\python -m src.main generate
```

### 5. Interactive Review Queue
Step through drafted campaigns in an interactive terminal review loop:
```powershell
.venv\Scripts\python -m src.main review
```
* The terminal will print lead information and prompt you: `Approve [A], Reject [R], Edit [E], Skip [S], Quit [Q]`.

### 6. Deliver Campaigns
Dispatch approved emails:
```powershell
.venv\Scripts\python -m src.main send
```
* **Simulator Flag:** Add `--dry-run` or configure settings to simulate sends locally without calling the Gmail API.

### 7. View Pipeline Funnel Status
Extract a quick statistical report of lead statuses:
```powershell
.venv\Scripts\python -m src.main status
```

---

## 4. Compliance Safeguards & Simulation Mode

This platform enforces strict compliance guards to protect your domain sending reputation and comply with CAN-SPAM laws:

* **Simulation Lock:** By default, the application runs in **Simulator Mode**. The system refuses to send live emails if `email.physical_address` or `email.unsubscribe_base_url` are set to default placeholders in `config.yaml`.
* **Suppression Blacklists:** Any lead whose email domain or exact address matches the suppression list database table is automatically set to `suppressed` status, preventing any generated drafts or dispatches.
* **Daily Capsule Safeguard:** Sending operations enforce a daily cap of **30** emails (adjustable under `send.daily_send_limit` in `config.yaml`) to avoid hitting spam-trap rate limits.
