#!/bin/bash
# Bash script to reset the sales automation database and screenshots.
# Usage:
#   ./reset_project.sh
#

echo -e "\033[0;31m==========================================\033[0m"
echo -e "\033[0;31mResetting Sales Automation Local Storage\033[0m"
echo -e "\033[0;31m==========================================\033[0m"

# 1. Remove SQLite Database
if [ -f "data/leads.db" ]; then
    rm "data/leads.db"
    if [ $? -eq 0 ]; then
        echo -e "\033[0;32m[OK] Database file (data/leads.db) deleted successfully.\033[0m"
    else
        echo -e "\033[0;31m[ERROR] Could not delete data/leads.db. Ensure the Uvicorn server is stopped and try again.\033[0m"
        exit 1
    fi
else
    echo -e "\033[0;90m[INFO] No leads.db file found. Database is already clear.\033[0m"
fi

# 2. Clear Crawled Screenshots
if [ -d "data/screenshots" ]; then
    count=$(find data/screenshots/ -maxdepth 1 -name "*.png" | wc -l)
    if [ "$count" -gt 0 ]; then
        rm data/screenshots/*.png
        echo -e "\033[0;32m[OK] Cleared $count screenshots from data/screenshots/.\033[0m"
    else
        echo -e "\033[0;90m[INFO] Screenshots directory is already clear.\033[0m"
    fi
else
    echo -e "\033[0;90m[INFO] Screenshots directory does not exist.\033[0m"
fi

echo -e "\033[0;32m==========================================\033[0m"
echo -e "\033[0;32mReset Complete! Run the app to start fresh.\033[0m"
echo -e "\033[0;32m==========================================\033[0m"
