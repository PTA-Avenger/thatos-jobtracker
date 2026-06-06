import os
import sys
import argparse
import requests
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load configuration from .env file
load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")
SCRAPER_KEY = os.getenv("SCRAPER_KEY", "ScraperSuperSecretKey123")
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")

# Candidate skills for Hugging Face zero-shot classification
CANDIDATE_SKILLS = [
    "Java", "Python", "C#", "C++", "JavaScript", "TypeScript", "SQL", 
    "React", "Angular", "Vue", "Spring Boot", "ASP.NET", "Docker", 
    "Kubernetes", "AWS", "Azure", "Git", "HTML", "CSS", "Linux", 
    "Agile", "Excel", "REST API", "NoSQL"
]

def fallback_extract_skills(description):
    """Fallback keyword matcher if Hugging Face API token is missing or error occurs."""
    desc_lower = description.lower()
    found = []
    for skill in CANDIDATE_SKILLS:
        # Avoid matching partial words (e.g. 'C' matching 'Cloud')
        # Simple word boundaries
        skill_lower = skill.lower()
        if f" {skill_lower} " in f" {desc_lower} " or f" {skill_lower}," in f" {desc_lower} " or f" {skill_lower}." in f" {desc_lower} ":
            found.append(skill)
            if len(found) >= 5:
                break
    return ", ".join(found) if found else "General IT"

def extract_skills_hf(description, token):
    """Uses Hugging Face zero-shot classification to identify top skills from job description."""
    if not token or token.startswith("your_"):
        print("[AI] Hugging Face token missing. Using keyword fallback.")
        return fallback_extract_skills(description)

    print(f"[AI] Calling Hugging Face Inference API...")
    headers = {"Authorization": f"Bearer {token}"}
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    
    # Limit context size to prevent exceeding token limits
    payload = {
        "inputs": description[:1200],
        "parameters": {"candidate_labels": CANDIDATE_SKILLS}
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=12)
        if response.status_code == 200:
            result = response.json()
            labels = result.get("labels", [])
            scores = result.get("scores", [])
            # Filter labels with confidence score above 0.3
            top_skills = [labels[i] for i in range(len(labels)) if scores[i] > 0.3]
            selected = top_skills[:5]
            return ", ".join(selected) if selected else fallback_extract_skills(description)
        else:
            print(f"[AI] HF API Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[AI] HF Request Failed: {e}")
        
    return fallback_extract_skills(description)

def get_job_hash(title, company, date_posted):
    """Generate a unique MD5 hash for job deduplication."""
    unique_str = f"{title.lower()}|{company.lower()}|{str(date_posted).lower()}"
    return hashlib.md5(unique_str.encode('utf-8')).hexdigest()

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
        # WeWorkRemotely titles are formatted as: "Company: Job Title"
        if ":" in raw_title:
            company, title = raw_title.split(":", 1)
            company = company.strip()
            title = title.strip()
        else:
            company = "WeWorkRemotely Client"
            title = raw_title.strip()
            
        link = item.link.text if item.link else ""
        pub_date = item.pubDate.text if item.pubDate else datetime.now().strftime("%Y-%m-%d")
        
        # Parse pub_date to a simpler format
        try:
            parsed_date = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
            date_posted = parsed_date.strftime("%Y-%m-%d")
        except Exception:
            date_posted = pub_date[:16] # Fallback string slice
            
        raw_desc = item.description.text if item.description else ""
        # Strip HTML tags from description
        desc_text = BeautifulSoup(raw_desc, "html.parser").get_text().strip()
        
        job_hash = get_job_hash(title, company, date_posted)
        
        # Extract skills (either via HF or keyword matcher)
        skills = extract_skills_hf(desc_text, HF_API_TOKEN)
        
        jobs.append({
            "title": title,
            "company": company,
            "location": "Remote",
            "description": desc_text,
            "skills": skills,
            "url": link,
            "datePosted": date_posted,
            "dateScraped": datetime.now().strftime("%Y-%m-%d"),
            "jobHash": job_hash
        })
        
        print(f"[Scraper] Parsed: '{title}' at '{company}' (Skills: {skills})")
        count += 1
        
    return jobs

def generate_mock_jobs(limit=10):
    """Generates mock job applications for testing without internet dependency."""
    print(f"[Scraper] Generating {limit} mock jobs...")
    import random
    titles = [
        "Software Engineer", "Frontend Developer", "Backend Developer", 
        "Fullstack Engineer", "DevOps Engineer", "Cloud Architect", 
        "Data Analyst", "Database Administrator"
    ]
    companies = ["Google", "Microsoft", "Amazon", "Netflix", "Meta", "Spotify", "Apple", "Uber"]
    locations = ["New York, NY", "Seattle, WA", "San Francisco, CA", "Remote", "Austin, TX", "London, UK"]
    
    jobs = []
    for i in range(limit):
        title = random.choice(titles)
        company = random.choice(companies)
        loc = random.choice(locations)
        date_posted = datetime.now().strftime("%Y-%m-%d")
        
        desc = f"We are looking for a skilled professional for the role of {title} at {company} based in {loc}.\n" \
               f"You will work with high-performing teams to build, deploy, and maintain robust applications.\n" \
               f"Requirements include solid experience with problem solving, coding standards, and system design."
        
        skills = fallback_extract_skills(desc)
        job_hash = get_job_hash(title, company, date_posted) + f"_{i}"
        
        jobs.append({
            "title": title,
            "company": company,
            "location": loc,
            "description": desc,
            "skills": skills,
            "url": "https://example.com/jobs",
            "datePosted": date_posted,
            "dateScraped": datetime.now().strftime("%Y-%m-%d"),
            "jobHash": job_hash
        })
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
        response = requests.post(url, json=jobs, headers=headers, timeout=15)
        if response.status_code == 200:
            print(f"[Backend] Success: {response.json()}")
        else:
            print(f"[Backend] Failed with status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[Backend] Error sending data: {e}")

def main():
    parser = argparse.ArgumentParser(description="MultiLang Job Tracker Scraper Module")
    parser.add_argument("--source", type=str, choices=["weworkremotely", "mock"], default="weworkremotely",
                        help="Scraper source (weworkremotely RSS or mock generator)")
    parser.add_argument("--limit", type=int, default=20, help="Max number of jobs to parse")
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
    else:
        jobs = generate_mock_jobs(args.limit)

    if jobs:
        submit_to_backend(jobs)
    else:
        print("[Main] No jobs scraped. Exiting.")

if __name__ == "__main__":
    main()
