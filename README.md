# AI Job Search & Resume Tailoring Engine

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-orange.svg)](https://github.com/TomSchimansky/CustomTkinter)

## 📋 Overview

A comprehensive **Final Year Project** system for AI-driven job search and resume tailoring. This desktop application helps job seekers:

- **Search Jobs**: Aggregate listings from multiple job boards (Indeed, LinkedIn, Glassdoor, Google Jobs)
- **AI Matching**: Get intelligent match scores (A-F) comparing your profile against job requirements
- **Resume Tailoring**: Generate customized resumes optimized for specific job postings
- **Track Applications**: Maintain a local database of your job application history
- **Cost Transparency**: Estimate API costs before running AI analyses

### Key Features

| Feature | Description |
|---------|-------------|
| 🖥️ Desktop GUI | Modern dark-themed interface using CustomTkinter |
| 🤖 AI Analysis | Google Gemini-powered job matching with confidence scores |
| 📄 PDF Generation | Professional ATS-friendly resume and cover letter export |
| 🔍 Web Scraping | Playwright-based job description extraction |
| 💾 Local Storage | SQLite database for application tracking |
| 📊 Analytics | Dashboard with statistics and match score distribution |
| ⚙️ Cost Estimator | Transparent API cost calculation per analysis |

---

## 🏗️ Architecture

```
workspace/
├── job_assistant/              # Main application package
│   ├── main.py                 # Entry point & GUI application
│   ├── core/                   # Core business logic
│   │   ├── ai_engine.py        # Google Gemini AI integration
│   │   ├── scraper.py          # Job description web scraper
│   │   ├── job_search.py       # Multi-source job aggregator
│   │   ├── resume_parser.py    # PDF/DOCX resume parser
│   │   ├── pdf_generator.py    # Resume/Cover letter PDF generator
│   │   └── database.py         # SQLite database manager
│   ├── utils/                  # Utilities
│   │   ├── config.py           # Configuration & constants
│   │   └── logger.py           # Logging setup
│   ├── data/                   # Application data
│   │   ├── job_history.db      # SQLite database
│   │   ├── user_profile.json   # User profile template
│   │   └── resumes/            # Generated PDFs
│   └── requirements.txt        # Python dependencies
├── tests/                      # Test suite
│   ├── test_ai_engine.py
│   ├── test_scraper.py
│   ├── test_resume_parser.py
│   └── test_database.py
├── docs/                       # Documentation
│   ├── USER_GUIDE.md
│   ├── API_REFERENCE.md
│   └── ACADEMIC_REPORT.md
├── LICENSE                     # MIT License
└── README.md                   # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Google Gemini API key ([Get one free](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository:**
   ```bash
   cd /workspace
   ```

2. **Install dependencies:**
   ```bash
   pip install -r job_assistant/requirements.txt
   ```

3. **Install Playwright browsers:**
   ```bash
   playwright install
   ```

4. **Set your API key:**
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```
   
   Or configure it in the application Settings menu.

5. **Run the application:**
   ```bash
   python job_assistant/main.py
   ```

---

## 📖 Usage Guide

### 1. Upload Your Resume

- Click **"Upload CV/Resume"** in the Job Analysis tab
- Select your PDF or DOCX resume file
- The system will parse and extract your skills, experience, and contact info

### 2. Search for Jobs

- Enter job title/skills (e.g., "Python Developer")
- Optionally specify location (e.g., "San Francisco, CA")
- Select sources (Indeed, LinkedIn, etc.)
- Click **"Search Jobs"**

### 3. Analyze Job Matches

- Browse search results in the list
- Click on any job to view details
- Click **"Analyze with AI"** to get your match score

### 4. Review AI Analysis

The AI provides:
- **Match Score** (A-F): How well you match the job requirements
- **Confidence**: AI's confidence in its assessment
- **Matched Skills**: Skills you have that the job requires
- **Missing Skills**: Skills the job requires that you lack
- **Tailored Bullets**: Custom resume bullet points for this job
- **Summary**: Brief assessment of your fit

### 5. Generate Tailored Resume

- Go to the **"Resume Preview"** tab
- Click **"Generate Tailored Resume"**
- Download the PDF optimized for the selected job

### 6. Track Applications

- Click **"Save to History"** to log analyzed jobs
- View all tracked applications in **"Search History"**
- Filter by match score or date

---

## 💰 Cost Estimation

The application uses Google Gemini API for AI analysis. Costs are transparently displayed:

| Operation | Tokens (approx) | Cost (USD)* |
|-----------|-----------------|-------------|
| Job Analysis | ~2,000 input + ~500 output | $0.0003 |
| Resume Generation | ~1,500 input + ~800 output | $0.00035 |

*Based on gemini-1.5-flash pricing at $0.000075/1K input tokens and $0.0003/1K output tokens.

**Estimated monthly cost for 100 job analyses: ~$0.03**

---

## 🧪 Running Tests

```bash
cd /workspace
python -m pytest tests/ -v
```

### Test Coverage

- ✅ AI Engine (mocked API responses)
- ✅ Resume Parser (sample PDF/DOCX files)
- ✅ Database Operations (in-memory SQLite)
- ✅ Scraper (mocked HTTP responses)

---

## 📚 Academic Compliance

This project is designed as a **Final Year Project** with the following academic considerations:

### Originality
- All code is original Python implementation
- Conceptually inspired by Career-Ops but fully re-engineered
- No copied code from external sources

### Documentation
- Comprehensive inline docstrings
- Module-level documentation
- User guide and API reference

### Ethical Considerations
- Only scrapes publicly available job data
- No login bypass or authentication circumvention
- Respects robots.txt and rate limits
- Transparent about AI usage

### Citation

If using this project in academic work, cite as:

```bibtex
@software{ai_job_search_2024,
  title = {AI Job Search \& Resume Tailoring Engine},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/ai-job-search},
  license = {MIT}
}
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | `""` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING) | `INFO` |
| `DATA_DIR` | Custom data directory path | `./job_assistant/data` |

### Config File (`utils/config.py`)

```python
# AI Model settings
AI_MODEL = "gemini-1.5-flash"
TEMPERATURE = 0.1  # Low for consistent scoring

# Scraping settings
PAGE_LOAD_TIMEOUT = 30000  # milliseconds
WAIT_FOR_CONTENT = 2000    # milliseconds

# Valid match scores
VALID_SCORES = ["A", "B", "C", "D", "F"]
```

---

## 🛠️ Troubleshooting

### Common Issues

**1. "Gemini API key not configured"**
- Set the `GEMINI_API_KEY` environment variable
- Or enter your key in Settings → API Configuration

**2. "Playwright browser not found"**
- Run: `playwright install`
- For headless servers: `playwright install --with-deps chromium`

**3. "Failed to parse resume"**
- Ensure your resume is in PDF or DOCX format
- Check that the file is not password-protected
- Try a simpler resume format

**4. "No jobs found"**
- Verify your internet connection
- Try different search terms
- Some job boards may block automated access

### Logs

Application logs are written to the console and can be configured via `LOG_LEVEL`.

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Development

### Adding New Job Sources

1. Add URL template in `JobSearchAggregator.search_urls`
2. Implement `_parse_<source>()` method
3. Implement `_process_<source>_job()` method
4. Update source selector in UI

### Customizing AI Prompts

Edit the prompt template in `AIEngine._build_prompt()` to adjust:
- Scoring criteria
- Output format
- Analysis focus areas

### Building Executables

```bash
pip install pyinstaller
pyinstaller --onefile --windowed job_assistant/main.py
```

---

## 🙏 Acknowledgments

- **Career-Ops**: Conceptual inspiration for job search automation
- **Google Gemini**: AI/LLM API for job matching
- **CustomTkinter**: Modern Python GUI framework
- **Playwright**: Reliable web automation
- **ReportLab**: Professional PDF generation

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review the FAQ section

---

**Built with ❤️ for Final Year Project**