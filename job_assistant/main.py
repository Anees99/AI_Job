"""
AI-Driven Dynamic Job Application & Career Assistant
Main GUI Application using CustomTkinter
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from utils.logger import setup_logger
from utils.config import Config
from core.scraper import JobScraper
from core.ai_engine import AIEngine, JobMatchResult
from core.database import DatabaseManager

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
        self.geometry("1200x800")
        self.minsize(1000, 700)

        # State variables
        self.scraper: Optional[JobScraper] = None
        self.ai_engine: Optional[AIEngine] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.user_profile: dict = {}
        self.current_result: Optional[JobMatchResult] = None
        self.is_processing = False

        # Initialize core components
        self._initialize_components()

        # Load user profile
        self._load_user_profile()

        # Build UI
        self._create_ui()

        logger.info("Application started successfully")

    def _initialize_components(self):
        """Initialize scraper, AI engine, and database manager."""
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
            self.scraper = JobScraper()
            logger.info("Scraper initialized")
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {e}")
            # Scraper failure is not critical at startup

    def _load_user_profile(self):
        """Load user profile from file or create default."""
        profile_path = Config.USER_PROFILE_PATH

        if profile_path.exists():
            try:
                with open(profile_path, 'r') as f:
                    self.user_profile = json.load(f)
                logger.info(f"Loaded user profile from {profile_path}")
            except Exception as e:
                logger.warning(f"Failed to load profile, using default: {e}")
                self.user_profile = Config.get_default_profile()
        else:
            logger.info("No profile found, using default template")
            self.user_profile = Config.get_default_profile()
            # Save default profile
            self._save_user_profile()

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
        """Build the job analysis tab."""
        self.tab_analyze.grid_columnconfigure(0, weight=1)
        self.tab_analyze.grid_rowconfigure(2, weight=1)

        # URL input section
        url_frame = ctk.CTkFrame(self.tab_analyze, fg_color="transparent")
        url_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        url_frame.grid_columnconfigure(1, weight=1)

        url_label = ctk.CTkLabel(url_frame, text="Job Posting URL:")
        url_label.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.url_entry = ctk.CTkEntry(url_frame, placeholder_text="https://...")
        self.url_entry.grid(row=0, column=1, sticky="ew")

        self.btn_scrape = ctk.CTkButton(
            url_frame,
            text="Extract Description",
            command=self._start_scraping,
            width=150
        )
        self.btn_scrape.grid(row=0, column=2, padx=(10, 0))

        # Scraped content preview
        content_label = ctk.CTkLabel(
            self.tab_analyze,
            text="Extracted Job Description:",
            anchor="w"
        )
        content_label.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="w")

        self.txt_content = ctk.CTkTextbox(
            self.tab_analyze,
            height=200,
            state="disabled"
        )
        self.txt_content.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")

        # Analyze button
        self.btn_analyze = ctk.CTkButton(
            self.tab_analyze,
            text="🚀 Analyze with AI",
            command=self._start_analysis,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            state="disabled"
        )
        self.btn_analyze.grid(row=3, column=0, padx=20, pady=20)

        # Progress indicator
        self.progress_bar = ctk.CTkProgressBar(self.tab_analyze)
        self.progress_bar.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            self.tab_analyze,
            text="",
            text_color="gray"
        )
        self.status_label.grid(row=5, column=0, padx=20, pady=(0, 20))

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

    def _generate_pdf(self):
        """Generate PDF resume (placeholder - full implementation later)."""
        if not self.current_result:
            return

        messagebox.showinfo(
            "PDF Generation",
            "PDF generation feature coming soon!\n\n"
            "For now, you can copy the tailored bullets and add them to your resume manually."
        )

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
