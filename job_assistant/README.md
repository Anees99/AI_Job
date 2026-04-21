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
├── main.py               # CustomTkinter GUI entry point
├── pdf_generator.py      # PDF resume generation (TODO)
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

## Features

- **Job Description Scraping**: Extract text from job posting URLs using Playwright (headless, no login required)
- **AI-Powered Matching**: Score job applications (A-F) using Google Gemini API with confidence metrics
- **Resume Tailoring**: Generate customized bullet points based on job requirements and your profile
- **Local Database**: Track application history with SQLite including scores, dates, and summaries
- **Modern GUI**: Clean, dark-themed desktop interface built with CustomTkinter
- **PDF Export**: Generate tailored resumes in PDF format (coming soon)

## Usage Workflow

1. **Configure Your Profile**: Click "My Profile" to edit your skills, experience, and qualifications in JSON format
2. **Set API Key**: Click "Settings" to enter your Google Gemini API key
3. **Analyze Jobs**: 
   - Paste a job posting URL in the "Job Analysis" tab
   - Click "Extract Description" to scrape the job details
   - Click "Analyze with AI" to get your match score (A-F)
4. **Review Results**: View matched/missing skills, AI summary, and tailored resume bullets
5. **Save History**: Click "Save to History" to log the analysis in your local database
6. **Copy Bullets**: Use the tailored bullet points in your actual resume

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Install Playwright browsers: `playwright install`
3. Set your Gemini API key: `export GEMINI_API_KEY="your-api-key"` (or configure in Settings)
4. Create your profile: Edit `data/user_profile.json` or use the GUI editor
5. Run the application: `python main.py`
