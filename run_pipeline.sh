#!/bin/bash
# Bash script to run the sales automation pipeline end-to-end automatically.
# Usage:
#   ./run_pipeline.sh --limit 5 --real-run
#

LIMIT=0
DRY_RUN=true

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -l|--limit) LIMIT="$2"; shift ;;
        --real-run) DRY_RUN=false ;;
        --dry-run) DRY_RUN=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

echo -e "\033[0;36m==================================================\033[0m"
echo -e "\033[0;36mWebsite-Audit Sales Automation Pipeline Initiated\033[0m"
echo -e "\033[0;36m==================================================\033[0m"

# 1. Activate Virtual Environment
if [ -f ".venv/bin/activate" ]; then
    echo -e "\033[0;33m[1/5] Activating Python virtual environment...\033[0m"
    source .venv/bin/activate
else
    echo -e "\033[0;31m[Warning] Virtual environment not found at .venv. Running with system python.\033[0m"
fi

# 2. Run Crawler / Scraper
echo -e "\033[0;33m[2/5] Starting Web Scraping (Playwright Crawler)...\033[0m"
if [ "$LIMIT" -gt 0 ]; then
    python3 -m src.main scrape --limit "$LIMIT"
else
    python3 -m src.main scrape
fi
if [ $? -ne 0 ]; then
    echo -e "\033[0;31mError: Scraping stage failed. Aborting.\033[0m"
    exit 1
fi

# 3. Run Analysis & Evidence Mapping
echo -e "\033[0;33m[3/5] Starting Web Audits and Service Mapping...\033[0m"
if [ "$LIMIT" -gt 0 ]; then
    python3 -m src.main analyze --limit "$LIMIT"
else
    python3 -m src.main analyze
fi
if [ $? -ne 0 ]; then
    echo -e "\033[0;31mError: Analysis stage failed. Aborting.\033[0m"
    exit 1
fi

# 4. Run LLM Email Draft Generation
echo -e "\033[0;33m[4/5] Starting Cold Email Draft Generation (LLM)...\033[0m"
if [ "$LIMIT" -gt 0 ]; then
    python3 -m src.main generate --limit "$LIMIT"
else
    python3 -m src.main generate
fi
if [ $? -ne 0 ]; then
    echo -e "\033[0;31mError: Generation stage failed. Aborting.\033[0m"
    exit 1
fi

# 5. Run Email Sending Queue
echo -e "\033[0;33m[5/5] Starting Send Dispatcher...\033[0m"
SEND_ARGS=""
if [ "$LIMIT" -gt 0 ]; then
    SEND_ARGS="--limit $LIMIT"
fi
if [ "$DRY_RUN" = true ]; then
    SEND_ARGS="$SEND_ARGS --dry-run"
else
    SEND_ARGS="$SEND_ARGS --real-run"
fi

python3 -m src.main send $SEND_ARGS
if [ $? -ne 0 ]; then
    echo -e "\033[0;31mError: Send dispatcher stage failed.\033[0m"
    exit 1
fi

echo -e "\033[0;32m==================================================\033[0m"
echo -e "\033[0;32mPipeline execution completed successfully!\033[0m"
echo -e "\033[0;32m==================================================\033[0m"
