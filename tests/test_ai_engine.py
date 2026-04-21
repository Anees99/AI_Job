"""
Test suite for AIEngine module.

Tests cover:
- AI engine initialization
- Job analysis (with mocked API)
- Score validation
- Error handling
- Cost estimation
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'job_assistant'))

from core.ai_engine import AIEngine, JobMatchResult


@pytest.fixture
def mock_api_key():
    """Provide a mock API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def sample_user_profile():
    """Sample user profile for testing."""
    return {
        "personal_info": {
            "name": "John Doe",
            "email": "john@example.com",
            "skills": ["Python", "JavaScript", "SQL"]
        },
        "experience": [
            {
                "title": "Software Developer",
                "company": "Tech Corp",
                "bullets": ["Developed web applications"]
            }
        ],
        "education": [
            {
                "degree": "BS Computer Science",
                "institution": "University"
            }
        ]
    }


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return """
    Senior Python Developer
    
    We are looking for an experienced Python developer to join our team.
    
    Requirements:
    - 5+ years of Python experience
    - Strong knowledge of SQL databases
    - Experience with web frameworks (Django, Flask)
    - Familiarity with JavaScript and frontend technologies
    - Excellent problem-solving skills
    
    Responsibilities:
    - Design and implement scalable backend services
    - Collaborate with cross-functional teams
    - Write clean, maintainable code
    """


class TestAIEngineInitialization:
    """Test AI engine initialization."""
    
    def test_init_with_api_key(self, mock_api_key):
        """Test initialization with provided API key."""
        with patch('google.generativeai.configure') as mock_configure:
            with patch('google.generativeai.GenerativeModel'):
                engine = AIEngine(api_key=mock_api_key)
                assert engine.api_key == mock_api_key
                mock_configure.assert_called_once_with(api_key=mock_api_key)
    
    def test_init_without_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        with patch('core.ai_engine.Config.GEMINI_API_KEY', ""):
            with pytest.raises(ValueError, match="Gemini API key required"):
                AIEngine()


class TestJobAnalysis:
    """Test job analysis functionality."""
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_analyze_job_success(self, mock_model_class, mock_configure, 
                                  mock_api_key, sample_job_description, 
                                  sample_user_profile):
        """Test successful job analysis."""
        # Mock API response
        mock_response = Mock()
        mock_response.text = json.dumps({
            "match_score": "A",
            "confidence": 0.92,
            "company_name": "Test Company",
            "job_title": "Senior Python Developer",
            "key_requirements": ["Python", "SQL", "Web frameworks"],
            "matched_skills": ["Python", "SQL", "JavaScript"],
            "missing_skills": ["Django", "Flask"],
            "tailored_bullets": [
                "Developed scalable Python applications serving 10k+ users",
                "Optimized SQL queries reducing response time by 40%"
            ],
            "summary": "Strong candidate with relevant experience."
        })
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        engine = AIEngine(api_key=mock_api_key)
        result = engine.analyze_job(sample_job_description, sample_user_profile)
        
        assert result is not None
        assert isinstance(result, JobMatchResult)
        assert result.match_score == "A"
        assert result.confidence == 0.92
        assert result.company_name == "Test Company"
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_analyze_job_invalid_input_empty_description(self, mock_model_class, 
                                                          mock_configure,
                                                          mock_api_key,
                                                          sample_user_profile):
        """Test that empty job description raises ValueError."""
        engine = AIEngine(api_key=mock_api_key)
        
        with pytest.raises(ValueError, match="Job description must be a non-empty string"):
            engine.analyze_job("", sample_user_profile)
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_analyze_job_invalid_input_empty_profile(self, mock_model_class,
                                                      mock_configure,
                                                      mock_api_key,
                                                      sample_job_description):
        """Test that empty profile raises ValueError."""
        engine = AIEngine(api_key=mock_api_key)
        
        with pytest.raises(ValueError, match="User profile must be a non-empty dictionary"):
            engine.analyze_job(sample_job_description, {})
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_analyze_job_score_normalization(self, mock_model_class, mock_configure,
                                              mock_api_key, sample_job_description,
                                              sample_user_profile):
        """Test that invalid scores are normalized."""
        # Mock response with invalid score
        mock_response = Mock()
        mock_response.text = json.dumps({
            "match_score": "X",  # Invalid score
            "confidence": 0.8,
            "company_name": "Test",
            "job_title": "Dev",
            "key_requirements": [],
            "matched_skills": [],
            "missing_skills": [],
            "tailored_bullets": [],
            "summary": "Test"
        })
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        engine = AIEngine(api_key=mock_api_key)
        result = engine.analyze_job(sample_job_description, sample_user_profile)
        
        # Should default to 'C' for invalid score
        assert result.match_score == "C"
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_analyze_job_confidence_normalization(self, mock_model_class, mock_configure,
                                                   mock_api_key, sample_job_description,
                                                   sample_user_profile):
        """Test that confidence values are normalized to 0-1 range."""
        # Mock response with out-of-range confidence
        mock_response = Mock()
        mock_response.text = json.dumps({
            "match_score": "B",
            "confidence": 1.5,  # > 1.0
            "company_name": "Test",
            "job_title": "Dev",
            "key_requirements": [],
            "matched_skills": [],
            "missing_skills": [],
            "tailored_bullets": [],
            "summary": "Test"
        })
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        engine = AIEngine(api_key=mock_api_key)
        result = engine.analyze_job(sample_job_description, sample_user_profile)
        
        assert 0 <= result.confidence <= 1


class TestScoreExplanation:
    """Test score explanation functionality."""
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_get_score_explanation(self, mock_model_class, mock_configure, mock_api_key):
        """Test getting human-readable score explanations."""
        engine = AIEngine(api_key=mock_api_key)
        
        explanations = {
            "A": "Excellent match",
            "B": "Strong match",
            "C": "Moderate match",
            "D": "Weak match",
            "F": "Poor match"
        }
        
        for score, expected_text in explanations.items():
            explanation = engine.get_score_explanation(score)
            assert expected_text in explanation
    
    def test_get_score_explanation_unknown(self, mock_api_key):
        """Test explanation for unknown score."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel'):
                engine = AIEngine(api_key=mock_api_key)
                explanation = engine.get_score_explanation("Z")
                assert explanation == "Unknown score"


class TestJSONExtraction:
    """Test JSON extraction from API responses."""
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_extract_json_plain(self, mock_model_class, mock_configure, mock_api_key):
        """Test extracting JSON from plain text."""
        engine = AIEngine(api_key=mock_api_key)
        
        json_str = '{"match_score": "A", "confidence": 0.9}'
        result = engine._extract_json(json_str)
        
        parsed = json.loads(result)
        assert parsed['match_score'] == "A"
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_extract_json_markdown_block(self, mock_model_class, mock_configure, mock_api_key):
        """Test extracting JSON from markdown code block."""
        engine = AIEngine(api_key=mock_api_key)
        
        markdown_json = """```json
        {"match_score": "B", "confidence": 0.8}
        ```"""
        
        result = engine._extract_json(markdown_json)
        parsed = json.loads(result)
        assert parsed['match_score'] == "B"
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_extract_json_with_surrounding_text(self, mock_model_class, mock_configure, mock_api_key):
        """Test extracting JSON with surrounding text."""
        engine = AIEngine(api_key=mock_api_key)
        
        text_with_json = """Here is the analysis:
        {"match_score": "C", "confidence": 0.7}
        Hope this helps!"""
        
        result = engine._extract_json(text_with_json)
        parsed = json.loads(result)
        assert parsed['match_score'] == "C"


class TestCostEstimation:
    """Test API cost estimation."""
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_cost_estimation_available(self, mock_model_class, mock_configure, mock_api_key):
        """Test that cost estimation information is available."""
        # This is more of a documentation test
        # In production, you'd want to track token usage
        engine = AIEngine(api_key=mock_api_key)
        
        # Verify engine has necessary attributes for cost tracking
        assert hasattr(engine, 'api_key')
        assert hasattr(engine, 'model')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
