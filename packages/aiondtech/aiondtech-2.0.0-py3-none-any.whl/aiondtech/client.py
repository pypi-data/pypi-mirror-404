"""
AiondTech Resume Analyser API Client - Updated Version

This is the main entry point for interacting with the API.
Supports all external endpoints with credit tracking.

Endpoints:
    - resumes.upload() - Upload resume, get ID
    - resumes.upload_and_analyze() - Upload + parse
    - resumes.upload_analyze_compare() - Upload + parse + compare to job
    - resumes.analyze() - Parse existing resume by ID
    - resumes.list() - List all uploaded resumes
    - jobs.create() - Create job posting
    - jobs.list() - List all jobs
    - matching.compare() - Compare resume to job
"""

import os
import mimetypes
from typing import Optional, Dict, Any, List, Union
from urllib.parse import urljoin

import requests

from .models import (
    ResumeUploadResult,
    ResumeAnalysisResult,
    ResumeComparisonResult,
    JobResult,
    ResumeListResult,
    JobListResult,
    ParsedResumeResult,
    APIError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    InsufficientCreditsError,
)


# Default API base URLs
DEFAULT_BASE_URL = "https://api.dev.aiondtech.com"
PRODUCTION_BASE_URL = "https://api.aiondtech.com"


class HTTPClient:
    """Low-level HTTP client for API requests."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: int = 120,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "aiondtech-python/2.0.0",
            "X-API-Key": api_key,
        })
    
    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Any:
        """Make an HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                data=data,
                json=json_data,
                files=files,
                params=params,
                timeout=self.timeout,
            )
            
            return self._handle_response(response)
            
        except requests.exceptions.Timeout:
            raise APIError("Request timed out", status_code=408)
        except requests.exceptions.ConnectionError:
            raise APIError("Failed to connect to API server")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
    
    def _handle_response(self, response: requests.Response) -> Any:
        """Handle API response and raise appropriate exceptions."""
        
        # Try to parse JSON response
        try:
            data = response.json()
        except ValueError:
            data = {"detail": response.text}
        
        # Handle error responses
        if response.status_code == 401:
            raise AuthenticationError(
                data.get("detail", "Invalid API key"),
                status_code=401,
                response=data
            )
        
        if response.status_code == 403:
            detail = data.get("detail", "")
            if "credit" in detail.lower():
                raise InsufficientCreditsError(
                    detail or "Insufficient API credits",
                    status_code=403,
                    response=data
                )
            raise AuthenticationError(
                detail or "Invalid or inactive API key",
                status_code=403,
                response=data
            )
        
        if response.status_code == 404:
            raise NotFoundError(
                data.get("detail", "Resource not found"),
                status_code=404,
                response=data
            )
        
        if response.status_code == 422:
            raise ValidationError(
                data.get("detail", "Validation error"),
                status_code=422,
                response=data
            )
        
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                data.get("detail", "Rate limit exceeded"),
                retry_after=int(retry_after) if retry_after else None,
                status_code=429,
                response=data
            )
        
        if response.status_code >= 500:
            raise APIError(
                data.get("detail", "Server error"),
                status_code=response.status_code,
                response=data
            )
        
        if response.status_code >= 400:
            raise APIError(
                data.get("detail", f"Request failed with status {response.status_code}"),
                status_code=response.status_code,
                response=data
            )
        
        return data


class Resumes:
    """
    Resume operations.
    
    Usage:
        client.resumes.upload("resume.pdf")
        client.resumes.upload_and_analyze("resume.pdf")
        client.resumes.upload_analyze_compare("resume.pdf", job_id=123)
        client.resumes.analyze(resume_id=123)
        client.resumes.list()
    """
    
    def __init__(self, client: HTTPClient):
        self._client = client
    
    def upload(self, file_path: str) -> ResumeUploadResult:
        """
        Upload a resume file (PDF only).
        
        Credits: 1 API credit
        
        Args:
            file_path: Path to the resume file (PDF)
        
        Returns:
            ResumeUploadResult with resume_id
        
        Example:
            result = client.resumes.upload("path/to/resume.pdf")
            print(f"Uploaded resume ID: {result.resume_id}")
        """
        self._validate_file(file_path)
        
        mime_type = mimetypes.guess_type(file_path)[0] or "application/pdf"
        filename = os.path.basename(file_path)
        
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, mime_type)}
            data = self._client.request("POST", "/external/upload-resume", files=files)
        
        return ResumeUploadResult.from_response(data)
    
    def upload_and_analyze(self, file_path: str) -> ResumeAnalysisResult:
        """
        Upload a resume and parse/extract structured data.
        
        Credits: 3 API credits (includes AI parsing)
        
        Args:
            file_path: Path to the resume file (PDF)
        
        Returns:
            ResumeAnalysisResult with resume_id and parsed_data
        
        Example:
            result = client.resumes.upload_and_analyze("resume.pdf")
            print(f"Name: {result.parsed_data.get('full_name')}")
            print(f"Skills: {result.parsed_data.get('skills')}")
        """
        self._validate_file(file_path)
        
        mime_type = mimetypes.guess_type(file_path)[0] or "application/pdf"
        filename = os.path.basename(file_path)
        
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, mime_type)}
            data = self._client.request(
                "POST",
                "/external/upload-resume-analyze",
                files=files
            )
        
        return ResumeAnalysisResult.from_response(data)
    
    def upload_analyze_compare(
        self,
        file_path: str,
        job_id: int
    ) -> ResumeComparisonResult:
        """
        Upload, parse, and compare resume against a job posting.
        
        Credits: 5 API credits (includes AI parsing + comparison)
        
        Args:
            file_path: Path to the resume file (PDF)
            job_id: ID of the job posting to compare against
        
        Returns:
            ResumeComparisonResult with resume_id, parsed_data, score, and reason
        
        Example:
            result = client.resumes.upload_analyze_compare("resume.pdf", job_id=42)
            print(f"Match Score: {result.comparison_score}%")
            print(f"Reason: {result.comparison_reason}")
        """
        self._validate_file(file_path)
        
        mime_type = mimetypes.guess_type(file_path)[0] or "application/pdf"
        filename = os.path.basename(file_path)
        
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, mime_type)}
            form_data = {"job_id": str(job_id)}
            data = self._client.request(
                "POST",
                "/external/upload-resume-analyze-compare",
                files=files,
                data=form_data
            )
        
        return ResumeComparisonResult.from_response(data)
    
    def analyze(self, resume_id: int) -> ParsedResumeResult:
        """
        Parse and extract structured data from an existing resume.
        
        Credits: 2 API credits (AI parsing only)
        
        Args:
            resume_id: ID of the uploaded resume
        
        Returns:
            ParsedResumeResult with extracted fields
        
        Example:
            parsed = client.resumes.analyze(resume_id=123)
            print(f"Name: {parsed.full_name}")
            print(f"Skills: {parsed.skills}")
        """
        data = self._client.request(
            "POST",
            "/external/analyze-resume-by-id",
            params={"resume_id": resume_id}
        )
        return ParsedResumeResult.from_response(data)
    
    def list(
        self,
        page: int = 1,
        limit: int = 50
    ) -> ResumeListResult:
        """
        List all uploaded resumes for this API key.
        
        Credits: 0 (free)
        
        Args:
            page: Page number (default: 1)
            limit: Items per page (default: 50, max: 100)
        
        Returns:
            ResumeListResult with list of resumes and pagination
        
        Example:
            result = client.resumes.list()
            for resume in result.resumes:
                print(f"ID: {resume['id']}, Name: {resume.get('full_name')}")
        """
        data = self._client.request(
            "GET",
            "/external/list-resumes",
            params={"page": page, "limit": min(limit, 100)}
        )
        return ResumeListResult.from_response(data)
    
    def _validate_file(self, file_path: str) -> None:
        """Validate file exists and is PDF."""
        if not os.path.exists(file_path):
            raise ValidationError(f"File not found: {file_path}")
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext != ".pdf":
            raise ValidationError(
                f"Invalid file type: {ext}. Only PDF files are supported."
            )


class Jobs:
    """
    Job posting operations.
    
    Usage:
        client.jobs.create("Python Developer", "Job description...")
        client.jobs.list()
    """
    
    def __init__(self, client: HTTPClient):
        self._client = client
    
    def create(self, title: str, description: str) -> JobResult:
        """
        Create a new job posting.
        
        Credits: 1 API credit
        
        Args:
            title: Job title
            description: Full job description
        
        Returns:
            JobResult with job_id
        
        Example:
            job = client.jobs.create(
                title="Senior Python Developer",
                description="We are looking for..."
            )
            print(f"Created job ID: {job.job_id}")
        """
        form_data = {
            "title": title,
            "description": description
        }
        data = self._client.request("POST", "/external/create-job", data=form_data)
        return JobResult.from_response(data)
    
    def list(
        self,
        page: int = 1,
        limit: int = 50
    ) -> JobListResult:
        """
        List all job postings for this API key.
        
        Credits: 0 (free)
        
        Args:
            page: Page number (default: 1)
            limit: Items per page (default: 50, max: 100)
        
        Returns:
            JobListResult with list of jobs and pagination
        
        Example:
            result = client.jobs.list()
            for job in result.jobs:
                print(f"ID: {job['id']}, Title: {job['title']}")
        """
        data = self._client.request(
            "GET",
            "/external/list-jobs",
            params={"page": page, "limit": min(limit, 100)}
        )
        return JobListResult.from_response(data)


class Matching:
    """
    Resume-job matching/comparison operations.
    
    Usage:
        client.matching.compare(resume_id=123, job_id=456)
    """
    
    def __init__(self, client: HTTPClient):
        self._client = client
    
    def compare(
        self,
        resume_id: int,
        job_id: int
    ) -> ResumeComparisonResult:
        """
        Compare a resume against a job posting.
        
        Credits: 3 API credits (AI comparison)
        
        Args:
            resume_id: ID of the uploaded resume
            job_id: ID of the job posting
        
        Returns:
            ResumeComparisonResult with score and reasoning
        
        Example:
            result = client.matching.compare(resume_id=123, job_id=456)
            print(f"Match Score: {result.comparison_score}%")
            print(f"Reasoning: {result.comparison_reason}")
        """
        payload = {
            "resume_id": resume_id,
            "job_id": job_id
        }
        data = self._client.request(
            "POST",
            "/external/compare-resumes",
            json_data=payload
        )
        return ResumeComparisonResult.from_response(data)


class Credits:
    """
    Credit balance and usage operations.
    
    Usage:
        client.credits.balance()
        client.credits.usage()
    """
    
    def __init__(self, client: HTTPClient):
        self._client = client
    
    def balance(self) -> Dict[str, Any]:
        """
        Get current credit balance.
        
        Returns:
            Dictionary with credit balance info
        
        Example:
            balance = client.credits.balance()
            print(f"Remaining: {balance['remaining']}")
            print(f"Used this month: {balance['used_mtd']}")
        """
        data = self._client.request("GET", "/external/credits/balance")
        return data
    
    def usage(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get detailed usage history.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Dictionary with usage details
        
        Example:
            usage = client.credits.usage()
            for entry in usage['history']:
                print(f"{entry['endpoint']}: {entry['credits']} credits")
        """
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        data = self._client.request("GET", "/external/credits/usage", params=params)
        return data


class ResumeAnalyser:
    """
    AiondTech Resume Analyser API Client.
    
    This is the main entry point for interacting with the API.
    
    Args:
        api_key: Your API key. Can also be set via AIONDTECH_API_KEY env var.
        base_url: API base URL. Defaults to https://api.dev.aiondtech.com
        timeout: Request timeout in seconds. Default 120.
        production: If True, use production URL (https://api.aiondtech.com)
    
    Example:
        from aiondtech import ResumeAnalyser
        
        # Initialize client
        client = ResumeAnalyser(api_key="your-api-key")
        
        # Or use environment variable
        # export AIONDTECH_API_KEY="your-api-key"
        client = ResumeAnalyser()
        
        # Upload resume
        result = client.resumes.upload("resume.pdf")
        
        # Upload and analyze
        analysis = client.resumes.upload_and_analyze("resume.pdf")
        
        # Create job posting
        job = client.jobs.create("Title", "Description")
        
        # Compare resume to job
        comparison = client.matching.compare(
            resume_id=result.resume_id,
            job_id=job.job_id
        )
        
        # Check credits
        balance = client.credits.balance()
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 120,
        production: bool = False,
    ):
        # Get API key from argument or environment
        self.api_key = api_key or os.getenv("AIONDTECH_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key is required. Pass api_key argument or set AIONDTECH_API_KEY environment variable."
            )
        
        # Get base URL
        if base_url:
            self.base_url = base_url
        elif production:
            self.base_url = PRODUCTION_BASE_URL
        else:
            self.base_url = os.getenv("AIONDTECH_BASE_URL") or DEFAULT_BASE_URL
        
        # Initialize HTTP client
        self._client = HTTPClient(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=timeout,
        )
        
        # Initialize resource classes
        self.resumes = Resumes(self._client)
        self.jobs = Jobs(self._client)
        self.matching = Matching(self._client)
        self.credits = Credits(self._client)
    
    def __repr__(self):
        masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}" if len(self.api_key) > 12 else "***"
        return f"<ResumeAnalyser base_url='{self.base_url}' api_key='{masked_key}'>"


# Alias for convenience
Client = ResumeAnalyser
