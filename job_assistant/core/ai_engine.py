"""AI Engine using Google Gemini API for job matching and resume tailoring."""

import json
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, ValidationError

from utils.logger import setup_logger
from utils.config import Config

# Initialize logger
logger = setup_logger(__name__)


class JobMatchResult(BaseModel):
    """Structured output from AI analysis."""
    
    match_score: str  # A, B, C, D, or F
    confidence: float  # 0.0 to 1.0
    company_name: str
    job_title: str
    key_requirements: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    tailored_bullets: list[str]
    summary: str


class AIEngine:
    """
    Process job descriptions and user profiles using Google Gemini API.
    
    Provides job matching scores (A-F) and generates tailored resume content.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the AI engine.
        
        Args:
            api_key: Gemini API key (default: from environment variable)
            
        Raises:
            ValueError: If API key is not provided
        """
        self.api_key = api_key or Config.GEMINI_API_KEY
        
        if not self.api_key:
            logger.error("Gemini API key not configured")
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Import and configure Gemini
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        
        self.model = genai.GenerativeModel(Config.AI_MODEL)
        self.model._model_id = Config.AI_MODEL  # Store model ID for reference
        
        logger.info(f"AIEngine initialized with model: {Config.AI_MODEL}")
    
    def analyze_job(self, job_description: str, user_profile: dict) -> Optional[JobMatchResult]:
        """
        Analyze a job description against a user profile.
        
        Args:
            job_description: Raw text of the job posting
            user_profile: User's profile/resume as a dictionary
            
        Returns:
            JobMatchResult with score and recommendations, or None if analysis fails
            
        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If API call fails
        """
        if not job_description or not isinstance(job_description, str):
            logger.error("Invalid job description")
            raise ValueError("Job description must be a non-empty string")
        
        if not user_profile or not isinstance(user_profile, dict):
            logger.error("Invalid user profile")
            raise ValueError("User profile must be a non-empty dictionary")
        
        if len(job_description.strip()) < 100:
            logger.warning("Job description seems too short")
        
        logger.info("Analyzing job description...")
        
        try:
            # Construct the prompt
            prompt = self._build_prompt(job_description, user_profile)
            
            # Make API call
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": Config.TEMPERATURE,
                    "response_mime_type": "application/json",
                }
            )
            
            # Parse response
            response_text = response.text.strip()
            logger.debug(f"Raw API response: {response_text[:200]}...")
            
            # Extract JSON from response (handle potential markdown wrapping)
            json_str = self._extract_json(response_text)
            
            # Validate and parse into structured result
            result_data = json.loads(json_str)
            result = JobMatchResult(**result_data)
            
            # Validate score
            if result.match_score not in Config.VALID_SCORES:
                logger.warning(f"Invalid score '{result.match_score}', defaulting to 'C'")
                result.match_score = "C"
            
            # Validate confidence
            if not 0 <= result.confidence <= 1:
                logger.warning(f"Invalid confidence {result.confidence}, normalizing")
                result.confidence = max(0, min(1, result.confidence))
            
            logger.info(f"Analysis complete - Match Score: {result.match_score}")
            return result
            
        except ValidationError as e:
            logger.error(f"Response validation failed: {e}")
            raise RuntimeError(f"Invalid API response format: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise RuntimeError(f"Failed to parse API response as JSON: {str(e)}")
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            raise RuntimeError(f"AI analysis error: {str(e)}")
    
    def _build_prompt(self, job_description: str, user_profile: dict) -> str:
        """
        Build the system prompt for job analysis.
        
        Args:
            job_description: Raw job posting text
            user_profile: User's profile data
            
        Returns:
            Formatted prompt string
        """
        profile_json = json.dumps(user_profile, indent=2)
        
        system_instruction = """You are an expert career advisor and ATS (Applicant Tracking System) specialist. 
Analyze the job description against the candidate's profile and provide a structured assessment.

**SCORING CRITERIA:**
- **A**: Excellent match (90%+). Candidate exceeds most requirements.
- **B**: Strong match (75-89%). Candidate meets most key requirements.
- **C**: Moderate match (60-74%). Candidate meets basic requirements but has gaps.
- **D**: Weak match (40-59%). Significant skill gaps or missing key requirements.
- **F**: Poor match (<40%). Candidate lacks essential qualifications.

**OUTPUT REQUIREMENTS:**
Return ONLY valid JSON with this exact structure:
{
    "match_score": "A|B|C|D|F",
    "confidence": 0.0-1.0,
    "company_name": "extracted company name or 'Unknown'",
    "job_title": "extracted job title",
    "key_requirements": ["list", "of", "top", "requirements"],
    "matched_skills": ["skills", "candidate", "has"],
    "missing_skills": ["skills", "candidate", "lacks"],
    "tailored_bullets": ["3-5", "customized", "bullet", "points", "for", "resume"],
    "summary": "Brief 2-3 sentence assessment"
}

The tailored_bullets should:
1. Use action verbs
2. Quantify achievements where possible
3. Directly address key job requirements
4. Incorporate keywords from the job description

Now analyze this job:"""

        prompt = f"""{system_instruction}

--- JOB DESCRIPTION ---
{job_description}

--- CANDIDATE PROFILE ---
{profile_json}

--- END INPUT ---

Provide your analysis in JSON format:"""

        return prompt
    
    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from API response text.
        
        Handles cases where response might include markdown code blocks
        or extra text around the JSON.
        
        Args:
            text: Raw response text
            
        Returns:
            Clean JSON string
        """
        import re
        
        # Try to find JSON between curly braces
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json_match.group(0)
        
        # Remove markdown code block markers if present
        text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'```$', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    def get_score_explanation(self, score: str) -> str:
        """
        Get a human-readable explanation for a match score.
        
        Args:
            score: Letter grade (A-F)
            
        Returns:
            Explanation string
        """
        explanations = {
            "A": "Excellent match - You're highly qualified for this role!",
            "B": "Strong match - You meet most requirements and should apply.",
            "C": "Moderate match - Consider addressing skill gaps before applying.",
            "D": "Weak match - Significant gaps exist; may need additional preparation.",
            "F": "Poor match - This role doesn't align well with your current profile."
        }
        return explanations.get(score, "Unknown score")
