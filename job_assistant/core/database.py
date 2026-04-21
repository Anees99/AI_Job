"""SQLite database management for job application history."""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Tuple
from pathlib import Path

from utils.logger import setup_logger
from utils.config import Config

# Initialize logger
logger = setup_logger(__name__)


class DatabaseManager:
    """
    Manage SQLite database for tracking job applications.
    
    Provides CRUD operations for the job_history table.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file (default: from Config)
        """
        self.db_path = db_path or str(Config.DATABASE_PATH)
        self._ensure_directory()
        self._initialize_db()
        logger.info(f"DatabaseManager initialized with database: {self.db_path}")
    
    def _ensure_directory(self):
        """Ensure the directory for the database file exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection with row factory enabled.
        
        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _initialize_db(self):
        """Create database tables if they don't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS job_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            match_score TEXT NOT NULL,
            url TEXT,
            confidence REAL,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_date ON job_history(date);
        CREATE INDEX IF NOT EXISTS idx_company ON job_history(company);
        CREATE INDEX IF NOT EXISTS idx_score ON job_history(match_score);
        """
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executescript(create_table_sql)
                conn.commit()
            logger.debug("Database tables initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def insert_job(
        self,
        company: str,
        role: str,
        match_score: str,
        url: str = None,
        confidence: float = None,
        summary: str = None,
        date: str = None
    ) -> int:
        """
        Insert a new job application record.
        
        Args:
            company: Company name
            role: Job title/role
            match_score: Letter grade (A-F)
            url: Job posting URL (optional)
            confidence: AI confidence score 0-1 (optional)
            summary: Brief assessment summary (optional)
            date: Application date in YYYY-MM-DD format (default: today)
            
        Returns:
            ID of the inserted record
            
        Raises:
            ValueError: If required fields are missing
            RuntimeError: If database operation fails
        """
        if not company or not isinstance(company, str):
            logger.error("Invalid company name")
            raise ValueError("Company name is required")
        
        if not role or not isinstance(role, str):
            logger.error("Invalid role")
            raise ValueError("Job role is required")
        
        if not match_score or match_score not in ["A", "B", "C", "D", "F"]:
            logger.error(f"Invalid match score: {match_score}")
            raise ValueError("Match score must be one of: A, B, C, D, F")
        
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        insert_sql = """
        INSERT INTO job_history (date, company, role, match_score, url, confidence, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    insert_sql,
                    (date, company, role, match_score, url, confidence, summary)
                )
                conn.commit()
                record_id = cursor.lastrowid
                logger.info(f"Inserted job record: ID={record_id}, Company={company}, Role={role}, Score={match_score}")
                return record_id
                
        except sqlite3.Error as e:
            logger.error(f"Database insert failed: {e}")
            raise RuntimeError(f"Failed to insert job record: {str(e)}")
    
    def get_all_jobs(self, limit: int = 100) -> List[dict]:
        """
        Retrieve all job records, ordered by date (newest first).
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of job records as dictionaries
        """
        query = """
        SELECT id, date, company, role, match_score, url, confidence, summary, created_at
        FROM job_history
        ORDER BY date DESC, created_at DESC
        LIMIT ?
        """
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (limit,))
                rows = cursor.fetchall()
                jobs = [dict(row) for row in rows]
                logger.debug(f"Retrieved {len(jobs)} job records")
                return jobs
        except sqlite3.Error as e:
            logger.error(f"Database query failed: {e}")
            raise RuntimeError(f"Failed to retrieve jobs: {str(e)}")
    
    def get_jobs_by_score(self, score: str) -> List[dict]:
        """
        Retrieve jobs filtered by match score.
        
        Args:
            score: Letter grade to filter by (A-F)
            
        Returns:
            List of matching job records
        """
        if score not in ["A", "B", "C", "D", "F"]:
            logger.error(f"Invalid score filter: {score}")
            raise ValueError("Score must be one of: A, B, C, D, F")
        
        query = """
        SELECT id, date, company, role, match_score, url, confidence, summary, created_at
        FROM job_history
        WHERE match_score = ?
        ORDER BY date DESC
        """
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (score,))
                rows = cursor.fetchall()
                jobs = [dict(row) for row in rows]
                logger.debug(f"Retrieved {len(jobs)} jobs with score {score}")
                return jobs
        except sqlite3.Error as e:
            logger.error(f"Database query failed: {e}")
            raise RuntimeError(f"Failed to retrieve jobs: {str(e)}")
    
    def get_job_by_id(self, job_id: int) -> Optional[dict]:
        """
        Retrieve a specific job record by ID.
        
        Args:
            job_id: The record ID
            
        Returns:
            Job record as dictionary, or None if not found
        """
        query = """
        SELECT id, date, company, role, match_score, url, confidence, summary, created_at
        FROM job_history
        WHERE id = ?
        """
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (job_id,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except sqlite3.Error as e:
            logger.error(f"Database query failed: {e}")
            raise RuntimeError(f"Failed to retrieve job: {str(e)}")
    
    def delete_job(self, job_id: int) -> bool:
        """
        Delete a job record by ID.
        
        Args:
            job_id: The record ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM job_history WHERE id = ?"
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (job_id,))
                conn.commit()
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Deleted job record: ID={job_id}")
                else:
                    logger.warning(f"Job record not found: ID={job_id}")
                return deleted
        except sqlite3.Error as e:
            logger.error(f"Database delete failed: {e}")
            raise RuntimeError(f"Failed to delete job: {str(e)}")
    
    def get_statistics(self) -> dict:
        """
        Get summary statistics of job applications.
        
        Returns:
            Dictionary with counts by score and total
        """
        stats_query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN match_score = 'A' THEN 1 ELSE 0 END) as a_count,
            SUM(CASE WHEN match_score = 'B' THEN 1 ELSE 0 END) as b_count,
            SUM(CASE WHEN match_score = 'C' THEN 1 ELSE 0 END) as c_count,
            SUM(CASE WHEN match_score = 'D' THEN 1 ELSE 0 END) as d_count,
            SUM(CASE WHEN match_score = 'F' THEN 1 ELSE 0 END) as f_count,
            AVG(confidence) as avg_confidence
        FROM job_history
        """
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(stats_query)
                row = cursor.fetchone()
                
                if row:
                    stats = {
                        "total": row["total"] or 0,
                        "a_count": row["a_count"] or 0,
                        "b_count": row["b_count"] or 0,
                        "c_count": row["c_count"] or 0,
                        "d_count": row["d_count"] or 0,
                        "f_count": row["f_count"] or 0,
                        "avg_confidence": row["avg_confidence"] or 0.0
                    }
                    logger.debug(f"Statistics calculated: {stats['total']} total jobs")
                    return stats
                return {"total": 0}
        except sqlite3.Error as e:
            logger.error(f"Database statistics query failed: {e}")
            raise RuntimeError(f"Failed to get statistics: {str(e)}")
    
    def clear_all(self) -> int:
        """
        Delete all records from the database.
        
        WARNING: This cannot be undone!
        
        Returns:
            Number of records deleted
        """
        query = "DELETE FROM job_history"
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()
                deleted = cursor.rowcount
                logger.warning(f"Cleared all {deleted} job records from database")
                return deleted
        except sqlite3.Error as e:
            logger.error(f"Database clear failed: {e}")
            raise RuntimeError(f"Failed to clear database: {str(e)}")
