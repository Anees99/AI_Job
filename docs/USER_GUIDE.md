# User Guide - AI Job Search & Resume Tailoring Engine

## Table of Contents

1. [Getting Started](#getting-started)
2. [First-Time Setup](#first-time-setup)
3. [Core Features](#core-features)
4. [Best Practices](#best-practices)
5. [Troubleshooting](#troubleshooting)
6. [FAQ](#faq)

---

## Getting Started

### System Requirements

- **Operating System**: Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Python**: Version 3.9 or higher
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 500MB free space
- **Internet**: Required for job search and AI analysis

### Installation Steps

1. **Install Python** (if not already installed):
   - Download from [python.org](https://www.python.org/downloads/)
   - Ensure "Add Python to PATH" is checked during installation

2. **Clone or download the project**:
   ```bash
   cd /workspace
   ```

3. **Install dependencies**:
   ```bash
   pip install -r job_assistant/requirements.txt
   ```

4. **Install Playwright browsers**:
   ```bash
   playwright install
   ```

5. **Launch the application**:
   ```bash
   python job_assistant/main.py
   ```

---

## First-Time Setup

### Step 1: Configure Your API Key

The application requires a Google Gemini API key for AI-powered job matching.

1. Get your free API key at [Google AI Studio](https://makersuite.google.com/app/apikey)
2. In the application, click **Settings** (⚙️) in the sidebar
3. Enter your API key in the "Gemini API Key" field
4. Click **Save**

**Alternative**: Set environment variable before running:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### Step 2: Upload Your Resume

Your resume is the foundation for all job matching.

1. Click **"Upload CV/Resume"** in the Job Analysis tab
2. Select your PDF or DOCX file
3. Review the parsed information
4. Edit any incorrect fields in the Profile Editor

**Tips for best parsing results**:
- Use a clean, standard resume format
- Avoid complex layouts or graphics
- Include clear section headers (Experience, Education, Skills)
- Save as PDF for best compatibility

### Step 3: Customize Your Profile

After uploading, review and enhance your profile:

1. Click **"My Profile"** (👤) in the sidebar
2. Update any missing information:
   - Add skills not detected automatically
   - Refine experience descriptions
   - Include projects and certifications
3. Click **Save** when done

---

## Core Features

### 1. Job Search

**How to search:**

1. Enter job title or keywords (e.g., "Python Developer")
2. Optionally add location (e.g., "Remote" or "New York")
3. Select job sources:
   - ✅ Indeed (recommended)
   - ⬜ LinkedIn (requires manual copy-paste)
   - ⬜ Glassdoor
4. Choose maximum job age (default: 7 days)
5. Click **"Search Jobs"**

**Understanding search results:**

Each result shows:
- Job title and company name
- Location (or "Remote")
- Posting date
- Source website
- Brief description snippet

### 2. AI Job Analysis

**Analyzing a job:**

1. Click on any job in the search results
2. Review the job details panel
3. Click **"Analyze with AI"**
4. Wait for analysis (typically 5-10 seconds)

**Understanding your match score:**

| Score | Meaning | Recommendation |
|-------|---------|----------------|
| **A** | Excellent (90%+) | Apply immediately! |
| **B** | Strong (75-89%) | Great fit, should apply |
| **C** | Moderate (60-74%) | Good potential, address gaps |
| **D** | Weak (40-59%) | Consider upskilling first |
| **F** | Poor (<40%) | Not a good fit currently |

**Analysis includes:**

- **Matched Skills**: What you have that they want
- **Missing Skills**: Gaps to address
- **Tailored Bullets**: Custom resume points
- **Summary**: AI assessment of your fit

### 3. Resume Generation

**Creating a tailored resume:**

1. After analyzing a job, go to **"Resume Preview"** tab
2. Click **"Generate Tailored Resume"**
3. Review the generated PDF
4. Click **"Download PDF"** to save

**What gets customized:**

- Professional summary aligned with job requirements
- Skills section prioritizing matched keywords
- Experience bullets emphasizing relevant achievements
- Optional: Cover letter draft

### 4. Application Tracking

**Saving jobs to history:**

1. After analyzing a job, click **"Save to History"**
2. Add notes if desired (e.g., "Applied via LinkedIn")
3. View all tracked applications in **"Search History"**

**Tracking features:**

- Filter by match score (A-F)
- Sort by date or company
- Export history to CSV
- View statistics dashboard

---

## Best Practices

### For Better Match Scores

1. **Keep your profile updated**: Regularly add new skills and experiences
2. **Be specific with searches**: "Senior Python Developer Django" vs just "Developer"
3. **Review missing skills**: Use them as learning goals
4. **Target B+ scores**: Don't limit yourself to only A matches

### For Effective Resume Tailoring

1. **Review AI suggestions**: Don't blindly accept all tailored bullets
2. **Maintain honesty**: Only claim skills you actually have
3. **Quantify achievements**: Add numbers where possible
4. **Keep a master resume**: Store all experiences, tailor for each application

### For Cost Management

**Estimated costs per operation:**

| Operation | Approximate Cost |
|-----------|------------------|
| Job Analysis | $0.0005 |
| Resume Generation | $0.0004 |

**Budget tips:**

- Analyze only jobs you're seriously considering
- Batch similar jobs for comparison
- Use free tier wisely (60 requests/minute limit)

**Monthly estimate for typical usage:**
- 50 job analyses: ~$0.025
- 20 resume generations: ~$0.008
- **Total: ~$0.03/month**

### For Job Search Strategy

1. **Quality over quantity**: Focus on high-match positions
2. **Track everything**: Log all applications for follow-up
3. **Iterate quickly**: Use feedback from rejections to improve profile
4. **Set daily goals**: e.g., "Analyze 5 jobs, apply to 2"

---

## Troubleshooting

### Common Issues

**Problem**: "Gemini API key not configured"

**Solutions**:
- Verify API key is correctly entered in Settings
- Check for extra spaces in the key
- Ensure API key is active at [Google AI Studio](https://makersuite.google.com/)
- Try setting environment variable instead

---

**Problem**: "Failed to parse resume"

**Solutions**:
- Ensure file is PDF or DOCX format (not DOC)
- Check file isn't password-protected
- Try converting to PDF if using DOCX
- Simplify formatting (remove tables, columns)
- Manually enter profile data instead

---

**Problem**: "No jobs found"

**Solutions**:
- Verify internet connection
- Try broader search terms
- Remove location filter
- Try different job sources
- Check if job board is blocking automated access

---

**Problem**: "Playwright browser error"

**Solutions**:
```bash
# Reinstall Playwright browsers
playwright install --force

# For Linux, install dependencies
playwright install --with-deps chromium
```

---

**Problem**: Application runs slowly

**Solutions**:
- Close other applications to free RAM
- Reduce number of search results (max 15 recommended)
- Use shorter job descriptions for analysis
- Check network connection speed

---

## FAQ

### General Questions

**Q: Is this application free to use?**

A: The application itself is free (MIT License). However, it uses Google Gemini API which has usage limits on the free tier. Typical job search usage costs less than $0.10/month.

**Q: Is my data secure?**

A: Yes. All data is stored locally on your computer:
- Resume/profile: `data/user_profile.json`
- Application history: `data/job_history.db`
- Generated PDFs: `data/resumes/`

No data is sent to our servers (there are none). Only job descriptions and your profile are sent to Google's API for analysis.

**Q: Can I use this without an API key?**

A: You can browse jobs and manage your profile without an API key, but AI features (matching, scoring, tailoring) require the key.

**Q: Does this work with LinkedIn?**

A: LinkedIn requires login for most job details, which we don't support for ethical reasons. You can:
1. Find jobs on LinkedIn
2. Copy the job description manually
3. Paste into our analyzer

**Q: How accurate are the match scores?**

A: The AI provides informed estimates based on keyword matching and semantic analysis. Treat scores as guidance, not absolute truth. Always review the detailed analysis.

### Technical Questions

**Q: Can I run this on a server without GUI?**

A: The core modules work headlessly, but the main interface requires a display. For server use, you'd need to create a web interface or use the modules programmatically.

**Q: Can I customize the AI prompts?**

A: Yes! Edit `core/ai_engine.py`, specifically the `_build_prompt()` method. Be careful to maintain the JSON output format.

**Q: How do I add a new job source?**

A: See the Development section in README.md. You'll need to:
1. Add URL template
2. Implement parser methods
3. Test thoroughly

**Q: Where are logs stored?**

A: Logs are printed to console by default. To save to file, modify `utils/logger.py`.

### Academic Use

**Q: Can I use this for my final year project?**

A: Absolutely! This project is designed as a FYP template. Make sure to:
- Understand and cite the code
- Extend with your own features
- Document your contributions
- Follow your institution's academic integrity policies

**Q: How do I cite this project?**

A: Use the BibTeX entry in README.md, customizing with your details if you've modified it.

---

## Support

For additional help:

1. Check this guide and README.md
2. Review inline code documentation
3. Open an issue on GitHub
4. Consult online resources for specific technologies (CustomTkinter, Playwright, etc.)

---

**Happy Job Hunting! 🎯**
