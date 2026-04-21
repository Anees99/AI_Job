"""Job search aggregator to find recent job postings from various sources."""

import logging
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus, urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from utils.logger import setup_logger
from utils.config import Config

# Initialize logger
logger = setup_logger(__name__)


class JobSearchAggregator:
    """
    Search for recent job postings across multiple platforms.
    
    Supports:
    - LinkedIn Jobs (public pages only)
    - Indeed
    - Glassdoor (public pages)
    - Google Jobs
    - Company career pages
    
    Note: Only scrapes publicly available content without logging in
    or bypassing any security measures.
    """
    
    def __init__(self, max_results: int = 20):
        """
        Initialize the job search aggregator.
        
        Args:
            max_results: Maximum number of job listings to return per search
        """
        self.max_results = max_results
        self.timeout = Config.PAGE_LOAD_TIMEOUT
        self.wait_time = Config.WAIT_FOR_CONTENT
        
        # Job board search URL templates
        self.search_urls = {
            'linkedin': f"https://www.linkedin.com/jobs/search/?keywords={{query}}&location={{location}}",
            'indeed': f"https://www.indeed.com/jobs?q={{query}}&l={{location}}",
            'glassdoor': f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={{query}}&locT={{location}}",
            'google': f"https://www.google.com/search?q={{query}}+jobs+{{location}}&ibp=htl;jobs"
        }
        
        logger.info(f"JobSearchAggregator initialized (max_results={max_results})")
    
    def search_jobs(
        self, 
        query: str, 
        location: str = "", 
        sources: List[str] = None,
        days_old: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Search for jobs matching the query across multiple sources.
        
        Args:
            query: Job title/skills to search for (e.g., "Python Developer")
            location: Geographic location (e.g., "San Francisco, CA")
            sources: List of job boards to search (default: ['indeed', 'linkedin'])
            days_old: Only include jobs posted within this many days
            
        Returns:
            List of job posting dictionaries with keys:
            - title: Job title
            - company: Company name
            - location: Job location
            - url: Direct link to job posting
            - source: Source job board
            - posted_date: When job was posted (if available)
            - description_snippet: Short description preview
            - salary: Salary range (if available)
            
        Raises:
            RuntimeError: If search fails across all sources
        """
        if not query or not isinstance(query, str):
            logger.error("Invalid search query")
            raise ValueError("Search query must be a non-empty string")
        
        sources = sources or ['indeed', 'linkedin']
        location = location.strip() if location else ""
        
        logger.info(f"Searching for '{query}' in {location or 'any location'}")
        logger.debug(f"Sources: {sources}, Max results: {self.max_results}")
        
        all_jobs = []
        
        for source in sources:
            if source not in self.search_urls:
                logger.warning(f"Unknown source: {source}, skipping")
                continue
            
            try:
                logger.info(f"Searching {source}...")
                jobs = self._search_source(source, query, location)
                all_jobs.extend(jobs)
                logger.info(f"Found {len(jobs)} jobs from {source}")
            except Exception as e:
                logger.error(f"Search failed on {source}: {str(e)}")
                # Continue with other sources
        
        if not all_jobs:
            logger.warning("No jobs found from any source")
            return []
        
        # Filter by date and deduplicate
        filtered_jobs = self._filter_and_deduplicate(all_jobs, days_old)
        
        # Sort by relevance (recent first, then by source priority)
        filtered_jobs.sort(key=lambda x: (
            x.get('posted_days_ago', 999),
            sources.index(x.get('source', 'unknown')) if x.get('source') in sources else 999
        ))
        
        logger.info(f"Total unique jobs after filtering: {len(filtered_jobs)}")
        return filtered_jobs[:self.max_results]
    
    def _search_source(self, source: str, query: str, location: str) -> List[Dict[str, Any]]:
        """
        Search a specific job board source.
        
        Args:
            source: Source identifier (e.g., 'indeed', 'linkedin')
            query: Search query
            location: Location filter
            
        Returns:
            List of job posting dictionaries
        """
        encoded_query = quote_plus(query)
        encoded_location = quote_plus(location) if location else ""
        
        search_url = self.search_urls[source].format(
            query=encoded_query,
            location=encoded_location
        )
        
        logger.debug(f"Searching URL: {search_url}")
        
        jobs = []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = context.new_page()
                page.set_default_timeout(self.timeout)
                
                try:
                    page.goto(search_url, wait_until="domcontentloaded")
                    page.wait_for_timeout(self.wait_time)
                    
                    # Extract jobs based on source-specific selectors
                    if source == 'indeed':
                        jobs = self._parse_indeed(page, query)
                    elif source == 'linkedin':
                        jobs = self._parse_linkedin(page, query)
                    elif source == 'glassdoor':
                        jobs = self._parse_glassdoor(page, query)
                    elif source == 'google':
                        jobs = self._parse_google_jobs(page, query)
                    
                except PlaywrightTimeout:
                    logger.warning(f"Timeout searching {source}")
                finally:
                    browser.close()
                    
        except Exception as e:
            logger.error(f"Playwright error searching {source}: {str(e)}")
        
        return jobs
    
    def _parse_indeed(self, page, query: str) -> List[Dict[str, Any]]:
        """Parse job listings from Indeed."""
        logger.debug("Parsing Indeed results")
        
        extract_script = """
        () => {
            const jobs = [];
            const jobCards = document.querySelectorAll('#mosaic-provider-jobcards li[data-jk], div.job_seen_beacon');
            
            jobCards.forEach((card, index) => {
                if (jobs.length >= 15) return;
                
                const titleEl = card.querySelector('h2 a, .jobTitle span[title]');
                const companyEl = card.querySelector('[data-testid="company-name"], span.companyName');
                const locationEl = card.querySelector('[data-testid="text-location"]');
                const dateEl = card.querySelector('span.date');
                const salaryEl = card.querySelector('.salary-snippet-container, .metadata.salary-snippet-container');
                const summaryEl = card.querySelector('.job-snippet, .job-snippet-wrapper');
                
                if (!titleEl) return;
                
                const url = titleEl.getAttribute('href');
                if (!url || !url.includes('/rc/clk')) return;
                
                // Clean Indeed URLs
                const cleanUrl = url.startsWith('http') ? url : `https://www.indeed.com${url}`;
                
                jobs.push({
                    title: titleEl.textContent?.trim() || '',
                    company: companyEl?.textContent?.trim() || 'Unknown',
                    location: locationEl?.textContent?.trim() || '',
                    url: cleanUrl,
                    source: 'indeed',
                    posted_text: dateEl?.textContent?.trim() || '',
                    salary: salaryEl?.textContent?.trim() || '',
                    description_snippet: summaryEl?.textContent?.trim() || ''
                });
            });
            
            return jobs;
        }
        """
        
        try:
            raw_jobs = page.evaluate(extract_script)
            return [self._process_indeed_job(job) for job in raw_jobs if job.get('title')]
        except Exception as e:
            logger.error(f"Indeed parsing error: {e}")
            return []
    
    def _process_indeed_job(self, job: Dict) -> Optional[Dict]:
        """Process and normalize Indeed job data."""
        # Parse posted date
        posted_days = self._parse_relative_date(job.get('posted_text', ''))
        
        return {
            'title': job.get('title', ''),
            'company': job.get('company', 'Unknown'),
            'location': job.get('location', ''),
            'url': job.get('url', ''),
            'source': 'indeed',
            'posted_date': self._days_ago_to_date(posted_days),
            'posted_days_ago': posted_days,
            'salary': job.get('salary', ''),
            'description_snippet': job.get('description_snippet', '')[:200]
        }
    
    def _parse_linkedin(self, page, query: str) -> List[Dict[str, Any]]:
        """Parse job listings from LinkedIn (public pages only)."""
        logger.debug("Parsing LinkedIn results")
        
        extract_script = """
        () => {
            const jobs = [];
            const jobCards = document.querySelectorAll('li.jobs-search-results__list-item');
            
            jobCards.forEach((card, index) => {
                if (jobs.length >= 15) return;
                
                const titleEl = card.querySelector('a.job-card-list__title');
                const companyEl = card.querySelector('div.artdeco-entity-lockup__subtitle');
                const locationEl = card.querySelector('span.job-search-card__location');
                const timeEl = card.querySelector('time');
                
                if (!titleEl) return;
                
                const url = titleEl.getAttribute('href');
                if (!url) return;
                
                const cleanUrl = url.startsWith('http') ? url : `https://www.linkedin.com${url}`;
                
                jobs.push({
                    title: titleEl.textContent?.trim() || '',
                    company: companyEl?.textContent?.trim() || 'Unknown',
                    location: locationEl?.textContent?.trim() || '',
                    url: cleanUrl.split('?')[0], // Remove tracking params
                    source: 'linkedin',
                    posted_text: timeEl?.dateTime || '',
                    description_snippet: ''
                });
            });
            
            return jobs;
        }
        """
        
        try:
            raw_jobs = page.evaluate(extract_script)
            return [self._process_linkedin_job(job) for job in raw_jobs if job.get('title')]
        except Exception as e:
            logger.error(f"LinkedIn parsing error: {e}")
            return []
    
    def _process_linkedin_job(self, job: Dict) -> Optional[Dict]:
        """Process and normalize LinkedIn job data."""
        # LinkedIn uses ISO date format in time element
        posted_days = 999
        posted_date = None
        
        if job.get('posted_text'):
            try:
                posted_dt = datetime.fromisoformat(job['posted_text'].replace('Z', '+00:00'))
                posted_days = (datetime.now(posted_dt.tzinfo) - posted_dt).days
                posted_date = posted_dt.isoformat()
            except:
                pass
        
        return {
            'title': job.get('title', ''),
            'company': job.get('company', 'Unknown'),
            'location': job.get('location', ''),
            'url': job.get('url', ''),
            'source': 'linkedin',
            'posted_date': posted_date,
            'posted_days_ago': posted_days,
            'salary': '',
            'description_snippet': ''
        }
    
    def _parse_glassdoor(self, page, query: str) -> List[Dict[str, Any]]:
        """Parse job listings from Glassdoor."""
        logger.debug("Parsing Glassdoor results")
        
        extract_script = """
        () => {
            const jobs = [];
            const jobCards = document.querySelectorAll('li.react-tiles-view__item, div.jobListing');
            
            jobCards.forEach((card, index) => {
                if (jobs.length >= 15) return;
                
                const titleEl = card.querySelector('a.jobLink, h2 a');
                const companyEl = card.querySelector('.employerName, .ng-binding');
                const locationEl = card.querySelector('.location, .col-md-4.location');
                const dateEl = card.querySelector('.age, .newTag');
                
                if (!titleEl) return;
                
                const url = titleEl.getAttribute('href');
                if (!url) return;
                
                const cleanUrl = url.startsWith('http') ? url : `https://www.glassdoor.com${url}`;
                
                jobs.push({
                    title: titleEl.textContent?.trim() || '',
                    company: companyEl?.textContent?.trim() || 'Unknown',
                    location: locationEl?.textContent?.trim() || '',
                    url: cleanUrl,
                    source: 'glassdoor',
                    posted_text: dateEl?.textContent?.trim() || '',
                    description_snippet: ''
                });
            });
            
            return jobs;
        }
        """
        
        try:
            raw_jobs = page.evaluate(extract_script)
            return [self._process_generic_job(job, 'glassdoor') for job in raw_jobs if job.get('title')]
        except Exception as e:
            logger.error(f"Glassdoor parsing error: {e}")
            return []
    
    def _parse_google_jobs(self, page, query: str) -> List[Dict[str, Any]]:
        """Parse job listings from Google Jobs."""
        logger.debug("Parsing Google Jobs results")
        
        extract_script = """
        () => {
            const jobs = [];
            const jobCards = document.querySelectorAll('a[jsname][data-href], div.BjJfJd');
            
            jobCards.forEach((card, index) => {
                if (jobs.length >= 15) return;
                
                const titleEl = card.querySelector('div[role='heading'], h3');
                const companyEl = card.querySelector('.CSQIe, .rQXrcc');
                const locationEl = card.querySelector('.QbL2zc, .VfkEw');
                const dateEl = card.querySelector('.QsDjHe, .HcRWhb');
                
                if (!titleEl && !card.getAttribute('data-href')) return;
                
                const url = card.getAttribute('data-href') || card.href;
                if (!url) return;
                
                jobs.push({
                    title: titleEl?.textContent?.trim() || '',
                    company: companyEl?.textContent?.trim() || 'Unknown',
                    location: locationEl?.textContent?.trim() || '',
                    url: url,
                    source: 'google',
                    posted_text: dateEl?.textContent?.trim() || '',
                    description_snippet: ''
                });
            });
            
            return jobs;
        }
        """
        
        try:
            raw_jobs = page.evaluate(extract_script)
            return [self._process_generic_job(job, 'google') for job in raw_jobs if job.get('title')]
        except Exception as e:
            logger.error(f"Google Jobs parsing error: {e}")
            return []
    
    def _process_generic_job(self, job: Dict, source: str) -> Optional[Dict]:
        """Process generic job data from any source."""
        posted_days = self._parse_relative_date(job.get('posted_text', ''))
        
        return {
            'title': job.get('title', ''),
            'company': job.get('company', 'Unknown'),
            'location': job.get('location', ''),
            'url': job.get('url', ''),
            'source': source,
            'posted_date': self._days_ago_to_date(posted_days),
            'posted_days_ago': posted_days,
            'salary': '',
            'description_snippet': job.get('description_snippet', '')[:200]
        }
    
    def _filter_and_deduplicate(
        self, 
        jobs: List[Dict], 
        days_old: int
    ) -> List[Dict]:
        """
        Filter jobs by age and remove duplicates.
        
        Args:
            jobs: List of job dictionaries
            days_old: Maximum age in days
            
        Returns:
            Filtered and deduplicated list
        """
        # Deduplicate by URL
        seen_urls = set()
        unique_jobs = []
        
        for job in jobs:
            url = job.get('url', '')
            # Normalize URL for comparison
            url_normalized = url.lower().split('?')[0].rstrip('/')
            
            if url_normalized in seen_urls:
                continue
            
            seen_urls.add(url_normalized)
            
            # Filter by age
            if job.get('posted_days_ago', 0) <= days_old:
                unique_jobs.append(job)
            else:
                logger.debug(f"Filtered out old job: {job.get('title')} ({job.get('posted_days_ago')} days)")
        
        return unique_jobs
    
    def _parse_relative_date(self, date_text: str) -> int:
        """
        Parse relative date strings like "2 days ago", "Just posted".
        
        Args:
            date_text: Date string to parse
            
        Returns:
            Number of days ago (999 if unparseable)
        """
        if not date_text:
            return 999
        
        date_text = date_text.lower().strip()
        
        # Handle "just posted", "today"
        if any(term in date_text for term in ['just posted', 'today', 'new', 'fresh']):
            return 0
        
        # Handle "yesterday"
        if 'yesterday' in date_text:
            return 1
        
        # Handle "X days ago"
        match = re.search(r'(\d+)\s*days?', date_text)
        if match:
            return int(match.group(1))
        
        # Handle "X hours ago" (convert to days)
        match = re.search(r'(\d+)\s*hours?', date_text)
        if match:
            hours = int(match.group(1))
            return max(0, hours // 24)
        
        # Handle "X weeks ago"
        match = re.search(r'(\d+)\s*weeks?', date_text)
        if match:
            return int(match.group(1)) * 7
        
        return 999
    
    def _days_ago_to_date(self, days_ago: int) -> Optional[str]:
        """Convert days ago to ISO date string."""
        if days_ago >= 999:
            return None
        
        date = datetime.now() - timedelta(days=days_ago)
        return date.isoformat()
    
    def save_search_results(self, jobs: List[Dict], output_path: str) -> str:
        """
        Save search results to JSON file.
        
        Args:
            jobs: List of job dictionaries
            output_path: Path to save JSON file
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        results = {
            'search_timestamp': datetime.now().isoformat(),
            'total_jobs': len(jobs),
            'jobs': jobs
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(jobs)} job results to {output_path}")
        return str(output_path)
    
    def load_search_results(self, json_path: str) -> List[Dict]:
        """
        Load search results from JSON file.
        
        Args:
            json_path: Path to JSON file
            
        Returns:
            List of job dictionaries
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        jobs = data.get('jobs', [])
        logger.info(f"Loaded {len(jobs)} job results from {json_path}")
        return jobs
