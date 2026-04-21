"""Configuration constants for the application."""

import os
from pathlib import Path


class Config:
    """Application configuration and constants."""
    
    # Base directory
    BASE_DIR = Path(__file__).parent.parent
    
    # Data directory
    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Database
    DATABASE_PATH = DATA_DIR / "job_history.db"
    
    # User profile
    USER_PROFILE_PATH = DATA_DIR / "user_profile.json"
    
    # API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Scraping settings
    PAGE_LOAD_TIMEOUT = 30000  # milliseconds
    WAIT_FOR_CONTENT = 2000  # milliseconds to wait after page load
    
    # AI settings
    AI_MODEL = "gemini-pro"
    TEMPERATURE = 0.1  # Low temperature for consistent scoring
    
    # Valid match scores
    VALID_SCORES = ["A", "B", "C", "D", "F"]
    
    @classmethod
    def validate_api_key(cls) -> bool:
        """Check if Gemini API key is configured."""
        return bool(cls.GEMINI_API_KEY and cls.GEMINI_API_KEY.strip())
    
    @classmethod
    def get_default_profile(cls) -> dict:
        """Return a default user profile template."""
        return {
            "personal_info": {
                "name": "Your Name",
                "email": "your.email@example.com",
                "phone": "+1-234-567-8900",
                "location": "City, State",
                "linkedin": "linkedin.com/in/yourprofile",
                "github": "github.com/yourusername"
            },
            "summary": "Brief professional summary about yourself.",
            "skills": [
                "Python",
                "JavaScript",
                "SQL",
                "Git"
            ],
            "experience": [
                {
                    "title": "Job Title",
                    "company": "Company Name",
                    "duration": "Jan 2020 - Present",
                    "bullets": [
                        "Accomplishment or responsibility",
                        "Another accomplishment"
                    ]
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "University Name",
                    "graduation": "May 2020"
                }
            ],
            "projects": [
                {
                    "name": "Project Name",
                    "description": "Brief description of the project",
                    "technologies": ["Python", "React"]
                }
            ]
        }
