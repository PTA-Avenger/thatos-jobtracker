@echo off
echo Starting MultiLang Job Tracker Scraper...
cd /d "%~dp0"
python scraper.py --source weworkremotely --limit 20
echo Scraper finished.
timeout /t 5
