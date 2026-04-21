"""Job description scraper using Playwright."""

import logging
from typing import Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from utils.logger import setup_logger
from utils.config import Config

# Initialize logger
logger = setup_logger(__name__)


class JobScraper:
    """
    Extract job description text from URLs using Playwright.
    
    This scraper only extracts publicly available content without
    attempting to log in or bypass any security measures.
    """
    
    def __init__(self, timeout: int = None):
        """
        Initialize the scraper.
        
        Args:
            timeout: Page load timeout in milliseconds (default: from Config)
        """
        self.timeout = timeout or Config.PAGE_LOAD_TIMEOUT
        self.wait_time = Config.WAIT_FOR_CONTENT
        logger.info(f"JobScraper initialized with timeout={self.timeout}ms")
    
    def scrape(self, url: str) -> Optional[str]:
        """
        Scrape text content from a job posting URL.
        
        Args:
            url: The URL of the job posting
            
        Returns:
            Extracted text content, or None if scraping fails
            
        Raises:
            ValueError: If URL is invalid or empty
            RuntimeError: If Playwright encounters an error
        """
        if not url or not isinstance(url, str):
            logger.error("Invalid URL provided")
            raise ValueError("URL must be a non-empty string")
        
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            logger.error(f"Invalid URL format: {url}")
            raise ValueError("URL must start with http:// or https://")
        
        logger.info(f"Scraping URL: {url}")
        
        try:
            with sync_playwright() as p:
                # Launch browser in headless mode
                browser = p.chromium.launch(headless=True)
                
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = context.new_page()
                
                # Set timeout
                page.set_default_timeout(self.timeout)
                
                try:
                    # Navigate to the page
                    logger.debug(f"Navigating to {url}")
                    response = page.goto(url, wait_until="domcontentloaded")
                    
                    # Check if page loaded successfully
                    if response and not response.ok:
                        logger.warning(f"Page returned status code: {response.status}")
                    
                    # Wait for content to fully render
                    page.wait_for_timeout(self.wait_time)
                    
                    # Extract text from main content areas
                    text = self._extract_text(page)
                    
                    if not text or len(text.strip()) < 50:
                        logger.warning("Extracted text is too short, may indicate scraping issue")
                    
                    logger.info(f"Successfully extracted {len(text)} characters")
                    return text
                    
                except PlaywrightTimeout:
                    logger.error(f"Timeout while loading {url}")
                    raise RuntimeError(f"Page load timeout after {self.timeout}ms")
                finally:
                    browser.close()
                    
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            raise RuntimeError(f"Failed to scrape URL: {str(e)}")
    
    def _extract_text(self, page) -> str:
        """
        Extract text from common job posting elements.
        
        Args:
            page: Playwright page object
            
        Returns:
            Concatenated text content from relevant elements
        """
        # JavaScript to extract text from common job posting selectors
        extract_script = """
        () => {
            const selectors = [
                'main',
                'article', 
                '.job-description',
                '.job-details',
                '[class*="job"]',
                '[id*="job"]',
                'body'
            ];
            
            let content = [];
            
            for (const selector of selectors) {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    // Skip scripts, styles, and hidden elements
                    if (el.tagName.toLowerCase() in ['script', 'style', 'noscript']) {
                        return;
                    }
                    
                    const text = el.innerText.trim();
                    if (text && text.length > 20) {
                        content.push(text);
                    }
                });
            }
            
            // Remove duplicates and join
            const unique = [...new Set(content)];
            return unique.join('\\n\\n');
        }
        """
        
        try:
            text = page.evaluate(extract_script)
            return self._clean_text(text)
        except Exception as e:
            logger.warning(f"Text extraction error: {e}, falling back to body text")
            # Fallback: get all body text
            return self._clean_text(page.content())
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text with normalized whitespace
        """
        if not text:
            return ""
        
        # Replace multiple newlines with double newline
        import re
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove excessive whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Strip each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Remove multiple consecutive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
