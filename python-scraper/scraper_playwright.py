import time
from playwright.sync_api import sync_playwright

def run_scraper_playwright(source, limit=10):
    print(f"[Playwright] Starting scraper for {source} (limit={limit})...")
    jobs = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # 1. Fetch listing links from directory
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        job_urls = []
        if source == "offerzen":
            url = "https://www.offerzen.com/jobs"
            try:
                print(f"[Playwright] Navigating to: {url}")
                page.goto(url, timeout=30000)
                print("[Playwright] Directory loaded. Waiting for job cards (resolving WAF if needed)...")
                page.wait_for_selector("a[href*='/job/']", timeout=25000)
                
                # Scroll down a bit to load more items
                page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                page.wait_for_timeout(2000)
                
                # Find all job links
                links = page.locator("a").all()
                for link in links:
                    href = link.get_attribute("href")
                    if href and "/job/" in href:
                        full_url = f"https://www.offerzen.com{href}" if href.startswith("/") else href
                        if full_url not in job_urls:
                            job_urls.append(full_url)
            except Exception as e:
                print(f"[Playwright] OfferZen directory load failed: {e}")
        
        elif source == "prosple":
            url = "https://za.prosple.com/graduate-jobs-south-africa"
            try:
                print(f"[Playwright] Navigating to: {url}")
                page.goto(url, timeout=30000)
                print("[Playwright] Directory loaded. Waiting for opportunity cards...")
                page.wait_for_selector("a[href*='/jobs-internships/']", timeout=25000)
                page.wait_for_timeout(2000)
                
                # Find all job links
                links = page.locator("a").all()
                for link in links:
                    href = link.get_attribute("href")
                    if href and "/graduate-employers/" in href and "/jobs-internships/" in href:
                        full_url = f"https://za.prosple.com{href}" if href.startswith("/") else href
                        if full_url not in job_urls:
                            job_urls.append(full_url)
            except Exception as e:
                print(f"[Playwright] Prosple directory load failed: {e}")
        
        # Clean up directory page/context
        page.close()
        context.close()
        
        print(f"[Playwright] Found {len(job_urls)} {source} listing links. Processing top {limit}...")
        
        # 2. Iterate through detail pages using fresh contexts to prevent memory exhaustion
        for idx, job_url in enumerate(job_urls[:limit]):
            print(f"[Playwright] [{idx+1}/{min(len(job_urls), limit)}] Navigating to: {job_url}")
            detail_context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            detail_page = detail_context.new_page()
            
            try:
                if source == "offerzen":
                    # Navigate and wait for h2 which represents the job title and is not present on Vercel security page
                    detail_page.goto(job_url, timeout=30000)
                    detail_page.wait_for_selector("h2", timeout=25000)
                    
                    # Extract title
                    title = ""
                    h1_el = detail_page.locator("h1")
                    if h1_el.count() > 0:
                        title = h1_el.first.inner_text().strip()
                    if not title or title == "Vercel Security Checkpoint":
                        h2_el = detail_page.locator("h2")
                        if h2_el.count() > 0:
                            title = h2_el.first.inner_text().strip()
                    if not title:
                        title = "Unknown OfferZen Title"
                    
                    # Extract company name
                    company = "OfferZen Employer"
                    company_links = detail_page.locator("a[href*='/companies/']").all()
                    for c_link in company_links:
                        c_text = c_link.inner_text().strip()
                        if c_text and len(c_text) > 1:
                            company = c_text
                            break
                    if company == "OfferZen Employer":
                        h2_el = detail_page.locator("h2")
                        if h2_el.count() > 0:
                            # Sometimes the company is on an h2/subtitle
                            company = h2_el.first.inner_text().strip()
                    
                    # Extract description
                    desc_selectors = [".job-description", "[data-test='job-description']", "article", "main"]
                    description = ""
                    for selector in desc_selectors:
                        el = detail_page.locator(selector)
                        if el.count() > 0:
                            description = el.first.inner_text().strip()
                            if len(description) > 100:
                                break
                    if not description or len(description) < 100:
                        description = detail_page.locator("body").inner_text().strip()
                        
                    # Clean strings
                    title = title.replace("\n", " ").strip()
                    company = company.replace("\n", " ").strip()
                    
                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": "Remote / South Africa",
                        "description": description,
                        "url": job_url,
                        "source_platform": "OfferZen"
                    })
                    print(f"  -> Successfully parsed '{title}' at '{company}'")
                    
                elif source == "prosple":
                    # Navigate and wait for h1 which represents the opportunity title and is not present on AWS WAF challenge
                    detail_page.goto(job_url, timeout=30000)
                    detail_page.wait_for_selector("h1", timeout=25000)
                    
                    # Extract title
                    title_el = detail_page.locator("h1")
                    title = title_el.first.inner_text().strip() if title_el.count() > 0 else "Unknown Graduate Role"
                    
                    # Extract company name
                    company = "Prosple Partner"
                    employer_links = detail_page.locator("a[href*='/graduate-employers/']").all()
                    for el_link in employer_links:
                        el_href = el_link.get_attribute("href")
                        if el_href and el_href.count("/") == 2: # e.g. /graduate-employers/company-name
                            el_text = el_link.inner_text().strip()
                            if el_text and "graduate employers" not in el_text.lower():
                                company = el_text
                                break
                    
                    # Extract description
                    desc_selectors = [".prose", "article", "#opportunity-details", ".opportunity-body", "main"]
                    description = ""
                    for selector in desc_selectors:
                        el = detail_page.locator(selector)
                        if el.count() > 0:
                            description = el.first.inner_text().strip()
                            if len(description) > 100:
                                break
                    if not description or len(description) < 100:
                        description = detail_page.locator("body").inner_text().strip()
                        
                    # Clean strings
                    title = title.replace("\n", " ").strip()
                    company = company.replace("\n", " ").strip()
                    
                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": "South Africa",
                        "description": description,
                        "url": job_url,
                        "source_platform": "Prosple"
                    })
                    print(f"  -> Successfully parsed '{title}' at '{company}'")
                    
            except Exception as ex:
                print(f"  -> Error parsing job at {job_url}: {ex}")
            finally:
                detail_page.close()
                detail_context.close()
                
        browser.close()
        
    return jobs

if __name__ == "__main__":
    # Test script locally
    res = run_scraper_playwright("offerzen", limit=2)
    print(f"OfferZen test results: {len(res)} jobs parsed.")
    res_p = run_scraper_playwright("prosple", limit=2)
    print(f"Prosple test results: {len(res_p)} jobs parsed.")
