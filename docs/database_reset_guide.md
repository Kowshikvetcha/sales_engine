# Sales Automation Platform: Database Reset & Clearing Guide

This document describes how to safely clear database records and website screenshots to reset the application state and start fresh.

---

## 1. What Resetting Accomplishes

When you reset the database:
* **Leads Funnel Clear:** Deletes all ingested leads and resets their statuses.
* **Scrape Records Clear:** Deletes all website raw texts and HTML records.
* **Audit Mappings Clear:** Deletes all identified weaknesses and mapped services findings.
* **Outreach Drafts Clear:** Deletes all generated email drafts and human review queue outcomes.
* **Activity & Background Jobs Clear:** Resets job running histories, cancellations, and logs.
* **Suppression Lists Clear:** Deletes added opt-out blacklisted domains and emails.

> [!WARNING]
> This operation is destructive and permanently deletes your records. Export any necessary data or backups before resetting.

---

## 2. One-Click Reset Scripts

To make starting fresh extremely convenient, we have included automation scripts at the root of the project:

### Windows PowerShell:
1. Open PowerShell and navigate to the project directory.
2. Stop the running Uvicorn backend server (press `Ctrl + C` in the server terminal) so that the database file is not locked.
3. Run the reset script:
   ```powershell
   .\reset_project.ps1
   ```

### Unix / macOS Bash:
1. Stop the running Uvicorn server.
2. Set permissions and run the reset script:
   ```bash
   chmod +x reset_project.sh
   ./reset_project.sh
   ```

---

## 3. Manual Reset Methods

If you prefer performing the actions manually, you can execute the deletion commands using standard terminal commands:

### A. Windows Command Prompt (CMD)
```cmd
# Delete database
del data\leads.db

# Clear screenshots
del data\screenshots\*.png
```

### B. macOS / Linux Terminal
```bash
# Delete database
rm data/leads.db

# Clear screenshots
rm data/screenshots/*.png
```

---

## 4. Re-initializing the Database

Once the database file (`data/leads.db`) is deleted, the system enters an uninitialized state. 

**No manual setup is required to recreate it.**

The next time you perform any of the following actions, the backend automatically detects the absence of the database, creates a new `leads.db` file, and sets up all required schemas and tables:
* Starting the FastAPI backend server:
  ```bash
  .venv\Scripts\uvicorn src.api.main:app --reload
  ```
* Running any pipeline commands via CLI:
  ```bash
  .venv\Scripts\python -m src.main ingest --csv data/leads_sample.csv
  ```
* Launching background tasks from the web application interface.
