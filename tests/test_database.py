"""
Test suite for DatabaseManager module.

Tests cover:
- Database initialization
- CRUD operations (Create, Read, Update, Delete)
- Statistics calculation
- Error handling
"""

import pytest
import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'job_assistant'))

from core.database import DatabaseManager


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_jobs.db"
    return str(db_path)


@pytest.fixture
def db_manager(temp_db):
    """Create a DatabaseManager instance with temporary database."""
    return DatabaseManager(db_path=temp_db)


class TestDatabaseInitialization:
    """Test database initialization and setup."""
    
    def test_database_creation(self, temp_db):
        """Test that database file is created."""
        db = DatabaseManager(db_path=temp_db)
        assert Path(temp_db).exists()
    
    def test_tables_created(self, db_manager):
        """Test that required tables are created."""
        conn = sqlite3.connect(db_manager.db_path)
        cursor = conn.cursor()
        
        # Check if job_history table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='job_history'"
        )
        result = cursor.fetchone()
        assert result is not None
        conn.close()
    
    def test_indexes_created(self, db_manager):
        """Test that indexes are created."""
        conn = sqlite3.connect(db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        assert 'idx_date' in indexes
        assert 'idx_company' in indexes
        assert 'idx_score' in indexes
        conn.close()


class TestInsertJob:
    """Test job insertion operations."""
    
    def test_insert_valid_job(self, db_manager):
        """Test inserting a valid job record."""
        job_id = db_manager.insert_job(
            company="Tech Corp",
            role="Software Engineer",
            match_score="A",
            url="https://example.com/job/123",
            confidence=0.95,
            summary="Excellent match"
        )
        
        assert job_id is not None
        assert isinstance(job_id, int)
        assert job_id > 0
    
    def test_insert_minimal_job(self, db_manager):
        """Test inserting job with only required fields."""
        job_id = db_manager.insert_job(
            company="StartupXYZ",
            role="Developer",
            match_score="B"
        )
        
        assert job_id is not None
    
    def test_insert_invalid_score(self, db_manager):
        """Test that invalid match scores raise error."""
        with pytest.raises(ValueError, match="Match score must be one of"):
            db_manager.insert_job(
                company="Test",
                role="Test",
                match_score="X"
            )
    
    def test_insert_missing_company(self, db_manager):
        """Test that missing company raises error."""
        with pytest.raises(ValueError, match="Company name is required"):
            db_manager.insert_job(
                company="",
                role="Developer",
                match_score="A"
            )
    
    def test_insert_missing_role(self, db_manager):
        """Test that missing role raises error."""
        with pytest.raises(ValueError, match="Job role is required"):
            db_manager.insert_job(
                company="Test Corp",
                role="",
                match_score="A"
            )
    
    def test_insert_custom_date(self, db_manager):
        """Test inserting job with custom date."""
        custom_date = "2024-01-15"
        job_id = db_manager.insert_job(
            company="Test",
            role="Test",
            match_score="C",
            date=custom_date
        )
        
        job = db_manager.get_job_by_id(job_id)
        assert job['date'] == custom_date


class TestGetJobs:
    """Test job retrieval operations."""
    
    def test_get_all_jobs_empty(self, db_manager):
        """Test getting all jobs when database is empty."""
        jobs = db_manager.get_all_jobs()
        assert jobs == []
    
    def test_get_all_jobs(self, db_manager):
        """Test retrieving all jobs."""
        # Insert multiple jobs
        db_manager.insert_job("Company A", "Role 1", "A")
        db_manager.insert_job("Company B", "Role 2", "B")
        db_manager.insert_job("Company C", "Role 3", "C")
        
        jobs = db_manager.get_all_jobs()
        assert len(jobs) == 3
    
    def test_get_jobs_limit(self, db_manager):
        """Test job retrieval with limit."""
        for i in range(10):
            db_manager.insert_job(f"Company {i}", f"Role {i}", "A")
        
        jobs = db_manager.get_all_jobs(limit=5)
        assert len(jobs) == 5
    
    def test_get_jobs_by_score(self, db_manager):
        """Test filtering jobs by score."""
        db_manager.insert_job("Company A", "Role 1", "A")
        db_manager.insert_job("Company B", "Role 2", "A")
        db_manager.insert_job("Company C", "Role 3", "B")
        db_manager.insert_job("Company D", "Role 4", "C")
        
        a_jobs = db_manager.get_jobs_by_score("A")
        assert len(a_jobs) == 2
        
        b_jobs = db_manager.get_jobs_by_score("B")
        assert len(b_jobs) == 1
    
    def test_get_job_by_id(self, db_manager):
        """Test retrieving specific job by ID."""
        job_id = db_manager.insert_job(
            company="Unique Corp",
            role="Unique Role",
            match_score="A",
            summary="Test summary"
        )
        
        job = db_manager.get_job_by_id(job_id)
        assert job is not None
        assert job['company'] == "Unique Corp"
        assert job['role'] == "Unique Role"
        assert job['summary'] == "Test summary"
    
    def test_get_nonexistent_job(self, db_manager):
        """Test retrieving job that doesn't exist."""
        job = db_manager.get_job_by_id(99999)
        assert job is None


class TestDeleteJob:
    """Test job deletion operations."""
    
    def test_delete_existing_job(self, db_manager):
        """Test deleting an existing job."""
        job_id = db_manager.insert_job("To Delete", "Role", "A")
        
        result = db_manager.delete_job(job_id)
        assert result is True
        
        # Verify deletion
        job = db_manager.get_job_by_id(job_id)
        assert job is None
    
    def test_delete_nonexistent_job(self, db_manager):
        """Test deleting job that doesn't exist."""
        result = db_manager.delete_job(99999)
        assert result is False
    
    def test_clear_all(self, db_manager):
        """Test clearing all jobs."""
        # Insert multiple jobs
        for i in range(5):
            db_manager.insert_job(f"Company {i}", f"Role {i}", "A")
        
        deleted_count = db_manager.clear_all()
        assert deleted_count == 5
        
        # Verify all deleted
        jobs = db_manager.get_all_jobs()
        assert len(jobs) == 0


class TestStatistics:
    """Test statistics calculation."""
    
    def test_statistics_empty(self, db_manager):
        """Test statistics with empty database."""
        stats = db_manager.get_statistics()
        
        assert stats['total'] == 0
        assert stats['a_count'] == 0
        assert stats['b_count'] == 0
        assert stats['avg_confidence'] == 0.0
    
    def test_statistics_with_data(self, db_manager):
        """Test statistics with sample data."""
        db_manager.insert_job("A", "R", "A", confidence=0.9)
        db_manager.insert_job("B", "R", "A", confidence=0.8)
        db_manager.insert_job("C", "R", "B", confidence=0.7)
        db_manager.insert_job("D", "R", "C", confidence=0.6)
        
        stats = db_manager.get_statistics()
        
        assert stats['total'] == 4
        assert stats['a_count'] == 2
        assert stats['b_count'] == 1
        assert stats['c_count'] == 1
        assert stats['d_count'] == 0
        assert stats['f_count'] == 0
        assert 0.7 <= stats['avg_confidence'] <= 0.8


class TestJobRecordStructure:
    """Test that job records have correct structure."""
    
    def test_record_fields(self, db_manager):
        """Test that retrieved records have all expected fields."""
        job_id = db_manager.insert_job(
            company="Test Corp",
            role="Test Role",
            match_score="A",
            url="https://test.com",
            confidence=0.95,
            summary="Test summary"
        )
        
        job = db_manager.get_job_by_id(job_id)
        
        expected_fields = [
            'id', 'date', 'company', 'role', 'match_score',
            'url', 'confidence', 'summary', 'created_at'
        ]
        
        for field in expected_fields:
            assert field in job, f"Missing field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
