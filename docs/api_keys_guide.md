# API Keys & Credentials Configuration Guide

This guide details all external APIs, credentials, and authentication keys used by the B2B Sales Automation Engine, where to acquire them, and where they must be configured.

---

## 1. Summary of Required Configuration

All secrets must be configured inside the gitignored **`.env`** file located in the root of the project. You can copy the template `.env.example` to start:

```powershell
copy .env.example .env
```

| Key Name | API Provider | Purpose | Where to Place |
| :--- | :--- | :--- | :--- |
| `API_AUTH_TOKEN` | Local Application | Frontend Client Authentication | `.env` |
| `ANTHROPIC_API_KEY` | Anthropic | Primary Email Generation (Claude) | `.env` |
| `OPENAI_API_KEY` | OpenAI | Comparative Email Generation (GPT) | `.env` |
| `GOOGLE_API_KEY` | Google Gemini | Comparative Email Generation (Gemini) | `.env` |
| `PAGESPEED_API_KEY` | Google Cloud | Running performance audits on lead sites | `.env` |
| OAuth client JSON | Google Cloud (Gmail) | Authenticating and dispatching mail | `secrets/gmail_oauth.json` |

---

## 2. API Key Details & Acquisition Steps

### A. Local Frontend Token (`API_AUTH_TOKEN`)
- **Purpose:** Restricts access to your local FastAPI backend endpoints.
- **Acquisition:** Define any custom secret string of your choice (e.g., `my-custom-super-secret-key-123`).
- **Placement:** Set `API_AUTH_TOKEN=your_token` in `.env`.

### B. Anthropic Claude API (`ANTHROPIC_API_KEY`)
- **Purpose:** Serves as the primary language model provider for drafting outreach emails.
- **Acquisition:**
  1. Visit the [Anthropic Console](https://console.anthropic.com/).
  2. Create an account, load credits, and click on **API Keys**.
  3. Create a key and copy it.
- **Placement:** Set `ANTHROPIC_API_KEY=sk-ant-api...` in `.env`.

### C. OpenAI GPT API (`OPENAI_API_KEY`)
- **Purpose:** Used for model A/B comparison (bake-off runs) and optional email drafting.
- **Acquisition:**
  1. Visit the [OpenAI API Platform](https://platform.openai.com/).
  2. Log in, navigate to **API Keys**, and click **Create new secret key**.
- **Placement:** Set `OPENAI_API_KEY=sk-proj-...` in `.env`.

### D. Google Gemini API (`GOOGLE_API_KEY`)
- **Purpose:** Used for model A/B comparison (bake-off runs) and optional email drafting.
- **Acquisition:**
  1. Visit [Google AI Studio](https://aistudio.google.com/).
  2. Click **Get API Key** and select/create a project to generate a key.
- **Placement:** Set `GOOGLE_API_KEY=AIzaSy...` in `.env`.

### E. Google PageSpeed Insights API (`PAGESPEED_API_KEY`)
- **Purpose:** Runs mobile strategy Lighthouse audits (scores for performance, SEO, accessibility) on B2B target websites.
- **Acquisition:**
  1. Go to the [Google Cloud Console API Library](https://console.cloud.google.com/apis/library).
  2. Enable the **PageSpeed Insights API** for your project.
  3. Navigate to **APIs & Services > Credentials**.
  4. Click **Create Credentials > API Key** and copy the generated key string.
- **Placement:** Set `PAGESPEED_API_KEY=AIzaSy...` in `.env`.

---

## 3. Gmail API & OAuth Setup (For Email Campaign Dispatch)

If you plan to toggle off "Simulator Mode" and send real outreach emails through your Gmail account, you must register a Google Cloud OAuth consent screen.

### Step 1: Create OAuth 2.0 Credentials
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the **Gmail API** in your project.
3. Configure the **OAuth Consent Screen** (select **External** or **Internal** user type; add your email to **Test Users**).
4. Go to **Credentials**, click **Create Credentials**, and select **OAuth Client ID**.
5. Choose **Desktop Application** as the application type, set a name, and click **Create**.
6. Download the OAuth credentials JSON file.

### Step 2: Save the File
1. Rename the downloaded JSON file to `gmail_oauth.json`.
2. Move it to the **`secrets/`** directory in your project root:
   ```
   e:/sales_engine/secrets/gmail_oauth.json
   ```

### Step 3: Authorize the App
- When you run the CLI sending process (`python -m src.main send`) or click send on the UI console for the first time, a local web browser page will open prompting you to log into your Google Account.
- Grant the requested permissions.
- Once authenticated, the backend automatically generates a **`secrets/gmail_token.json`** file. Subsequent sends use this token file and require no manual login.
