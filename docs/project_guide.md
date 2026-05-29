# Project Guide & Directory Dictionary

This document describes the structure of the Website-Audit Sales Automation platform. It details the purpose and inner workings of every file in the codebase, both briefly and in detail.

---

## Configuration Files

### [config.yaml](file:///e:/sales_engine/config.yaml)
* **Brief:** Non-secret global configuration settings.
* **Detail:** Defines application parameters such as scraping concurrency, timeouts, robots.txt options, local HTML scoring thresholds, LLM defaults (model and provider name, temperature, retries), compliance details (sender information, physical address, unsubscribe links), and sending throttles (daily limits and per-message delays).

### [.env.example](file:///e:/sales_engine/.env.example)
* **Brief:** A template showing required environment variables and secrets.
* **Detail:** Documents the names of secret keys needed for the application to function. Includes keys for LLMs (Anthropic, OpenAI, Google), Google PageSpeed Insights, paths to Gmail API OAuth credentials and token files, and backend authentication tokens.

### [.env](file:///e:/sales_engine/.env)
* **Brief:** Local credentials storage (gitignored).
* **Detail:** Stores actual secret API keys, authorization tokens, and paths for local execution. Loaded dynamically at startup to authenticate external requests.

### [requirements.txt](file:///e:/sales_engine/requirements.txt)
* **Brief:** Lists Python package dependencies.
* **Detail:** Pinpoints base library versions required for APIs (FastAPI, Uvicorn, SSE-Starlette), configuration (Pydantic Settings, PyYAML), database (SQLAlchemy), browser automation (Playwright), HTML parsing (BeautifulSoup4, lxml), LLMs (LangChain), Gmail integration (Google API client), and test execution (Pytest).

---

## Application Core

### [src/main.py](file:///e:/sales_engine/src/main.py)
* **Brief:** Command Line Interface (CLI) entrypoint.
* **Detail:** Built using the Typer library. Defines subcommands to drive pipeline operations from the terminal. Implements commands like `ingest` (imports leads from CSV), `scrape` (runs Playwright scraper on pending leads), `analyze` (runs local checks and PageSpeed audits), `generate` (drafts personalized emails), `bakeoff` (compares model drafts side-by-side), and `status` (displays lead counts grouped by status). Automatically initializes database schemas at startup.

### [src/config.py](file:///e:/sales_engine/src/config.py)
* **Brief:** Merges and validates YAML configurations and environment secrets.
* **Detail:** Uses Pydantic Settings (`BaseSettings`) to load `config.yaml` using PyYAML, parse it into nested schemas, and overlay variables loaded from `.env` or system environment variables. Exposes a single, global thread-safe `settings` instance.

### [src/db.py](file:///e:/sales_engine/src/db.py)
* **Brief:** Database models, SQLAlchemy engine, and session management.
* **Detail:** Declares the SQLite database models representing the system's database schema. Includes tables for `leads` (lead profiles, statuses), `scrapes` (scraped texts, screenshot paths), `analyses` (performance scores, mapped findings), `emails` (generated drafts, send logs), `suppression` (opt-out list), `events` (tracking events), and `jobs` (background tasks status). Handles automatic file initialization and session creation.

### [src/models.py](file:///e:/sales_engine/src/models.py)
* **Brief:** Pydantic validation schemas for data exchange.
* **Detail:** Decoupled from the database layer, this file defines pure Pydantic schemas (e.g. `LeadOut`, `ScrapeOut`, `EmailDraft`, `JobOut`) to parse, validate, and serialize JSON requests/responses for API and service-to-service communication.

### [src/api/main.py](file:///e:/sales_engine/src/api/main.py)
* **Brief:** FastAPI web application server.
* **Detail:** Defines the REST API endpoints, applies CORS header controls, configures global API token authorization, and exposes routes to list leads, read details, download screenshot images, query pipeline stats, read configurations, and write updated properties back to the config file.

### [src/api/jobs.py](file:///e:/sales_engine/src/api/jobs.py)
* **Brief:** Background async pipeline job runner.
* **Detail:** Coordinates in-process asynchronous task execution using FastAPI BackgroundTasks. Manages active task registry, updates execution progress (done/total) inside the database Job table, supports cooperative task cancellation, and broadcasts live progress changes to listeners connected to the SSE streaming channels.

---

## Core Pipeline Stages

### [src/core/ingest.py](file:///e:/sales_engine/src/core/ingest.py)
* **Brief:** Ingestion engine for importing lead CSVs.
* **Detail:** Reads and parses lead data. Implements header parsing matching common CSV columns. Normalizes website URLs and extracts domains. Implements strict data safety: filters invalid email syntaxes, verifies leads against the suppression list (marking them `suppressed`), and validates database duplication. Duplicate leads are ignored, preventing database constraint failures.

### [src/core/scrape.py](file:///e:/sales_engine/src/core/scrape.py)
* **Brief:** Website scraping and screenshot capturing engine.
* **Detail:** Leverages Playwright Chromium (headless) to navigate to lead homepages and crawl internal B2B links (about, services, contact, pricing). Respects robots.txt files and manages domain politeness rate-limiting. Captures full-page screenshots stored in `data/screenshots/` and extracts text content up to configuration limits. Updates lead status to `scraped` or `failed` based on outcome.

### [src/core/analyze.py](file:///e:/sales_engine/src/core/analyze.py)
* **Brief:** Website analysis auditor.
* **Detail:** Conducts local homepage audits including tag presence, SSL validation, analytics tracking tools detection, and lead-capture input form detection. Executes concurrent broken link head-checking on a sample of hyperlinks, integrates with the PageSpeed Insight API client, compiles signals, and runs service mapping rules.

### [src/core/service_map.py](file:///e:/sales_engine/src/core/service_map.py)
* **Brief:** Rule-based evidence mapping engine.
* **Detail:** Evaluates compiled audit signals against structured thresholds (e.g. perf score, SSL, mobile friendly, forms, analytics). Maps matching weaknesses to our sold services (Design, CRM, Analytics, Data solutions) along with grounded evidence templates, prioritizes findings by severity, and limits the output mapping up to configurable count limits.

### [src/core/generate.py](file:///e:/sales_engine/src/core/generate.py)
* **Brief:** Grounded B2B email generation service.
* **Detail:** Orchestrates LLM prompt injection and JSON parsing to output cold emails. Evaluates generated content using a grounding validator, retries on ungrounded claims, and appends CAN-SPAM compliant footers. Falls back to mock B2B template output for dry-runs.

### [src/core/review.py](file:///e:/sales_engine/src/core/review.py)
* **Brief:** Terminal-based interactive review console.
* **Detail:** Finds leads in 'drafted' status and walks the user through their metadata, screenshot path, mapped service findings, and current email draft. Prompts the user to Approve [A], Reject [R], Edit [E], Skip [S], or Quit [Q]. Appends compliance footers on edited content.

### [src/core/send.py](file:///e:/sales_engine/src/core/send.py)
* **Brief:** Email send orchestrator.
* **Detail:** Conducts pre-send compliance checks, enforces daily cap sending limits across database logs, performs real-time suppression list checking, runs rate-limiting delays between dispatches, creates sent audit event records, and updates database lead/email statuses.

---

## Utility Functions

### [src/utils/url.py](file:///e:/sales_engine/src/utils/url.py)
* **Brief:** URL cleansing and domain extraction helpers.
* **Detail:** Uses standard `urllib.parse` to cleanse web links. Strips query parameter strings and page fragments, lowercases the hostname, strips trailing dots, prepends `https://` if a scheme is missing, and extracts the root domain by stripping standard prefixes like `www.`.

### [src/utils/logging.py](file:///e:/sales_engine/src/utils/logging.py)
* **Brief:** Central logger setup utilizing structlog.
* **Detail:** Configures standard logging alongside structlog. Renders rich colorized logs to standard output in local interactive terminals, and streams structured JSON formatted logs to output streams in non-TTY environments for production searchability.

---

## External Integrations

### [src/integrations/pagespeed.py](file:///e:/sales_engine/src/integrations/pagespeed.py)
* **Brief:** Google PageSpeed Insights client.
* **Detail:** Queries Google's PSI API for mobile-strategy Lighthouse metrics (Performance, SEO, Accessibility, Best Practices) and extracts speed index load times. Handles API exceptions gracefully and falls back to pre-defined mocked scores in dry-run scenarios.

---

## LLM Integration & Grounding

### [src/llm/client.py](file:///e:/sales_engine/src/llm/client.py)
* **Brief:** dynamic LangChain LLM loader.
* **Detail:** Initializes LangChain chat models dynamically via `init_chat_model` with configurable fields for runtime model/provider switches.

### [src/llm/prompts.py](file:///e:/sales_engine/src/llm/prompts.py)
* **Brief:** LLM outreach templates and guidelines.
* **Detail:** Declares prompts forcing strict JSON structures and grounding. Sets compliance constraints (helpful tone, max 150 words, cite only listed weaknesses).

### [src/llm/validate.py](file:///e:/sales_engine/src/llm/validate.py)
* **Brief:** Post-generation email grounding auditor.
* **Detail:** Passes drafts to a deterministic LLM auditor to compare claims against audit findings. Extracts and saves a JSON list of findings cited, failing ungrounded drafts.

### [src/llm/bakeoff.py](file:///e:/sales_engine/src/llm/bakeoff.py)
* **Brief:** LLM model A/B comparison console.
* **Detail:** Compares latency, character token cost, subject lines, and draft body content side-by-side across Claude, GPT, and Gemini models.

---

## Test Suite

### [tests/test_ingest.py](file:///e:/sales_engine/tests/test_ingest.py)
* **Brief:** Unit tests for CSV ingestion, validation, and URL helpers.
* **Detail:** Uses Pytest fixtures to stand up an in-memory SQLite database. Runs table-driven tests against `is_valid_email`, `normalize_url`, and `extract_domain`. Simulates CSV imports to test successful insertions, validation failures, suppression flags, and email/domain deduplication logic.

### [tests/test_scrape.py](file:///e:/sales_engine/tests/test_scrape.py)
* **Brief:** Integration tests for the Playwright scraping engine.
* **Detail:** Launches a dynamic local HTTP mock server in a background thread to serve test B2B html contents. Verifies that the scraper correctly parses B2B subpage links, respects robots.txt restrictions, processes pages within a concurrency semaphore, saves screenshots to disk, and records scrapes properly in the database.

### [tests/test_service_map.py](file:///e:/sales_engine/tests/test_service_map.py)
* **Brief:** Unit tests for service mapping rules.
* **Detail:** Validates service mapping logic by passing various mock signals (low performance scores, SSL absence, mobile friendliness errors, lack of analytics, lack of forms) and asserting correct service output associations and evidence statements. Checks sorting by severity and count limits.

### [tests/test_grounding.py](file:///e:/sales_engine/tests/test_grounding.py)
* **Brief:** Unit tests for the email grounding auditor.
* **Detail:** Mocks LangChain chat model response JSONs to verify that validation status passes on grounded emails and fails on ungrounded claims (such as mentioning SSL errors when no SSL findings were measured). Exposes cited findings arrays.

### [tests/test_send_dryrun.py](file:///e:/sales_engine/tests/test_send_dryrun.py)
* **Brief:** Tests for email send orchestration.
* **Detail:** Verifies dry-run behavior, real-time suppression list blocking, daily send cap limitation safety checks, and CAN-SPAM compliance validation.

### [tests/test_api.py](file:///e:/sales_engine/tests/test_api.py)
* **Brief:** FastAPI integration test suite.
* **Detail:** Performs HTTP request validation using the FastAPI test client. Tests routes for leads query, screenshots, stats, and configurations under token-validated and unauthorized conditions.

---

## React Frontend Application

### [frontend/vite.config.ts](file:///e:/sales_engine/frontend/vite.config.ts)
* **Brief:** Vite compilation and development server settings.
* **Detail:** Integrates `@tailwindcss/vite` for Tailwind CSS processing and configures dev-server routing proxy mapping `/api` requests to `http://127.0.0.1:8000` to bypass CORS restrictions.

### [frontend/src/api/client.ts](file:///e:/sales_engine/frontend/src/api/client.ts)
* **Brief:** Frontend API client client routing logic.
* **Detail:** Exposes a unified async request helper that automatically appends `X-API-Token` credentials to HTTP headers and constructs query parameters for binary image assets. Bundles API methods for stats extraction, configuration queries, leads reading/creation, and job scheduling.

### [frontend/src/index.css](file:///e:/sales_engine/frontend/src/index.css)
* **Brief:** Main global stylesheet.
* **Detail:** Configures Tailwind CSS imports, sets up the base dark theme, and defines glassmorphic CSS rules for panels, borders, and backdrop filters.

### [frontend/src/App.tsx](file:///e:/sales_engine/frontend/src/App.tsx)
* **Brief:** Single Page Application (SPA) entry and layout component.
* **Detail:** Orchestrates page state tabs and rendering of sub-panels: Dashboard conversion charts, CSV spreadsheet parsing and header-to-column mapper, paged Leads table, and the slide-out Lead Inspector detailing individual audit telemetry, screenshot streams, and running job logs.
