# AI-Driven Dynamic Job Application & Career Assistant

## Project Structure

```
job_assistant/
├── core/
│   ├── __init__.py
│   ├── scraper.py        # Playwright-based job description extractor
│   ├── ai_engine.py      # Gemini API integration for scoring and tailoring
│   └── database.py       # SQLite database management
├── utils/
│   ├── __init__.py
│   ├── config.py         # Configuration and constants
│   └── logger.py         # Logging setup
├── data/
│   ├── job_history.db    # SQLite database (auto-created)
│   └── user_profile.json # User's base resume/profile (template)
├── main.py               # CustomTkinter GUI entry point (TODO)
├── pdf_generator.py      # PDF resume generation (TODO)
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

## Features

- **Job Description Scraping**: Extract text from job posting URLs using Playwright
- **AI-Powered Matching**: Score job applications (A-F) using Google Gemini API
- **Resume Tailoring**: Generate customized bullet points based on job requirements
- **Local Database**: Track application history with SQLite
- **PDF Export**: Generate tailored resumes in PDF format

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Install Playwright browsers: `playwright install`
3. Set your Gemini API key: `export GEMINI_API_KEY="your-api-key"`
4. Create your profile: Edit `data/user_profile.json`
5. Run the application: `python main.py`
