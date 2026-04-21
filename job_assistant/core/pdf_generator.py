"""
PDF Generator Module for AI-Driven Job Application Assistant.

This module generates professional, tailored PDF resumes using ReportLab.
It takes the AI-generated content and user profile to create a customized
resume optimized for the specific job application.

Author: Senior Computer Systems Engineer
Project: AI-Driven Dynamic Job Application & Career Assistant
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

from utils.logger import setup_logger

logger = setup_logger(__name__)


class PDFGenerator:
    """
    Generates professional PDF resumes tailored to specific job applications.
    
    This class handles the creation of well-formatted, ATS-friendly PDF resumes
    that incorporate AI-generated tailored content based on job descriptions.
    """
    
    def __init__(self, output_dir: str = "data/resumes"):
        """
        Initialize the PDF generator.
        
        Args:
            output_dir: Directory where generated PDFs will be saved.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Register fonts if needed (using default Helvetica for compatibility)
        self._setup_styles()
        
        logger.info(f"PDFGenerator initialized with output directory: {self.output_dir}")
    
    def _setup_styles(self):
        """Set up custom paragraph styles for the resume."""
        self.styles = getSampleStyleSheet()
        
        # Custom title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceBefore=16,
            spaceAfter=8,
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderPadding=4,
            borderColor=colors.HexColor('#3498db'),
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='ResumeBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=6,
            alignment=TA_LEFT,
            fontName='Helvetica',
        ))
        
        # Bullet point style
        self.styles.add(ParagraphStyle(
            name='BulletPoint',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=4,
            leftIndent=12,
            bulletIndent=12,
            fontName='Helvetica',
        ))
        
        # Contact info style
        self.styles.add(ParagraphStyle(
            name='ContactInfo',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=4,
            alignment=TA_CENTER,
            fontName='Helvetica',
        ))
        
        # Skills style
        self.styles.add(ParagraphStyle(
            name='Skills',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=3,
            fontName='Helvetica',
        ))
        
        logger.debug("Custom styles configured successfully")
    
    def generate_resume(
        self,
        user_profile: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        job_details: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate a tailored PDF resume.
        
        Args:
            user_profile: User's base profile information (skills, experience, etc.)
            ai_analysis: AI-generated analysis including tailored bullets and suggestions
            job_details: Optional job details (company, role, etc.) for header
            filename: Optional custom filename; if None, auto-generated
            
        Returns:
            Path to the generated PDF file
            
        Raises:
            ValueError: If required data is missing
            IOError: If PDF generation fails
        """
        try:
            # Validate inputs
            if not user_profile:
                raise ValueError("User profile is required")
            if not ai_analysis:
                raise ValueError("AI analysis is required")
            
            # Generate filename if not provided
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                company = job_details.get('company', 'Company') if job_details else 'Company'
                role = job_details.get('role', 'Role') if job_details else 'Role'
                # Sanitize filename
                safe_company = "".join(c for c in company if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_role = "".join(c for c in role if c.isalnum() or c in (' ', '-', '_')).strip()
                filename = f"Resume_{safe_company}_{safe_role}_{timestamp}.pdf"
            
            output_path = self.output_dir / filename
            
            # Build PDF content
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch,
            )
            
            story = []
            
            # Add header with name and contact info
            story.extend(self._build_header(user_profile, job_details))
            
            # Add professional summary (tailored if available)
            story.extend(self._build_summary(user_profile, ai_analysis))
            
            # Add tailored skills section
            story.extend(self._build_skills(user_profile, ai_analysis))
            
            # Add experience with tailored bullets
            story.extend(self._build_experience(user_profile, ai_analysis))
            
            # Add education
            story.extend(self._build_education(user_profile))
            
            # Add projects or additional sections if available
            story.extend(self._build_additional_sections(user_profile, ai_analysis))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"PDF resume generated successfully: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to generate PDF resume: {str(e)}", exc_info=True)
            raise IOError(f"PDF generation failed: {str(e)}") from e
    
    def _build_header(
        self,
        user_profile: Dict[str, Any],
        job_details: Optional[Dict[str, Any]]
    ) -> List:
        """Build the resume header with name and contact information."""
        elements = []
        
        # Name
        name = user_profile.get('name', 'Your Name')
        elements.append(Paragraph(name, self.styles['CustomTitle']))
        
        # Target role (if job details provided)
        if job_details and job_details.get('role'):
            target_role = f"Target Position: {job_details['role']}"
            elements.append(Paragraph(target_role, self.styles['ContactInfo']))
        
        # Contact information
        contact_info = []
        if user_profile.get('email'):
            contact_info.append(user_profile['email'])
        if user_profile.get('phone'):
            contact_info.append(user_profile['phone'])
        if user_profile.get('location'):
            contact_info.append(user_profile['location'])
        if user_profile.get('linkedin'):
            contact_info.append(f"LinkedIn: {user_profile['linkedin']}")
        if user_profile.get('github'):
            contact_info.append(f"GitHub: {user_profile['github']}")
        
        if contact_info:
            contact_string = " | ".join(contact_info)
            elements.append(Paragraph(contact_string, self.styles['ContactInfo']))
        
        # Horizontal line using a simple table approach
        elements.append(Spacer(1, 0.1*inch))
        line_table = Table([[6*inch, 0.5]], colWidths=[6*inch], rowHeights=[0.5])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _build_summary(
        self,
        user_profile: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> List:
        """Build the professional summary section."""
        elements = []
        
        elements.append(Paragraph("PROFESSIONAL SUMMARY", self.styles['SectionHeader']))
        
        # Use AI-tailored summary if available, otherwise use profile summary
        summary = ai_analysis.get('tailored_summary') or user_profile.get('summary', '')
        
        if summary:
            # Split into paragraphs if needed
            paragraphs = summary.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    elements.append(Paragraph(para.strip(), self.styles['ResumeBody']))
        else:
            # Generate a basic summary from profile
            title = user_profile.get('title', 'Professional')
            years_exp = user_profile.get('years_of_experience', '')
            key_skills = user_profile.get('skills', [])[:5]
            
            if years_exp:
                summary_text = f"{title} with {years_exp} years of experience. "
            else:
                summary_text = f"{title} with proven expertise. "
            
            if key_skills:
                summary_text += f"Skilled in {', '.join(key_skills)}."
            
            elements.append(Paragraph(summary_text, self.styles['ResumeBody']))
        
        elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _build_skills(
        self,
        user_profile: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> List:
        """Build the skills section with AI-prioritized skills."""
        elements = []
        
        elements.append(Paragraph("SKILLS", self.styles['SectionHeader']))
        
        # Get matched/prioritized skills from AI analysis
        matched_skills = ai_analysis.get('matched_skills', [])
        all_skills = user_profile.get('skills', [])
        
        # Prioritize matched skills, then add remaining
        if matched_skills:
            # Display matched skills prominently
            skills_text = "Key Skills: " + ", ".join(matched_skills[:10])
            elements.append(Paragraph(skills_text, self.styles['Skills']))
            
            # Add other skills if any
            other_skills = [s for s in all_skills if s not in matched_skills]
            if other_skills:
                other_text = "Additional Skills: " + ", ".join(other_skills[:10])
                elements.append(Paragraph(other_text, self.styles['Skills']))
        else:
            # Fallback to all skills
            if all_skills:
                skills_text = ", ".join(all_skills[:15])
                elements.append(Paragraph(skills_text, self.styles['Skills']))
        
        elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _build_experience(
        self,
        user_profile: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> List:
        """Build the work experience section with tailored bullets."""
        elements = []
        
        elements.append(Paragraph("WORK EXPERIENCE", self.styles['SectionHeader']))
        
        experiences = user_profile.get('experience', [])
        tailored_bullets = ai_analysis.get('tailored_bullets', {})
        
        if experiences:
            for idx, exp in enumerate(experiences):
                # Company and role
                company = exp.get('company', 'Company')
                role = exp.get('role', 'Position')
                dates = exp.get('dates', '')
                location = exp.get('location', '')
                
                # Create header line
                header_text = f"<b>{role}</b> at <b>{company}</b>"
                if dates:
                    header_text += f" | {dates}"
                if location:
                    header_text += f" | {location}"
                
                elements.append(Paragraph(header_text, self.styles['ResumeBody']))
                
                # Add tailored bullets if available for this position
                # Otherwise use original bullets
                bullets = tailored_bullets.get(str(idx), exp.get('bullets', []))
                
                if isinstance(bullets, list):
                    for bullet in bullets[:6]:  # Limit to 6 bullets per role
                        if bullet.strip():
                            # Format bullet point
                            bullet_text = f"• {bullet}"
                            elements.append(Paragraph(bullet_text, self.styles['BulletPoint']))
                
                elements.append(Spacer(1, 0.08*inch))
        else:
            elements.append(Paragraph("Experience details not provided.", self.styles['ResumeBody']))
        
        elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _build_education(self, user_profile: Dict[str, Any]) -> List:
        """Build the education section."""
        elements = []
        
        elements.append(Paragraph("EDUCATION", self.styles['SectionHeader']))
        
        education_list = user_profile.get('education', [])
        
        if education_list:
            for edu in education_list:
                degree = edu.get('degree', '')
                school = edu.get('school', '')
                graduation = edu.get('graduation_year', '')
                gpa = edu.get('gpa', '')
                
                edu_text = f"<b>{degree}</b> - {school}"
                if graduation:
                    edu_text += f" | Graduated: {graduation}"
                if gpa:
                    edu_text += f" | GPA: {gpa}"
                
                elements.append(Paragraph(edu_text, self.styles['ResumeBody']))
        else:
            elements.append(Paragraph("Education details not provided.", self.styles['ResumeBody']))
        
        elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _build_additional_sections(
        self,
        user_profile: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> List:
        """Build additional sections (projects, certifications, etc.)."""
        elements = []
        
        # Projects section
        projects = user_profile.get('projects', [])
        if projects:
            elements.append(Paragraph("PROJECTS", self.styles['SectionHeader']))
            
            for project in projects[:3]:  # Limit to 3 projects
                proj_name = project.get('name', 'Project')
                proj_desc = project.get('description', '')
                proj_tech = project.get('technologies', [])
                
                proj_text = f"<b>{proj_name}</b>"
                if proj_tech:
                    proj_text += f" ({', '.join(proj_tech)})"
                elements.append(Paragraph(proj_text, self.styles['ResumeBody']))
                
                if proj_desc:
                    elements.append(Paragraph(proj_desc, self.styles['BulletPoint']))
            
            elements.append(Spacer(1, 0.1*inch))
        
        # Certifications section
        certifications = user_profile.get('certifications', [])
        if certifications:
            elements.append(Paragraph("CERTIFICATIONS", self.styles['SectionHeader']))
            
            for cert in certifications:
                if isinstance(cert, str):
                    elements.append(Paragraph(f"• {cert}", self.styles['BulletPoint']))
                elif isinstance(cert, dict):
                    cert_name = cert.get('name', '')
                    cert_issuer = cert.get('issuer', '')
                    cert_date = cert.get('date', '')
                    
                    cert_text = f"• {cert_name}"
                    if cert_issuer:
                        cert_text += f" - {cert_issuer}"
                    if cert_date:
                        cert_text += f" ({cert_date})"
                    
                    elements.append(Paragraph(cert_text, self.styles['BulletPoint']))
            
            elements.append(Spacer(1, 0.1*inch))
        
        # AI recommendations section (optional)
        recommendations = ai_analysis.get('recommendations', [])
        if recommendations:
            elements.append(Paragraph("KEY QUALIFICATIONS FOR THIS ROLE", self.styles['SectionHeader']))
            
            for rec in recommendations[:5]:
                elements.append(Paragraph(f"• {rec}", self.styles['BulletPoint']))
            
            elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def generate_cover_letter(
        self,
        user_profile: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        job_details: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        Generate a tailored cover letter PDF.
        
        Args:
            user_profile: User's base profile information
            ai_analysis: AI-generated analysis with tailored content
            job_details: Job details (company, role, hiring manager, etc.)
            filename: Optional custom filename
            
        Returns:
            Path to the generated PDF file
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                company = job_details.get('company', 'Company')
                safe_company = "".join(c for c in company if c.isalnum() or c in (' ', '-', '_')).strip()
                filename = f"CoverLetter_{safe_company}_{timestamp}.pdf"
            
            output_path = self.output_dir / filename
            
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                rightMargin=1*inch,
                leftMargin=1*inch,
                topMargin=1*inch,
                bottomMargin=1*inch,
            )
            
            story = []
            
            # Header
            name = user_profile.get('name', 'Your Name')
            contact_info = []
            if user_profile.get('email'):
                contact_info.append(user_profile['email'])
            if user_profile.get('phone'):
                contact_info.append(user_profile['phone'])
            if user_profile.get('location'):
                contact_info.append(user_profile['location'])
            
            story.append(Paragraph(name, self.styles['CustomTitle']))
            if contact_info:
                story.append(Paragraph(" | ".join(contact_info), self.styles['ContactInfo']))
            
            story.append(Spacer(1, 0.5*inch))
            
            # Date
            story.append(Paragraph(datetime.now().strftime("%B %d, %Y"), self.styles['ResumeBody']))
            story.append(Spacer(1, 0.2*inch))
            
            # Recipient info
            company = job_details.get('company', 'Hiring Team')
            role = job_details.get('role', 'Position')
            
            story.append(Paragraph(f"Hiring Manager", self.styles['ResumeBody']))
            story.append(Paragraph(f"{company}", self.styles['ResumeBody']))
            story.append(Spacer(1, 0.3*inch))
            
            # Salutation
            story.append(Paragraph(f"Dear Hiring Manager,", self.styles['ResumeBody']))
            story.append(Spacer(1, 0.2*inch))
            
            # Opening paragraph
            opening = ai_analysis.get('cover_letter_opening', '')
            if not opening:
                opening = (f"I am writing to express my strong interest in the {role} position at {company}. "
                          f"With my background and skills, I am confident in my ability to contribute effectively to your team.")
            story.append(Paragraph(opening, self.styles['ResumeBody']))
            story.append(Spacer(1, 0.15*inch))
            
            # Body paragraphs (tailored)
            body_paragraphs = ai_analysis.get('cover_letter_body', [])
            if body_paragraphs:
                for para in body_paragraphs[:3]:
                    story.append(Paragraph(para, self.styles['ResumeBody']))
                    story.append(Spacer(1, 0.15*inch))
            else:
                # Generate generic body from profile
                summary = user_profile.get('summary', '')
                if summary:
                    story.append(Paragraph(summary, self.styles['ResumeBody']))
                    story.append(Spacer(1, 0.15*inch))
            
            # Closing paragraph
            closing = ai_analysis.get('cover_letter_closing', '')
            if not closing:
                closing = (f"Thank you for considering my application. I look forward to the opportunity to discuss "
                          f"how my skills and experiences align with the needs of {company}.")
            story.append(Paragraph(closing, self.styles['ResumeBody']))
            story.append(Spacer(1, 0.3*inch))
            
            # Sign-off
            story.append(Paragraph("Sincerely,", self.styles['ResumeBody']))
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph(name, self.styles['ResumeBody']))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Cover letter generated successfully: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to generate cover letter: {str(e)}", exc_info=True)
            raise IOError(f"Cover letter generation failed: {str(e)}") from e


def main():
    """Test function for PDF generation."""
    # Sample test data
    user_profile = {
        'name': 'John Doe',
        'email': 'john.doe@email.com',
        'phone': '(555) 123-4567',
        'location': 'San Francisco, CA',
        'linkedin': 'linkedin.com/in/johndoe',
        'github': 'github.com/johndoe',
        'title': 'Senior Software Engineer',
        'years_of_experience': '5+',
        'summary': 'Passionate software engineer with expertise in building scalable web applications.',
        'skills': ['Python', 'JavaScript', 'React', 'Node.js', 'AWS', 'Docker', 'Kubernetes'],
        'experience': [
            {
                'company': 'Tech Corp',
                'role': 'Senior Software Engineer',
                'dates': '2020 - Present',
                'location': 'San Francisco, CA',
                'bullets': [
                    'Led development of microservices architecture',
                    'Improved system performance by 40%',
                    'Mentored junior developers'
                ]
            }
        ],
        'education': [
            {
                'degree': 'B.S. Computer Science',
                'school': 'University of California',
                'graduation_year': '2018',
                'gpa': '3.8'
            }
        ],
        'projects': [
            {
                'name': 'Open Source Contributor',
                'description': 'Active contributor to major Python libraries',
                'technologies': ['Python', 'Git', 'CI/CD']
            }
        ],
        'certifications': ['AWS Certified Solutions Architect', 'Certified Kubernetes Administrator']
    }
    
    ai_analysis = {
        'match_score': 'A',
        'confidence': 0.92,
        'matched_skills': ['Python', 'AWS', 'Docker', 'Kubernetes'],
        'tailored_summary': 'Results-driven Senior Software Engineer with 5+ years of experience specializing in cloud-native architectures and microservices. Proven track record of optimizing system performance and leading cross-functional teams.',
        'tailored_bullets': {
            '0': [
                'Architected and deployed microservices infrastructure using Docker and Kubernetes, reducing deployment time by 60%',
                'Optimized AWS cloud infrastructure resulting in 40% cost savings while improving system reliability',
                'Led a team of 5 engineers in developing scalable APIs serving 1M+ daily requests'
            ]
        },
        'recommendations': [
            'Strong expertise in required cloud technologies',
            'Proven leadership experience',
            'Track record of performance optimization'
        ],
        'cover_letter_opening': 'I am excited to apply for the Senior Software Engineer position at InnovateTech. Your company\'s commitment to cutting-edge cloud solutions aligns perfectly with my passion for building scalable, efficient systems.',
        'cover_letter_body': [
            'In my current role at Tech Corp, I have spearheaded the migration of legacy monolithic applications to containerized microservices, resulting in improved scalability and reduced operational costs.',
            'My expertise in AWS, Docker, and Kubernetes has enabled me to design and implement robust CI/CD pipelines that have accelerated our release cycle by 3x.'
        ],
        'cover_letter_closing': 'I am eager to bring my technical expertise and leadership skills to InnovateTech. Thank you for considering my application.'
    }
    
    job_details = {
        'company': 'InnovateTech',
        'role': 'Senior Software Engineer',
        'url': 'https://example.com/job/123'
    }
    
    # Test PDF generation
    generator = PDFGenerator()
    
    try:
        resume_path = generator.generate_resume(user_profile, ai_analysis, job_details)
        print(f"Resume generated: {resume_path}")
        
        cover_letter_path = generator.generate_cover_letter(user_profile, ai_analysis, job_details)
        print(f"Cover letter generated: {cover_letter_path}")
        
    except Exception as e:
        print(f"Error generating PDFs: {e}")


if __name__ == "__main__":
    main()
