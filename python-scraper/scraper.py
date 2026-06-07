import os
import sys
import argparse
import requests
import hashlib
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load configuration from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Import Playwright scraper module
sys.path.append(os.path.dirname(__file__))
from scraper_playwright import run_scraper_playwright

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")
SCRAPER_KEY = os.getenv("SCRAPER_KEY", "ScraperSuperSecretKey123")
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")

# Candidate skills for fallback zero-shot keyword matching
CANDIDATE_SKILLS = [
    "Java", "Python", "C#", "C++", "JavaScript", "TypeScript", "SQL", 
    "React", "Angular", "Vue", "Spring Boot", "ASP.NET", "Docker", 
    "Kubernetes", "AWS", "Azure", "Git", "HTML", "CSS", "Linux", 
    "Agile", "Excel", "REST API", "NoSQL"
]

def fallback_extract_skills(description):
    """Fallback keyword matcher if Hugging Face API is missing or error occurs."""
    desc_lower = description.lower()
    found = []
    for skill in CANDIDATE_SKILLS:
        skill_lower = skill.lower()
        # Word boundary match
        if f" {skill_lower} " in f" {desc_lower} " or f" {skill_lower}," in f" {desc_lower} " or f" {skill_lower}." in f" {desc_lower} ":
            found.append(skill)
            if len(found) >= 5:
                break
    return ", ".join(found) if found else "General SDE"

def fallback_extract_closing_date(text):
    """Regex fallback to extract closing dates (like YYYY-MM-DD or DD Mon YYYY)."""
    # 1. Match 'Apply by 11 Jun 2026' or 'Closing in 4 days'
    match_apply_by = re.search(r'(?:apply\s+by|closing\s+on|deadline)\s*[:\-]?\s*(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})', text, re.IGNORECASE)
    if match_apply_by:
        return match_apply_by.group(1).strip()
    
    # 2. Match standard ISO dates (YYYY-MM-DD)
    match_iso = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
    if match_iso:
        return match_iso.group(1)
        
    return None

def fallback_extract_visa(text):
    """Heuristic fallback to identify visa sponsorship or work rights requirements."""
    txt_lower = text.lower()
    if "must be a south african citizen" in txt_lower or "south african citizen only" in txt_lower or "valid south african id" in txt_lower:
        return False
    if "visa sponsorship" in txt_lower:
        if "no visa sponsorship" in txt_lower or "does not offer" in txt_lower or "not available" in txt_lower or "not provide" in txt_lower:
            return False
        return True
    if "sponsorship is available" in txt_lower or "offer sponsorship" in txt_lower:
        return True
    return None

def fallback_extract_experience(text):
    """Heuristic fallback for years of experience required."""
    txt_lower = text.lower()
    if "no experience required" in txt_lower or "no experience needed" in txt_lower or "entry level" in txt_lower or "graduate role" in txt_lower or "yes program" in txt_lower:
        return 0
    # Look for '1-3 years', '2+ years', '3 years of experience'
    match = re.search(r'(\d+)\s*(?:\+|to|-)\s*\d*\s*years?\s+(?:of\s+)?experience', txt_lower)
    if match:
        return int(match.group(1))
    match2 = re.search(r'(\d+)\s*years?\s+(?:of\s+)?experience', txt_lower)
    if match2:
        return int(match2.group(1))
    return None

def normalize_job_with_llm(description, title_hint, company_hint):
    """Use Hugging Face Serverless chat completion (Qwen-72B) to normalize job information."""
    if not HF_API_TOKEN or HF_API_TOKEN.startswith("your_"):
        print("[AI] Hugging Face token missing. Using fallback parser.")
        return None
        
    url = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""Analyze the following job description and extract SDE-specific fields. Return a JSON object containing:
{{
  "title": "Normalized Job Title",
  "company": "Company Name",
  "skills": "Comma-separated list of tech stack keywords",
  "closingDate": "YYYY-MM-DD or null",
  "visaSponsorship": true/false/null,
  "yearsExperienceRequired": integer or null
}}
Strictly output ONLY the raw JSON block. Do not include markdown codeblocks or explanation.

Title Hint: {title_hint}
Company Hint: {company_hint}

Job Description:
{description[:2500]}
"""

    payload = {
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 350,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            res_data = response.json()
            content = res_data["choices"][0]["message"]["content"].strip()
            # Clean up markdown code wraps if present
            if content.startswith("```"):
                content = content.replace("```json", "").replace("```", "").strip()
            # Try to load JSON
            return json.loads(content)
        else:
            print(f"[AI] HF API Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[AI] HF Request Failed: {e}")
        
    return None

def get_job_hash(title, company, date_posted):
    """Generate a unique MD5 hash for job deduplication."""
    unique_str = f"{title.lower()}|{company.lower()}|{str(date_posted).lower()}"
    return hashlib.md5(unique_str.encode('utf-8')).hexdigest()

def save_vault_snapshot(job, vault_dir="python-scraper/vault"):
    """Saves raw job postings as Markdown files in a local vault folder."""
    os.makedirs(vault_dir, exist_ok=True)
    filename = f"{job['jobHash']}.md"
    filepath = os.path.join(vault_dir, filename)
    
    visas = "Yes" if job.get("visaSponsorship") is True else ("No" if job.get("visaSponsorship") is False else "Unknown")
    exp = f"{job.get('yearsExperienceRequired')} years" if job.get('yearsExperienceRequired') is not None else "Not specified"
    closing = job.get("closingDate") or "Not specified"
    
    content = f"""# {job['title']} at {job['company']}

- **Source Platform**: {job.get('source_platform', 'Unknown')}
- **URL**: {job['url']}
- **Date Scraped**: {job['dateScraped']}
- **Closing Date / Deadline**: {closing}
- **Visa Sponsorship**: {visas}
- **Experience Required**: {exp}
- **Is Ghost Job**: {"Yes" if job.get("isGhostJob") else "No"}

---

## Job Description

{job['description']}
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath

def scrape_weworkremotely(limit=20):
    """Scrapes jobs from WeWorkRemotely using their public RSS feed."""
    print(f"[Scraper] Fetching WeWorkRemotely RSS feed...")
    url = "https://weworkremotely.com/remote-jobs.rss"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"[Scraper] Failed to fetch feed: {e}")
        return []

    soup = BeautifulSoup(response.content, features="xml")
    items = soup.find_all("item")
    
    jobs = []
    count = 0
    
    for item in items:
        if count >= limit:
            break
            
        raw_title = item.title.text if item.title else "Unknown Title"
        if ":" in raw_title:
            company, title = raw_title.split(":", 1)
            company = company.strip()
            title = title.strip()
        else:
            company = "WeWorkRemotely Client"
            title = raw_title.strip()
            
        link = item.link.text if item.link else ""
        pub_date = item.pubDate.text if item.pubDate else datetime.now().strftime("%Y-%m-%d")
        
        try:
            parsed_date = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
            date_posted = parsed_date.strftime("%Y-%m-%d")
        except Exception:
            date_posted = pub_date[:16]
            
        raw_desc = item.description.text if item.description else ""
        desc_text = BeautifulSoup(raw_desc, "html.parser").get_text().strip()
        
        job_hash = get_job_hash(title, company, date_posted)
        
        # Determine ghost job flag (posted >45 days ago)
        is_ghost = False
        try:
            parsed_pdate = datetime.strptime(date_posted, "%Y-%m-%d")
            delta = datetime.now() - parsed_pdate
            if delta.days > 45:
                is_ghost = True
        except Exception:
            pass

        # Normalize with AI (or fall back)
        ai_data = normalize_job_with_llm(desc_text, title, company)
        if ai_data:
            title = ai_data.get("title", title)
            company = ai_data.get("company", company)
            skills = ai_data.get("skills", fallback_extract_skills(desc_text))
            closing_date = ai_data.get("closingDate")
            visa_sponsorship = ai_data.get("visaSponsorship")
            years_experience = ai_data.get("yearsExperienceRequired")
        else:
            skills = fallback_extract_skills(desc_text)
            closing_date = fallback_extract_closing_date(desc_text)
            visa_sponsorship = fallback_extract_visa(desc_text)
            years_experience = fallback_extract_experience(desc_text)
            
        job_item = {
            "title": title,
            "company": company,
            "location": "Remote",
            "description": desc_text,
            "skills": skills,
            "url": link,
            "datePosted": date_posted,
            "dateScraped": datetime.now().strftime("%Y-%m-%d"),
            "jobHash": job_hash,
            "closingDate": closing_date,
            "visaSponsorship": visa_sponsorship,
            "yearsExperienceRequired": years_experience,
            "sourcePlatform": "WeWorkRemotely",
            "isGhostJob": is_ghost
        }
        
        # Save snapshot
        snapshot_path = save_vault_snapshot(job_item)
        job_item["snapshotPath"] = snapshot_path
        
        jobs.append(job_item)
        print(f"[Scraper] Parsed WWR: '{title}' at '{company}' (Skills: {skills})")
        count += 1
        
    return jobs

def scrape_playwright_source(source, limit=10):
    """Integrates Playwright scraping and runs the LLM normalization pipeline."""
    raw_jobs = run_scraper_playwright(source, limit)
    jobs = []
    
    for raw_job in raw_jobs:
        title = raw_job["title"]
        company = raw_job["company"]
        desc = raw_job["description"]
        url = raw_job["url"]
        source_platform = raw_job["source_platform"]
        
        date_posted = datetime.now().strftime("%Y-%m-%d") # Default
        job_hash = get_job_hash(title, company, date_posted)
        
        # Normalize with AI (or fall back)
        ai_data = normalize_job_with_llm(desc, title, company)
        if ai_data:
            title = ai_data.get("title", title)
            company = ai_data.get("company", company)
            skills = ai_data.get("skills", fallback_extract_skills(desc))
            closing_date = ai_data.get("closingDate")
            visa_sponsorship = ai_data.get("visaSponsorship")
            years_experience = ai_data.get("yearsExperienceRequired")
        else:
            skills = fallback_extract_skills(desc)
            closing_date = fallback_extract_closing_date(desc)
            visa_sponsorship = fallback_extract_visa(desc)
            years_experience = fallback_extract_experience(desc)
            
        # Standardize experience
        if years_experience is not None:
            years_experience = int(years_experience)

        # Detect ghost job (posting age heuristically or standard default false for fresh grad scraper)
        is_ghost = False
        
        job_item = {
            "title": title,
            "company": company,
            "location": raw_job.get("location", "South Africa"),
            "description": desc,
            "skills": skills,
            "url": url,
            "datePosted": date_posted,
            "dateScraped": datetime.now().strftime("%Y-%m-%d"),
            "jobHash": job_hash,
            "closingDate": closing_date,
            "visaSponsorship": visa_sponsorship,
            "yearsExperienceRequired": years_experience,
            "sourcePlatform": source_platform,
            "isGhostJob": is_ghost
        }
        
        # Save snapshot
        snapshot_path = save_vault_snapshot(job_item)
        job_item["snapshotPath"] = snapshot_path
        
        jobs.append(job_item)
        print(f"[Scraper] Parsed {source}: '{title}' at '{company}' (Skills: {skills}, Closing: {closing_date})")
        
    return jobs

def generate_mock_jobs(limit=10):
    """Generates mock job applications with new fields for testing."""
    print(f"[Scraper] Generating {limit} mock jobs...")
    import random
    titles = [
        "Software Engineer", "Frontend Developer", "Backend Developer", 
        "Fullstack Engineer", "DevOps Engineer", "Cloud Architect", 
        "Data Analyst", "Database Administrator"
    ]
    companies = ["Google", "Microsoft", "Amazon", "Netflix", "Meta", "Spotify", "Apple", "Uber"]
    locations = ["New York, NY", "Seattle, WA", "San Francisco, CA", "Remote", "Austin, TX", "London, UK"]
    sources = ["OfferZen", "Prosple", "Glassdoor"]
    
    jobs = []
    for i in range(limit):
        title = random.choice(titles)
        company = random.choice(companies)
        loc = random.choice(locations)
        source = random.choice(sources)
        date_posted = datetime.now().strftime("%Y-%m-%d")
        
        desc = f"We are looking for a skilled professional for the role of {title} at {company} based in {loc}.\n" \
               f"Requirements include solid experience with problem solving, coding standards, and system design.\n" \
               f"Relocation or visa sponsorship is available for this SDE position."
        
        skills = fallback_extract_skills(desc)
        job_hash = get_job_hash(title, company, date_posted) + f"_{i}"
        
        job_item = {
            "title": title,
            "company": company,
            "location": loc,
            "description": desc,
            "skills": skills,
            "url": "https://example.com/jobs",
            "datePosted": date_posted,
            "dateScraped": datetime.now().strftime("%Y-%m-%d"),
            "jobHash": job_hash,
            "closingDate": "2026-07-31",
            "visaSponsorship": True,
            "yearsExperienceRequired": random.choice([0, 1, 2, None]),
            "sourcePlatform": source,
            "isGhostJob": False
        }
        
        snapshot_path = save_vault_snapshot(job_item)
        job_item["snapshotPath"] = snapshot_path
        
        jobs.append(job_item)
    return jobs

def submit_to_backend(jobs):
    """Sends list of jobs to Java REST API."""
    print(f"[Backend] Submitting {len(jobs)} jobs to {BACKEND_URL}/api/jobs/import...")
    url = f"{BACKEND_URL}/api/jobs/import"
    headers = {
        "X-Scraper-Key": SCRAPER_KEY,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=jobs, headers=headers, timeout=20)
        if response.status_code == 200:
            print(f"[Backend] Success: {response.json()}")
        else:
            print(f"[Backend] Failed with status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[Backend] Error sending data: {e}")

def main():
    parser = argparse.ArgumentParser(description="MultiLang Job Tracker Scraper Module")
    parser.add_argument("--source", type=str, choices=["weworkremotely", "mock", "offerzen", "prosple"], default="weworkremotely",
                        help="Scraper source (weworkremotely RSS, mock generator, offerzen, or prosple)")
    parser.add_argument("--limit", type=int, default=10, help="Max number of jobs to parse")
    args = parser.parse_args()

    # Check if Hugging Face token is loaded
    if not HF_API_TOKEN or HF_API_TOKEN.startswith("your_"):
        print("="*60)
        print("WARNING: Hugging Face API key is missing in '.env'.")
        print("The script will run using local rule-based keyword skill extraction.")
        print("To enable AI zero-shot classification, please provide your HF_API_TOKEN.")
        print("="*60)

    if args.source == "weworkremotely":
        jobs = scrape_weworkremotely(args.limit)
    elif args.source == "mock":
        jobs = generate_mock_jobs(args.limit)
    else:
        jobs = scrape_playwright_source(args.source, args.limit)

    if jobs:
        submit_to_backend(jobs)
    else:
        print("[Main] No jobs scraped. Exiting.")

if __name__ == "__main__":
    main()
