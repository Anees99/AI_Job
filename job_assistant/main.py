"""
AI-Driven Dynamic Job Application & Career Assistant
Main GUI Application using CustomTkinter

Workflow:
1. User uploads their CV/Resume (PDF/DOCX)
2. System parses the resume to extract skills/experience
3. User enters job search criteria (title, location)
4. System searches multiple job boards for recent postings
5. AI analyzes each job against the user's profile
6. Results shown with match scores (A-F)
7. Generate tailored resumes for selected jobs
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from utils.logger import setup_logger
from utils.config import Config
from core.resume_parser import ResumeParser
from core.job_search import JobSearchAggregator
from core.scraper import JobScraper
from core.ai_engine import AIEngine, JobMatchResult
from core.database import DatabaseManager
from core.pdf_generator import PDFGenerator

# Initialize logger
logger = setup_logger(__name__)

# Configure CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class JobAssistantApp(ctk.CTk):
    """Main application window for the Job Application Assistant."""

    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("AI Job Application Assistant")
        self.geometry("1400x900")
        self.minsize(1200, 800)

        # State variables
        self.resume_parser: Optional[ResumeParser] = None
        self.job_searcher: Optional[JobSearchAggregator] = None
        self.scraper: Optional[JobScraper] = None
        self.ai_engine: Optional[AIEngine] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.pdf_generator: Optional[PDFGenerator] = None
        
        self.user_profile: dict = {}
        self.resume_file_path: str = ""
        self.search_results: List[Dict[str, Any]] = []
        self.analysis_results: Dict[str, JobMatchResult] = {}
        self.is_processing = False

        # Initialize core components
        self._initialize_components()

        # Load or parse user profile
        self._load_or_create_profile()

        # Build UI
        self._create_ui()

        logger.info("Application started successfully")

    def _initialize_components(self):
        """Initialize all core components."""
        try:
            self.db_manager = DatabaseManager()
            logger.info("Database manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            messagebox.showerror(
                "Database Error",
                f"Failed to initialize database:\n{str(e)}"
            )

        try:
            self.resume_parser = ResumeParser()
            logger.info("Resume parser initialized")
        except Exception as e:
            logger.error(f"Failed to initialize resume parser: {e}")

        try:
            self.job_searcher = JobSearchAggregator(max_results=15)
            logger.info("Job searcher initialized")
        except Exception as e:
            logger.error(f"Failed to initialize job searcher: {e}")

        try:
            self.scraper = JobScraper()
            logger.info("Scraper initialized")
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {e}")

        try:
            self.pdf_generator = PDFGenerator()
            logger.info("PDF generator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PDF generator: {e}")

    def _load_or_create_profile(self):
        """Load user profile from uploaded resume or existing file."""
        # First try to load from existing JSON profile
        profile_path = Config.USER_PROFILE_PATH
        
        if profile_path.exists():
            try:
                with open(profile_path, 'r') as f:
                    self.user_profile = json.load(f)
                logger.info(f"Loaded user profile from {profile_path}")
                return
            except Exception as e:
                logger.warning(f"Failed to load profile: {e}")
        
        # If no profile exists, use default template
        logger.info("No profile found, using default template")
        self.user_profile = Config.get_default_profile()
    
    def _parse_uploaded_resume(self, file_path: str):
        """Parse an uploaded resume file and update user profile."""
        if not self.resume_parser:
            messagebox.showerror("Error", "Resume parser not initialized")
            return False
        
        try:
            logger.info(f"Parsing resume: {file_path}")
            self.status_var.set(f"Parsing resume: {Path(file_path).name}...")
            self.update()
            
            # Parse the resume
            parsed_data = self.resume_parser.parse_file(file_path)
            
            # Update user profile with parsed data
            contact = parsed_data.get('contact', {})
            self.user_profile['personal_info'] = {
                'name': contact.get('name', ''),
                'email': contact.get('email', ''),
                'phone': contact.get('phone', ''),
                'location': contact.get('location', ''),
                'linkedin': contact.get('linkedin', ''),
                'website': contact.get('website', '')
            }
            
            # Merge skills
            existing_skills = set(self.user_profile.get('skills', []))
            new_skills = set(parsed_data.get('skills', []))
            self.user_profile['skills'] = list(existing_skills | new_skills)
            
            # Add experience if not present
            if 'experience' not in self.user_profile and parsed_data.get('experience'):
                self.user_profile['experience'] = parsed_data['experience']
            
            # Add education if not present
            if 'education' not in self.user_profile and parsed_data.get('education'):
                self.user_profile['education'] = parsed_data['education']
            
            # Save updated profile
            self._save_user_profile()
            
            self.resume_file_path = file_path
            logger.info(f"Successfully parsed resume and updated profile")
            self.status_var.set(f"✓ Resume loaded: {contact.get('name', 'Unknown')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to parse resume: {e}")
            messagebox.showerror("Parse Error", f"Failed to parse resume:\n{str(e)}")
            self.status_var.set("✗ Failed to parse resume")
            return False
    
    def _save_user_profile(self):
        """Save current user profile to file."""
        try:
            with open(Config.USER_PROFILE_PATH, 'w') as f:
                json.dump(self.user_profile, f, indent=2)
            logger.info(f"Saved user profile to {Config.USER_PROFILE_PATH}")
        except Exception as e:
            logger.error(f"Failed to save profile: {e}")
            messagebox.showwarning("Warning", f"Could not save profile: {str(e)}")

    def _create_ui(self):
        """Build the main user interface."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create sidebar
        self._create_sidebar()

        # Create main content area
        self._create_main_area()

        # Create status bar
        self._create_status_bar()

    def _create_sidebar(self):
        """Create the left sidebar with navigation and controls."""
        sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_rowconfigure(4, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            sidebar,
            text="🎯 Job Assistant",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        # Profile button
        self.btn_profile = ctk.CTkButton(
            sidebar,
            text="👤 My Profile",
            command=self._open_profile_editor,
            height=40
        )
        self.btn_profile.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # History button
        self.btn_history = ctk.CTkButton(
            sidebar,
            text="📊 Search History",
            command=self._show_history,
            height=40
        )
        self.btn_history.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Settings button (for API key)
        self.btn_settings = ctk.CTkButton(
            sidebar,
            text="⚙️ Settings",
            command=self._open_settings,
            height=40
        )
        self.btn_settings.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Version label
        version_label = ctk.CTkLabel(
            sidebar,
            text="v1.0.0",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        version_label.grid(row=5, column=0, padx=20, pady=20)

    def _create_main_area(self):
        """Create the main content area with tabs."""
        # Main container
        main_frame = ctk.CTkFrame(self, corner_radius=0)
        main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkLabel(
            main_frame,
            text="Analyze Job Postings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.grid(row=0, column=0, padx=30, pady=(30, 20), sticky="w")

        # Create tabview
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.grid(row=1, column=0, padx=30, pady=(0, 30), sticky="nsew")

        # Add tabs
        self.tab_analyze = self.tabview.add("🔍 Job Analysis")
        self.tab_results = self.tabview.add("📋 Results")
        self.tab_resume = self.tabview.add("📄 Resume Preview")

        # Build tab contents
        self._build_analyze_tab()
        self._build_results_tab()
        self._build_resume_tab()

    def _build_analyze_tab(self):
        """Build the job analysis tab with resume upload and job search."""
        self.tab_analyze.grid_columnconfigure(0, weight=1)
        self.tab_analyze.grid_rowconfigure(4, weight=1)

        # === Resume Upload Section ===
        resume_frame = ctk.CTkFrame(self.tab_analyze, fg_color="transparent")
        resume_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        resume_frame.grid_columnconfigure(1, weight=1)

        resume_label = ctk.CTkLabel(
            resume_frame, 
            text="📄 Your Resume:",
            font=ctk.CTkFont(weight="bold")
        )
        resume_label.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.lbl_resume_file = ctk.CTkLabel(
            resume_frame,
            text="No resume uploaded",
            text_color="gray"
        )
        self.lbl_resume_file.grid(row=0, column=1, sticky="w")

        self.btn_upload_resume = ctk.CTkButton(
            resume_frame,
            text="Upload CV/Resume",
            command=self._upload_resume,
            width=150
        )
        self.btn_upload_resume.grid(row=0, column=2, padx=(10, 0))

        # === Job Search Section ===
        search_frame = ctk.CTkFrame(self.tab_analyze, fg_color="transparent")
        search_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        search_frame.grid_columnconfigure((1, 2), weight=1)

        query_label = ctk.CTkLabel(search_frame, text="🔍 Job Title/Skills:")
        query_label.grid(row=0, column=0, padx=(0, 10), sticky="w", pady=5)

        self.entry_job_query = ctk.CTkEntry(
            search_frame, 
            placeholder_text="e.g., Python Developer, Data Scientist",
            width=300
        )
        self.entry_job_query.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        location_label = ctk.CTkLabel(search_frame, text="📍 Location:")
        location_label.grid(row=0, column=2, padx=(10, 5), sticky="w", pady=5)

        self.entry_location = ctk.CTkEntry(
            search_frame,
            placeholder_text="e.g., San Francisco, CA (optional)",
            width=250
        )
        self.entry_location.grid(row=0, column=3, sticky="ew", padx=5, pady=5)

        self.btn_search_jobs = ctk.CTkButton(
            search_frame,
            text="Search Jobs",
            command=self._start_job_search,
            width=120
        )
        self.btn_search_jobs.grid(row=0, column=4, padx=(10, 0), pady=5)

        # Search options
        options_frame = ctk.CTkFrame(self.tab_analyze, fg_color="transparent")
        options_frame.grid(row=2, column=0, padx=20, pady=5, sticky="w")

        ctk.CTkLabel(options_frame, text="Sources:").grid(row=0, column=0, padx=(0, 5))
        
        self.var_indeed = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(options_frame, text="Indeed", variable=self.var_indeed).grid(row=0, column=1, padx=5)
        
        self.var_linkedin = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(options_frame, text="LinkedIn", variable=self.var_linkedin).grid(row=0, column=2, padx=5)
        
        ctk.CTkLabel(options_frame, text="| Max Age:").grid(row=0, column=3, padx=(15, 5))
        
        self.var_days_old = ctk.StringVar(value="7")
        days_combo = ctk.CTkOptionMenu(
            options_frame,
            values=["3", "7", "14", "30"],
            variable=self.var_days_old,
            width=60
        )
        days_combo.grid(row=0, column=4, padx=5)
        ctk.CTkLabel(options_frame, text="days").grid(row=0, column=5, padx=0)

        # Results header
        results_header = ctk.CTkLabel(
            self.tab_analyze,
            text="Recent Job Postings:",
            font=ctk.CTkFont(weight="bold"),
            anchor="w"
        )
        results_header.grid(row=3, column=0, padx=20, pady=(15, 5), sticky="w")

        # Job results list (scrollable)
        self.job_results_frame = ctk.CTkScrollableFrame(
            self.tab_analyze,
            height=250
        )
        self.job_results_frame.grid(row=4, column=0, padx=20, pady=(0, 15), sticky="nsew")

        # Progress indicator
        self.progress_bar = ctk.CTkProgressBar(self.tab_analyze)
        self.progress_bar.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            self.tab_analyze,
            text="",
            text_color="gray"
        )
        self.status_label.grid(row=6, column=0, padx=20, pady=(0, 20))

    def _build_results_tab(self):
        """Build the results display tab."""
        self.tab_results.grid_columnconfigure(0, weight=1)
        self.tab_results.grid_rowconfigure(0, weight=1)

        # Results container
        results_frame = ctk.CTkScrollableFrame(self.tab_results)
        results_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        results_frame.grid_columnconfigure(1, weight=1)

        # Score display
        score_frame = ctk.CTkFrame(results_frame)
        score_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        score_frame.grid_columnconfigure(1, weight=1)

        score_label = ctk.CTkLabel(
            score_frame,
            text="Match Score:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        score_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

        self.lbl_score = ctk.CTkLabel(
            score_frame,
            text="--",
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color="#3498db"
        )
        self.lbl_score.grid(row=0, column=1, pady=20)

        self.lbl_confidence = ctk.CTkLabel(
            score_frame,
            text="Confidence: --%",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.lbl_confidence.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="e")

        # Job info
        info_frame = ctk.CTkFrame(results_frame)
        info_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        info_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(info_frame, text="Company:").grid(row=0, column=0, padx=20, pady=10, sticky="w")
        self.lbl_company = ctk.CTkLabel(info_frame, text="--")
        self.lbl_company.grid(row=0, column=1, pady=10, sticky="w")

        ctk.CTkLabel(info_frame, text="Role:").grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.lbl_role = ctk.CTkLabel(info_frame, text="--")
        self.lbl_role.grid(row=1, column=1, pady=10, sticky="w")

        # Summary
        summary_frame = ctk.CTkFrame(results_frame)
        summary_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        summary_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            summary_frame,
            text="AI Summary:",
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=20, pady=10, sticky="w")

        self.lbl_summary = ctk.CTkLabel(
            summary_frame,
            text="--",
            wraplength=800,
            justify="left"
        )
        self.lbl_summary.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        # Matched skills
        skills_frame = ctk.CTkFrame(results_frame)
        skills_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        skills_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            skills_frame,
            text="✅ Matched Skills",
            font=ctk.CTkFont(weight="bold"),
            text_color="green"
        ).grid(row=0, column=0, padx=20, pady=10)

        ctk.CTkLabel(
            skills_frame,
            text="❌ Missing Skills",
            font=ctk.CTkFont(weight="bold"),
            text_color="red"
        ).grid(row=0, column=1, padx=20, pady=10)

        self.lbl_matched = ctk.CTkLabel(skills_frame, text="--", justify="left")
        self.lbl_matched.grid(row=1, column=0, padx=20, pady=10, sticky="nw")

        self.lbl_missing = ctk.CTkLabel(skills_frame, text="--", justify="left")
        self.lbl_missing.grid(row=1, column=1, padx=20, pady=10, sticky="nw")

        # Tailored bullets
        bullets_frame = ctk.CTkFrame(results_frame)
        bullets_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        bullets_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            bullets_frame,
            text="📝 Tailored Resume Bullets:",
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=20, pady=10, sticky="w")

        self.txt_bullets = ctk.CTkTextbox(
            bullets_frame,
            height=150,
            state="disabled"
        )
        self.txt_bullets.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Save to history button
        self.btn_save = ctk.CTkButton(
            results_frame,
            text="💾 Save to History",
            command=self._save_to_history,
            height=40,
            state="disabled"
        )
        self.btn_save.grid(row=5, column=0, padx=20, pady=20)

    def _build_resume_tab(self):
        """Build the resume preview tab."""
        self.tab_resume.grid_columnconfigure(0, weight=1)
        self.tab_resume.grid_rowconfigure(1, weight=1)

        info_label = ctk.CTkLabel(
            self.tab_resume,
            text="Resume Preview & Generation",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        info_label.grid(row=0, column=0, padx=20, pady=20)

        self.txt_resume_preview = ctk.CTkTextbox(
            self.tab_resume,
            state="disabled"
        )
        self.txt_resume_preview.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        btn_frame = ctk.CTkFrame(self.tab_resume, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=20, pady=20)

        self.btn_generate_pdf = ctk.CTkButton(
            btn_frame,
            text="📄 Generate PDF Resume",
            command=self._generate_pdf,
            state="disabled"
        )
        self.btn_generate_pdf.pack(side="left", padx=10)

        self.btn_copy_bullets = ctk.CTkButton(
            btn_frame,
            text="📋 Copy Tailored Bullets",
            command=self._copy_bullets
        )
        self.btn_copy_bullets.pack(side="left", padx=10)

    def _create_status_bar(self):
        """Create the bottom status bar."""
        status_bar = ctk.CTkFrame(self, height=30, corner_radius=0)
        status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        status_bar.grid_columnconfigure(1, weight=1)

        self.status_left = ctk.CTkLabel(
            status_bar,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_left.grid(row=0, column=0, padx=20, sticky="w")

        self.status_right = ctk.CTkLabel(
            status_bar,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_right.grid(row=0, column=1, padx=20, sticky="e")

    def _update_status(self, message: str, right_text: str = ""):
        """Update status bar text."""
        self.status_left.configure(text=message)
        self.status_right.configure(text=right_text)

    def _open_profile_editor(self):
        """Open profile editor dialog."""
        profile_window = ctk.CTkToplevel(self)
        profile_window.title("Edit Profile")
        profile_window.geometry("800x600")
        profile_window.transient(self)

        # Make modal
        profile_window.grab_set()

        # Content
        label = ctk.CTkLabel(
            profile_window,
            text="Edit Your Profile (JSON Format)",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        label.pack(padx=20, pady=20)

        txt_editor = ctk.CTkTextbox(profile_window)
        txt_editor.pack(padx=20, pady=10, expand=True, fill="both")
        txt_editor.insert("0.0", json.dumps(self.user_profile, indent=2))

        def save_profile():
            try:
                content = txt_editor.get("0.0", "end").strip()
                self.user_profile = json.loads(content)
                self._save_user_profile()
                messagebox.showinfo("Success", "Profile saved successfully!")
                profile_window.destroy()
            except json.JSONDecodeError as e:
                messagebox.showerror("Error", f"Invalid JSON: {str(e)}")

        btn_frame = ctk.CTkFrame(profile_window, fg_color="transparent")
        btn_frame.pack(padx=20, pady=20)

        ctk.CTkButton(btn_frame, text="Save", command=save_profile).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", command=profile_window.destroy).pack(side="left", padx=10)

    def _show_history(self):
        """Show job search history."""
        if not self.db_manager:
            messagebox.showerror("Error", "Database not initialized")
            return

        history_window = ctk.CTkToplevel(self)
        history_window.title("Job Search History")
        history_window.geometry("900x600")
        history_window.transient(self)
        history_window.grab_set()

        # Get statistics
        stats = self.db_manager.get_statistics()

        # Stats frame
        stats_frame = ctk.CTkFrame(history_window)
        stats_frame.pack(padx=20, pady=20, fill="x")

        ctk.CTkLabel(
            stats_frame,
            text=f"Total: {stats.get('total', 0)} | "
                 f"A: {stats.get('a_count', 0)} | "
                 f"B: {stats.get('b_count', 0)} | "
                 f"C: {stats.get('c_count', 0)} | "
                 f"D: {stats.get('d_count', 0)} | "
                 f"F: {stats.get('f_count', 0)}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=10)

        # Scrollable list
        scroll_frame = ctk.CTkScrollableFrame(history_window)
        scroll_frame.pack(padx=20, pady=10, expand=True, fill="both")

        jobs = self.db_manager.get_all_jobs(limit=50)

        if not jobs:
            ctk.CTkLabel(scroll_frame, text="No job history yet.").pack(pady=20)
        else:
            for job in jobs:
                job_frame = ctk.CTkFrame(scroll_frame)
                job_frame.pack(fill="x", padx=10, pady=5)

                score_color = {
                    "A": "#2ecc71", "B": "#3498db", "C": "#f39c12",
                    "D": "#e67e22", "F": "#e74c3c"
                }.get(job["match_score"], "gray")

                ctk.CTkLabel(
                    job_frame,
                    text=job["match_score"],
                    font=ctk.CTkFont(size=20, weight="bold"),
                    text_color=score_color,
                    width=40
                ).pack(side="left", padx=10, pady=10)

                info_frame = ctk.CTkFrame(job_frame, fg_color="transparent")
                info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=10)

                ctk.CTkLabel(
                    info_frame,
                    text=f"{job['role']} at {job['company']}",
                    font=ctk.CTkFont(weight="bold"),
                    anchor="w"
                ).pack(fill="x")

                ctk.CTkLabel(
                    info_frame,
                    text=f"{job['date']} | {job.get('summary', '')[:100]}",
                    text_color="gray",
                    anchor="w"
                ).pack(fill="x")

    def _open_settings(self):
        """Open settings dialog."""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("500x300")
        settings_window.transient(self)
        settings_window.grab_set()

        ctk.CTkLabel(
            settings_window,
            text="Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(padx=20, pady=20)

        # API Key
        api_frame = ctk.CTkFrame(settings_window)
        api_frame.pack(padx=20, pady=10, fill="x")

        ctk.CTkLabel(api_frame, text="Gemini API Key:").pack(padx=20, pady=10, anchor="w")

        api_entry = ctk.CTkEntry(api_frame, width=400)
        api_entry.pack(padx=20, pady=10)
        api_entry.insert(0, Config.GEMINI_API_KEY or "")

        def save_settings():
            api_key = api_entry.get().strip()
            if api_key:
                # Update environment variable for this session
                import os
                os.environ["GEMINI_API_KEY"] = api_key
                Config.GEMINI_API_KEY = api_key

                # Reinitialize AI engine
                try:
                    self.ai_engine = AIEngine(api_key=api_key)
                    messagebox.showinfo("Success", "API key saved! AI engine initialized.")
                    settings_window.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to initialize AI engine: {str(e)}")
            else:
                messagebox.showwarning("Warning", "API key cannot be empty")

        ctk.CTkButton(settings_window, text="Save", command=save_settings).pack(pady=20)

    def _start_scraping(self):
        """Start scraping job description in background thread."""
        url = self.url_entry.get().strip()

        if not url:
            messagebox.showwarning("Warning", "Please enter a URL")
            return

        if self.is_processing:
            messagebox.showinfo("Info", "Already processing a request")
            return

        self.is_processing = True
        self.btn_scrape.configure(state="disabled")
        self.btn_analyze.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(text="Scraping job description...")
        self._update_status("Scraping...", url)

        # Run in background thread
        thread = threading.Thread(target=self._scrape_job, args=(url,), daemon=True)
        thread.start()

    def _scrape_job(self, url: str):
        """Scrape job description (runs in background thread)."""
        try:
            if not self.scraper:
                self.scraper = JobScraper()

            content = self.scraper.scrape(url)

            # Update UI in main thread
            self.after(0, lambda: self._on_scrape_complete(content, url))

        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            self.after(0, lambda: self._on_scrape_error(str(e)))

    def _on_scrape_complete(self, content: str, url: str):
        """Handle successful scrape completion."""
        self.is_processing = False
        self.btn_scrape.configure(state="normal")
        self.progress_bar.set(1.0)
        self.status_label.configure(text=f"Extracted {len(content)} characters")
        self._update_status("Scraping complete", f"{len(content)} chars")

        # Display content
        self.txt_content.configure(state="normal")
        self.txt_content.delete("0.0", "end")
        self.txt_content.insert("0.0", content)
        self.txt_content.configure(state="disabled")

        # Store for analysis
        self.current_scraped_content = content
        self.current_url = url

        # Enable analyze button
        self.btn_analyze.configure(state="normal")

        # Check if AI engine is initialized
        if not self.ai_engine and Config.validate_api_key():
            try:
                self.ai_engine = AIEngine()
            except Exception as e:
                logger.warning(f"Could not initialize AI engine: {e}")

        if not self.ai_engine:
            self.btn_analyze.configure(state="disabled")
            messagebox.showinfo(
                "AI Engine Not Ready",
                "Please configure your Gemini API key in Settings first."
            )

    def _on_scrape_error(self, error_msg: str):
        """Handle scrape error."""
        self.is_processing = False
        self.btn_scrape.configure(state="normal")
        self.progress_bar.set(0)
        self.status_label.configure(text="Scraping failed")
        self._update_status("Error", error_msg)

        messagebox.showerror("Scraping Error", f"Failed to extract job description:\n{error_msg}")

    def _start_analysis(self):
        """Start AI analysis in background thread."""
        if not hasattr(self, 'current_scraped_content') or not self.current_scraped_content:
            messagebox.showwarning("Warning", "No job description to analyze")
            return

        if self.is_processing:
            return

        self.is_processing = True
        self.btn_analyze.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(text="Analyzing with AI...")
        self._update_status("Analyzing...", "This may take a few seconds")

        # Run in background thread
        thread = threading.Thread(target=self._analyze_job, daemon=True)
        thread.start()

    def _analyze_job(self):
        """Run AI analysis (background thread)."""
        try:
            if not self.ai_engine:
                self.ai_engine = AIEngine()

            result = self.ai_engine.analyze_job(
                self.current_scraped_content,
                self.user_profile
            )

            self.after(0, lambda: self._on_analysis_complete(result))

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.after(0, lambda: self._on_analysis_error(str(e)))

    def _on_analysis_complete(self, result: JobMatchResult):
        """Handle successful analysis completion."""
        self.is_processing = False
        self.btn_analyze.configure(state="normal")
        self.progress_bar.set(1.0)
        self.status_label.configure(text="Analysis complete!")
        self._update_status("Ready", f"Match Score: {result.match_score}")

        # Store result
        self.current_result = result

        # Update results tab
        self._display_results(result)

        # Switch to results tab
        self.tabview.set("📋 Results")

    def _on_analysis_error(self, error_msg: str):
        """Handle analysis error."""
        self.is_processing = False
        self.btn_analyze.configure(state="normal")
        self.progress_bar.set(0)
        self.status_label.configure(text="Analysis failed")
        self._update_status("Error", error_msg)

        messagebox.showerror("Analysis Error", f"AI analysis failed:\n{error_msg}")

    def _display_results(self, result: JobMatchResult):
        """Display analysis results in the results tab."""
        # Score
        self.lbl_score.configure(text=result.match_score)

        # Color code the score
        score_colors = {
            "A": "#2ecc71", "B": "#3498db", "C": "#f39c12",
            "D": "#e67e22", "F": "#e74c3c"
        }
        self.lbl_score.configure(text_color=score_colors.get(result.match_score, "white"))

        # Confidence
        confidence_pct = int(result.confidence * 100)
        self.lbl_confidence.configure(text=f"Confidence: {confidence_pct}%")

        # Job info
        self.lbl_company.configure(text=result.company_name)
        self.lbl_role.configure(text=result.job_title)

        # Summary
        self.lbl_summary.configure(text=result.summary)

        # Skills
        matched_text = "\n• ".join(result.matched_skills) if result.matched_skills else "--"
        missing_text = "\n• ".join(result.missing_skills) if result.missing_skills else "--"
        self.lbl_matched.configure(text="• " + matched_text if matched_text != "--" else "--")
        self.lbl_missing.configure(text="• " + missing_text if missing_text != "--" else "--")

        # Tailored bullets
        self.txt_bullets.configure(state="normal")
        self.txt_bullets.delete("0.0", "end")
        bullets_text = "\n".join([f"• {bullet}" for bullet in result.tailored_bullets])
        self.txt_bullets.insert("0.0", bullets_text)
        self.txt_bullets.configure(state="disabled")

        # Enable save button
        self.btn_save.configure(state="normal")

        # Update resume preview tab
        self._update_resume_preview(result)

    def _update_resume_preview(self, result: JobMatchResult):
        """Update resume preview with tailored content."""
        preview_lines = [
            "=" * 60,
            f"TAILORED RESUME FOR: {result.job_title}",
            f"COMPANY: {result.company_name}",
            "=" * 60,
            "",
            "RECOMMENDED BULLET POINTS:",
            "-" * 40
        ]

        for i, bullet in enumerate(result.tailored_bullets, 1):
            preview_lines.append(f"{i}. {bullet}")

        preview_lines.extend([
            "",
            "-" * 40,
            "MATCHED SKILLS TO HIGHLIGHT:",
        ])
        for skill in result.matched_skills[:5]:
            preview_lines.append(f"  • {skill}")

        preview_lines.extend([
            "",
            "SKILLS TO DEVELOP:",
        ])
        for skill in result.missing_skills[:5]:
            preview_lines.append(f"  • {skill}")

        preview_text = "\n".join(preview_lines)

        self.txt_resume_preview.configure(state="normal")
        self.txt_resume_preview.delete("0.0", "end")
        self.txt_resume_preview.insert("0.0", preview_text)
        self.txt_resume_preview.configure(state="disabled")

        # Enable PDF generation
        self.btn_generate_pdf.configure(state="normal")

    def _save_to_history(self):
        """Save current analysis to database."""
        if not self.current_result or not self.db_manager:
            return

        try:
            job_id = self.db_manager.insert_job(
                company=self.current_result.company_name,
                role=self.current_result.job_title,
                match_score=self.current_result.match_score,
                url=getattr(self, 'current_url', None),
                confidence=self.current_result.confidence,
                summary=self.current_result.summary
            )

            messagebox.showinfo(
                "Success",
                f"Job saved to history!\nRecord ID: {job_id}"
            )

            self.btn_save.configure(state="disabled")
            self._update_status("Saved", f"Record ID: {job_id}")

        except Exception as e:
            logger.error(f"Failed to save to history: {e}")
            messagebox.showerror("Error", f"Could not save to history:\n{str(e)}")

    def _upload_resume(self):
        """Open file dialog to upload resume/CV."""
        if not self.resume_parser:
            messagebox.showerror("Error", "Resume parser not initialized")
            return
        
        filetypes = [
            ("PDF files", "*.pdf"),
            ("Word documents", "*.docx *.doc"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Select Your Resume/CV",
            filetypes=filetypes
        )
        
        if file_path:
            success = self._parse_uploaded_resume(file_path)
            if success:
                self.lbl_resume_file.configure(
                    text=f"✓ {Path(file_path).name}",
                    text_color="#2ecc71"
                )
                self.status_var.set(f"Resume loaded - Ready to search jobs!")
    
    def _start_job_search(self):
        """Start searching for jobs in background thread."""
        if not self.resume_file_path and not self.user_profile.get('skills'):
            messagebox.showwarning(
                "No Resume",
                "Please upload your resume first so we can find matching jobs!"
            )
            return
        
        query = self.entry_job_query.get().strip()
        if not query:
            messagebox.showwarning(
                "Missing Query",
                "Please enter a job title or skills to search for."
            )
            return
        
        if self.is_processing:
            return
        
        # Get search parameters
        location = self.entry_location.get().strip()
        days_old = int(self.var_days_old.get())
        
        sources = []
        if self.var_indeed.get():
            sources.append('indeed')
        if self.var_linkedin.get():
            sources.append('linkedin')
        
        if not sources:
            sources = ['indeed']  # Default to Indeed
        
        # Start background search
        self.is_processing = True
        self.progress_bar.set(0)
        self.btn_search_jobs.configure(state="disabled")
        self.status_var.set(f"Searching for '{query}' jobs...")
        
        # Clear previous results
        for widget in self.job_results_frame.winfo_children():
            widget.destroy()
        
        search_thread = threading.Thread(
            target=self._search_jobs_thread,
            args=(query, location, sources, days_old),
            daemon=True
        )
        search_thread.start()
    
    def _search_jobs_thread(self, query: str, location: str, sources: List[str], days_old: int):
        """Background thread for job searching."""
        try:
            if not self.job_searcher:
                raise RuntimeError("Job searcher not initialized")
            
            # Perform search
            jobs = self.job_searcher.search_jobs(
                query=query,
                location=location,
                sources=sources,
                days_old=days_old
            )
            
            self.search_results = jobs
            
            # Update UI on main thread
            self.after(0, lambda: self._on_search_complete(jobs))
            
        except Exception as e:
            logger.error(f"Job search failed: {e}")
            self.after(0, lambda: self._on_search_error(str(e)))
    
    def _on_search_complete(self, jobs: List[Dict[str, Any]]):
        """Handle successful job search completion."""
        self.is_processing = False
        self.btn_search_jobs.configure(state="normal")
        self.progress_bar.set(1)
        
        if not jobs:
            self.status_var.set("⚠ No jobs found. Try different keywords or expand search.")
            messagebox.showinfo(
                "No Results",
                "No jobs found matching your criteria.\n\n"
                "Try:\n"
                "- Using broader keywords\n"
                "- Expanding the date range\n"
                "- Removing location filter"
            )
            return
        
        # Display job results
        self._display_job_results(jobs)
        
        self.status_var.set(f"✓ Found {len(jobs)} jobs! Click 'Analyze Match' on any job.")
        logger.info(f"Search complete: {len(jobs)} jobs found")
    
    def _on_search_error(self, error_msg: str):
        """Handle job search error."""
        self.is_processing = False
        self.btn_search_jobs.configure(state="normal")
        self.progress_bar.set(0)
        self.status_var.set("✗ Search failed")
        
        messagebox.showerror(
            "Search Error",
            f"Failed to search for jobs:\n{error_msg}"
        )
    
    def _display_job_results(self, jobs: List[Dict[str, Any]]):
        """Display job search results in scrollable frame."""
        # Clear existing
        for widget in self.job_results_frame.winfo_children():
            widget.destroy()
        
        for idx, job in enumerate(jobs):
            # Create job card frame
            card = ctk.CTkFrame(self.job_results_frame, corner_radius=8)
            card.pack(fill="x", padx=5, pady=5)
            
            # Title and company
            title_frame = ctk.CTkFrame(card, fg_color="transparent")
            title_frame.pack(fill="x", padx=15, pady=(15, 5))
            
            title_label = ctk.CTkLabel(
                title_frame,
                text=job.get('title', 'Unknown Position'),
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            )
            title_label.pack(side="left")
            
            # Source badge
            source = job.get('source', 'unknown')
            source_colors = {
                'indeed': '#2166ac',
                'linkedin': '#0a66c2',
                'glassdoor': '#0caa4b',
                'google': '#4285f4'
            }
            source_color = source_colors.get(source, '#666')
            
            source_badge = ctk.CTkLabel(
                title_frame,
                text=source.upper(),
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=source_color,
                bg_color=source_color + "20"  # Add transparency
            )
            source_badge.pack(side="right")
            
            # Company and location
            info_label = ctk.CTkLabel(
                card,
                text=f"{job.get('company', 'Unknown Company')} • {job.get('location', 'Remote/Unspecified')}",
                text_color="gray",
                anchor="w"
            )
            info_label.pack(padx=15, pady=(0, 5))
            
            # Posted date
            posted = job.get('posted_days_ago', 999)
            if posted < 999:
                if posted == 0:
                    date_text = "Posted today"
                elif posted == 1:
                    date_text = "Posted yesterday"
                else:
                    date_text = f"Posted {posted} days ago"
                
                date_label = ctk.CTkLabel(
                    card,
                    text=date_text,
                    text_color="gray",
                    font=ctk.CTkFont(size=11),
                    anchor="w"
                )
                date_label.pack(padx=15, pady=(0, 10))
            
            # Analyze button
            analyze_btn = ctk.CTkButton(
                card,
                text="🎯 Analyze Match",
                command=lambda j=job: self._analyze_single_job(j),
                width=120,
                height=32
            )
            analyze_btn.pack(padx=15, pady=(0, 15))
            
            # Separator line (except last)
            if idx < len(jobs) - 1:
                separator = ctk.CTkFrame(card, height=1, fg_color="#444")
                separator.pack(fill="x", padx=15, pady=(0, 5))

    def _analyze_single_job(self, job: Dict[str, Any]):
        """Analyze a single job posting against user profile."""
        if not self.scraper or not self.ai_engine:
            messagebox.showerror("Error", "Required components not initialized")
            return
        
        url = job.get('url', '')
        if not url:
            messagebox.showerror("Error", "Job has no URL")
            return
        
        if self.is_processing:
            return
        
        self.is_processing = True
        self.progress_bar.set(0)
        self.status_var.set(f"Scraping job description from {job.get('company', 'company')}...")
        
        # Disable all analyze buttons temporarily
        for widget in self.job_results_frame.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, ctk.CTkButton):
                    child.configure(state="disabled")
        
        # Start scraping in background
        scrape_thread = threading.Thread(
            target=self._scrape_and_analyze_job,
            args=(job,),
            daemon=True
        )
        scrape_thread.start()
    
    def _scrape_and_analyze_job(self, job: Dict[str, Any]):
        """Background thread to scrape job and analyze with AI."""
        try:
            # Step 1: Scrape job description
            self.after(0, lambda: self.progress_bar.set(0.3))
            job_description = self.scraper.scrape(job.get('url', ''))
            
            if not job_description or len(job_description) < 100:
                raise RuntimeError("Could not extract sufficient job description")
            
            # Step 2: Analyze with AI
            self.after(0, lambda: self.status_var.set("Analyzing match with AI..."))
            self.after(0, lambda: self.progress_bar.set(0.5))
            
            if not self.ai_engine:
                raise RuntimeError("AI engine not initialized")
            
            result = self.ai_engine.analyze_job(
                job_description=job_description,
                user_profile=self.user_profile
            )
            
            # Store result with job info
            result.job_info = job
            
            self.analysis_results[job.get('url')] = result
            
            # Update UI
            self.after(0, lambda: self._on_job_analysis_complete(result, job))
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.after(0, lambda: self._on_analysis_error(str(e)))
    
    def _on_job_analysis_complete(self, result: JobMatchResult, job: Dict[str, Any]):
        """Handle successful job analysis."""
        self.is_processing = False
        self.progress_bar.set(1)
        
        # Re-enable buttons
        for widget in self.job_results_frame.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, ctk.CTkButton):
                    child.configure(state="normal")
        
        # Switch to results tab
        self.tabview.set("📋 Results")
        
        # Display results
        self._display_results(result)
        
        self.status_var.set(f"✓ Analysis complete: Match Score {result.match_grade}")
        logger.info(f"Analysis complete for {job.get('title')} - Grade: {result.match_grade}")

    def _copy_bullets(self):
        """Copy tailored bullets to clipboard."""
        if not self.current_result:
            return

        bullets_text = "\n".join(self.current_result.tailored_bullets)

        self.clipboard_clear()
        self.clipboard_append(bullets_text)

        messagebox.showinfo(
            "Copied!",
            f"Copied {len(self.current_result.tailored_bullets)} bullet points to clipboard!"
        )


def main():
    """Main entry point."""
    app = JobAssistantApp()
    app.mainloop()


if __name__ == "__main__":
    main()
