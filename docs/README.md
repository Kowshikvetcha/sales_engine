# Website-Audit Sales Automation

Ingest a CSV of US business leads, scrape each website, measure objective quality signals, map weaknesses to the services we sell, and generate personalized, **grounded** cold emails — reviewed in a web UI and sent via Gmail (testing) or a dedicated sending stack (scale).

> **Source of truth:** [`SALES_AUTOMATION_SPEC.md`](./SALES_AUTOMATION_SPEC.md). Read it before writing code. It defines the architecture, data model, pipeline stages, API, UI screens, build milestones (M1–M10), and acceptance criteria.

> **For the agentic coding tool:** implement the milestones in **§14** of the spec **in order, one at a time**. Do not skip the grounding validator (§6.3) or the compliance guardrails (§7, §8.5) — they are hard requirements, not nice-to-haves.

---

## Prerequisites
- **Python 3.11+**
- **Node.js 18+** (required by Vite + Tailwind v4)
- API keys: an LLM provider (Anthropic / OpenAI / Google), a free **Google PageSpeed Insights** key, and **Gmail OAuth** credentials for sending.

## Repository layout
See spec **§9** for the full tree. Top level:
```
.
├── SALES_AUTOMATION_SPEC.md   # the spec — read first
├── requirements.txt
├── config.yaml                # create from spec §10
├── .env                       # create from spec §10 (never commit)
├── src/                       # Python: core/, api/, llm/, integrations/, utils/, main.py
├── frontend/                  # React + Vite + TS + Tailwind v4
├── data/                      # leads.db + screenshots/  (gitignored)
└── tests/
```

---

## Backend setup
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium                            # required for scraping

cp .env.example .env          # then fill in keys  (contents specified in spec §10)
# create config.yaml from spec §10 and fill sender_name / physical_address / unsubscribe_base_url
```

Run the API:
```bash
uvicorn src.api.main:app --reload     # http://127.0.0.1:8000
```

Run the CLI (automation / cron — same core as the UI):
```bash
python -m src.main ingest --csv leads.csv
python -m src.main run --all --dry-run
python -m src.main status
```

---

## Frontend setup
The `frontend/package.json` lists the target dependencies. If starting fresh, the canonical scaffold is:
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install tailwindcss @tailwindcss/vite        # Tailwind v4
```
Then wire Tailwind v4 (no `tailwind.config.js`/PostCSS needed for basic setup):
```ts
// vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
export default defineConfig({ plugins: [react(), tailwindcss()] });
```
```css
/* src/index.css */
@import "tailwindcss";
```
Add shadcn/ui components:
```bash
npx shadcn@latest init
npx shadcn@latest add button card table dialog tabs badge input toast
```
Run the UI (proxy `/api` → `http://127.0.0.1:8000` in `vite.config.ts`):
```bash
npm run dev        # http://localhost:5173
```

---

## Build order (milestones)
Implement in sequence — each has a "done when" in spec §14:
1. **M1** Scaffold + config + DB + ingest
2. **M2** Scraper (Playwright)
3. **M3** Analysis (PageSpeed + HTML/SSL/SEO) + service mapping
4. **M4** LLM generation + grounding validator + bake-off
5. **M5** CLI review + Gmail send + suppression
6. **M6** Core refactor + FastAPI read APIs
7. **M7** Background job runner + stage endpoints + SSE progress
8. **M8** React: Dashboard / Import / Leads / Detail / Jobs
9. **M9** Review Queue + Send Console + Suppression + Settings
10. **M10** Bake-off UI + polish + end-to-end dry run

---

## Compliance & safety (do not skip)
- **US / CAN-SPAM only** in v1. Every email must carry a real physical postal address + a working unsubscribe link, applied deterministically (not by the model).
- The UI **disables real sending** until `physical_address` and `unsubscribe_base_url` are set.
- Honor opt-outs immediately via the suppression list (checked at ingest and pre-send).
- **Testing phase:** send from a Google Workspace inbox at ~**30/day**, and **do not test on your best leads** — use addresses you control or expendable leads, since first drafts may be rough.
- Every claim in an email must trace to a measured finding (`findings_cited`). Leads with no findings get no email.

## Default model
`claude-sonnet-4-6` (Anthropic). Swappable at runtime via LangChain `init_chat_model` with no code changes — see spec §6.1. Verify exact provider model IDs in each provider's docs (they version often).
