"""
AiondTech Resume Analyser API - Python SDK v2.0

A Python client library for the AiondTech Resume Analyser API.
Provides resume parsing, analysis, and job matching capabilities.

Quick Start:
    from aiondtech import ResumeAnalyser
    
    client = ResumeAnalyser(api_key="your-api-key")
    
    # Upload a resume
    result = client.resumes.upload("resume.pdf")
    print(f"Resume ID: {result.resume_id}")
    
    # Upload and analyze
    analysis = client.resumes.upload_and_analyze("resume.pdf")
    print(f"Name: {analysis.full_name}")
    print(f"Skills: {analysis.skills}")
    
    # Create job and compare
    job = client.jobs.create("Developer", "Python required...")
    comparison = client.matching.compare(
        resume_id=result.resume_id,
        job_id=job.job_id
    )
    print(f"Match Score: {comparison.comparison_score}%")

Environment Variables:
    AIONDTECH_API_KEY: Your API key
    AIONDTECH_BASE_URL: Custom API URL (default: https://api.dev.aiondtech.com)
"""

__version__ = "2.0.0"
__author__ = "AiondTech"

from .client import ResumeAnalyser, Client
from .models import (
    # Response models
    ResumeUploadResult,
    ResumeAnalysisResult,
    ResumeComparisonResult,
    JobResult,
    ParsedResumeResult,
    ResumeListResult,
    JobListResult,
    CreditBalance,
    # Exceptions
    APIError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    InsufficientCreditsError,
)

__all__ = [
    # Client
    "ResumeAnalyser",
    "Client",
    # Response models
    "ResumeUploadResult",
    "ResumeAnalysisResult",
    "ResumeComparisonResult",
    "JobResult",
    "ParsedResumeResult",
    "ResumeListResult",
    "JobListResult",
    "CreditBalance",
    # Exceptions
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "NotFoundError",
    "InsufficientCreditsError",
    # Version
    "__version__",
]
