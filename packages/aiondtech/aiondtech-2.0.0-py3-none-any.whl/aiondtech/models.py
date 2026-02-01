"""
Data models and exceptions for the AiondTech SDK v2.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============================================================================
# EXCEPTIONS
# ============================================================================

class APIError(Exception):
    """Base exception for all API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.response = response or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(APIError):
    """Raised when API key is invalid or missing."""
    pass


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        self.retry_after = retry_after
        super().__init__(message, **kwargs)


class ValidationError(APIError):
    """Raised when request validation fails."""
    pass


class NotFoundError(APIError):
    """Raised when a resource is not found."""
    pass


class InsufficientCreditsError(APIError):
    """Raised when user has insufficient API credits."""
    
    def __init__(
        self,
        message: str = "Insufficient API credits",
        credits_remaining: int = 0,
        credits_required: int = 0,
        **kwargs
    ):
        self.credits_remaining = credits_remaining
        self.credits_required = credits_required
        super().__init__(message, **kwargs)


# ============================================================================
# RESPONSE MODELS
# ============================================================================

@dataclass
class ResumeUploadResult:
    """Result from uploading a resume (upload only, no parsing)."""
    resume_id: int
    message: str
    credits_used: int = 1
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> "ResumeUploadResult":
        return cls(
            resume_id=data.get("resume_id"),
            message=data.get("message", "Resume uploaded successfully"),
            credits_used=data.get("credits_used", 1),
            _raw=data
        )
    
    def __repr__(self):
        return f"<ResumeUploadResult resume_id={self.resume_id}>"


@dataclass
class ResumeAnalysisResult:
    """Result from uploading and analyzing a resume."""
    resume_id: int
    parsed_data: Dict[str, Any]
    credits_used: int = 3
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> "ResumeAnalysisResult":
        return cls(
            resume_id=data.get("resume_id"),
            parsed_data=data.get("parsed_data", {}),
            credits_used=data.get("credits_used", 3),
            _raw=data
        )
    
    @property
    def full_name(self) -> Optional[str]:
        return self.parsed_data.get("full_name")
    
    @property
    def email(self) -> Optional[str]:
        return self.parsed_data.get("email")
    
    @property
    def skills(self) -> List[str]:
        skills = self.parsed_data.get("skills", [])
        if isinstance(skills, str):
            return [s.strip() for s in skills.split(",") if s.strip()]
        return skills or []
    
    @property
    def job_titles(self) -> List[str]:
        titles = self.parsed_data.get("job_titles", [])
        if isinstance(titles, str):
            return [t.strip() for t in titles.split(",") if t.strip()]
        return titles or []
    
    @property
    def total_experience(self) -> Optional[str]:
        return self.parsed_data.get("total_experience")
    
    def __repr__(self):
        name = self.full_name or "Unknown"
        return f"<ResumeAnalysisResult resume_id={self.resume_id} name='{name}'>"


@dataclass
class ResumeComparisonResult:
    """Result from comparing a resume to a job posting."""
    resume_id: int
    job_id: int
    comparison_score: float
    comparison_reason: str
    parsed_data: Optional[Dict[str, Any]] = None
    matched_keywords: List[str] = field(default_factory=list)
    missing_keywords: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    credits_used: int = 3
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> "ResumeComparisonResult":
        return cls(
            resume_id=data.get("resume_id"),
            job_id=data.get("job_id"),
            comparison_score=data.get("comparison_score", 0) or data.get("ats_score", 0),
            comparison_reason=data.get("comparison_reason", "") or data.get("reason", ""),
            parsed_data=data.get("parsed_data"),
            matched_keywords=data.get("matched_keywords", []),
            missing_keywords=data.get("missing_keywords", []),
            suggestions=data.get("suggestions", []),
            credits_used=data.get("credits_used", 3),
            _raw=data
        )
    
    @property
    def is_good_match(self) -> bool:
        """Returns True if score is 70% or higher."""
        return self.comparison_score >= 70
    
    @property
    def match_level(self) -> str:
        """Returns match level: 'excellent', 'good', 'fair', 'poor'."""
        if self.comparison_score >= 85:
            return "excellent"
        elif self.comparison_score >= 70:
            return "good"
        elif self.comparison_score >= 50:
            return "fair"
        return "poor"
    
    def __repr__(self):
        return f"<ResumeComparisonResult resume_id={self.resume_id} score={self.comparison_score}%>"


@dataclass
class JobResult:
    """Result from creating a job posting."""
    job_id: int
    title: str
    description: str
    created_by: str
    created_at: Optional[str] = None
    credits_used: int = 1
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> "JobResult":
        return cls(
            job_id=data.get("job_id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            created_by=data.get("created_by", ""),
            created_at=data.get("created_at"),
            credits_used=data.get("credits_used", 1),
            _raw=data
        )
    
    def __repr__(self):
        return f"<JobResult job_id={self.job_id} title='{self.title}'>"


@dataclass
class ParsedResumeResult:
    """Result from parsing/analyzing a resume by ID."""
    resume_id: int
    partner: str
    parsed_data: Dict[str, Any]
    credits_used: int = 2
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> "ParsedResumeResult":
        return cls(
            resume_id=data.get("resume_id"),
            partner=data.get("partner", ""),
            parsed_data=data.get("parsed_data", {}),
            credits_used=data.get("credits_used", 2),
            _raw=data
        )
    
    @property
    def full_name(self) -> Optional[str]:
        return self.parsed_data.get("full_name")
    
    @property
    def email(self) -> Optional[str]:
        return self.parsed_data.get("email")
    
    @property
    def phone(self) -> Optional[str]:
        return self.parsed_data.get("contact_number")
    
    @property
    def linkedin(self) -> Optional[str]:
        return self.parsed_data.get("linkedin")
    
    @property
    def location(self) -> Optional[str]:
        return self.parsed_data.get("location")
    
    @property
    def skills(self) -> List[str]:
        skills = self.parsed_data.get("skills", [])
        if isinstance(skills, str):
            return [s.strip() for s in skills.split(",") if s.strip()]
        return skills or []
    
    @property
    def job_titles(self) -> List[str]:
        titles = self.parsed_data.get("job_titles", [])
        if isinstance(titles, str):
            return [t.strip() for t in titles.split(",") if t.strip()]
        return titles or []
    
    @property
    def companies(self) -> List[str]:
        companies = self.parsed_data.get("companies", [])
        if isinstance(companies, str):
            return [c.strip() for c in companies.split(",") if c.strip()]
        return companies or []
    
    @property
    def education(self) -> List[str]:
        edu = self.parsed_data.get("education", [])
        if isinstance(edu, str):
            return [e.strip() for e in edu.split(",") if e.strip()]
        return edu or []
    
    @property
    def total_experience(self) -> Optional[str]:
        return self.parsed_data.get("total_experience")
    
    @property
    def certifications(self) -> List[str]:
        certs = self.parsed_data.get("certifications", [])
        if isinstance(certs, str):
            return [c.strip() for c in certs.split(",") if c.strip()]
        return certs or []
    
    def __repr__(self):
        name = self.full_name or "Unknown"
        return f"<ParsedResumeResult resume_id={self.resume_id} name='{name}'>"


@dataclass
class ResumeListItem:
    """Single resume in a list."""
    id: int
    filename: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    uploaded_at: Optional[str] = None
    is_parsed: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResumeListItem":
        return cls(
            id=data.get("id"),
            filename=data.get("filename", ""),
            full_name=data.get("full_name"),
            email=data.get("email"),
            uploaded_at=data.get("uploaded_at"),
            is_parsed=data.get("is_parsed", False)
        )


@dataclass
class ResumeListResult:
    """Result from listing resumes."""
    resumes: List[Dict[str, Any]]
    total: int
    page: int
    limit: int
    has_more: bool
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> "ResumeListResult":
        return cls(
            resumes=data.get("resumes", []),
            total=data.get("total", 0),
            page=data.get("page", 1),
            limit=data.get("limit", 50),
            has_more=data.get("has_more", False),
            _raw=data
        )
    
    def __len__(self):
        return len(self.resumes)
    
    def __iter__(self):
        return iter(self.resumes)
    
    def __repr__(self):
        return f"<ResumeListResult count={len(self.resumes)} total={self.total}>"


@dataclass
class JobListItem:
    """Single job in a list."""
    id: int
    title: str
    description: str
    created_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobListItem":
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            created_at=data.get("created_at")
        )


@dataclass
class JobListResult:
    """Result from listing jobs."""
    jobs: List[Dict[str, Any]]
    total: int
    page: int
    limit: int
    has_more: bool
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> "JobListResult":
        return cls(
            jobs=data.get("jobs", []),
            total=data.get("total", 0),
            page=data.get("page", 1),
            limit=data.get("limit", 50),
            has_more=data.get("has_more", False),
            _raw=data
        )
    
    def __len__(self):
        return len(self.jobs)
    
    def __iter__(self):
        return iter(self.jobs)
    
    def __repr__(self):
        return f"<JobListResult count={len(self.jobs)} total={self.total}>"


@dataclass
class CreditBalance:
    """Credit balance information."""
    total: int
    used_mtd: int
    remaining: int
    plan_name: str
    resets_at: Optional[str] = None
    
    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> "CreditBalance":
        return cls(
            total=data.get("total", 0),
            used_mtd=data.get("used_mtd", 0),
            remaining=data.get("remaining", 0),
            plan_name=data.get("plan_name", ""),
            resets_at=data.get("resets_at")
        )
