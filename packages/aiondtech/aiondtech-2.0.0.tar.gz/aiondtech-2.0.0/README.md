# AiondTech Resume Analyser SDK

Official Python SDK for the [AiondTech Resume Analyser API](https://aiondtech.com).

[![PyPI version](https://badge.fury.io/py/aiondtech.svg)](https://badge.fury.io/py/aiondtech)
[![Python Versions](https://img.shields.io/pypi/pyversions/aiondtech.svg)](https://pypi.org/project/aiondtech/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install aiondtech
```

## Quick Start

```python
from aiondtech import ResumeAnalyser

# Initialize client
client = ResumeAnalyser(api_key="your-api-key")

# Or use environment variable
# export AIONDTECH_API_KEY="your-api-key"
client = ResumeAnalyser()

# Upload a resume (1 credit)
result = client.resumes.upload("resume.pdf")
print(f"Resume ID: {result.resume_id}")

# Upload and analyze (3 credits)
analysis = client.resumes.upload_and_analyze("resume.pdf")
print(f"Name: {analysis.full_name}")
print(f"Skills: {analysis.skills}")

# Create a job posting (1 credit)
job = client.jobs.create(
    title="Senior Python Developer",
    description="We are looking for an experienced Python developer..."
)
print(f"Job ID: {job.job_id}")

# Compare resume to job (3 credits)
comparison = client.matching.compare(
    resume_id=result.resume_id,
    job_id=job.job_id
)
print(f"Match Score: {comparison.comparison_score}%")
print(f"Reason: {comparison.comparison_reason}")

# Check credit balance (free)
balance = client.credits.balance()
print(f"Remaining: {balance['remaining_credits']}")
```

## API Endpoints

| Method | Endpoint | Credits | Description |
|--------|----------|---------|-------------|
| `resumes.upload()` | POST /external/upload-resume | 1 | Upload PDF |
| `resumes.upload_and_analyze()` | POST /external/upload-resume-analyze | 3 | Upload + AI parsing |
| `resumes.upload_analyze_compare()` | POST /external/upload-resume-analyze-compare | 5 | Upload + parse + compare |
| `resumes.analyze()` | POST /external/analyze-resume-by-id | 2 | Parse existing resume |
| `resumes.list()` | GET /external/list-resumes | 0 | List all resumes |
| `jobs.create()` | POST /external/create-job | 1 | Create job posting |
| `jobs.list()` | GET /external/list-jobs | 0 | List all jobs |
| `matching.compare()` | POST /external/compare-resumes | 3 | Compare resume to job |
| `credits.balance()` | GET /external/credits/balance | 0 | Check balance |
| `credits.usage()` | GET /external/credits/usage | 0 | View history |

## Detailed Examples

### Upload and Analyze Resume

```python
from aiondtech import ResumeAnalyser

client = ResumeAnalyser(api_key="your-api-key")

# Upload and get structured data
analysis = client.resumes.upload_and_analyze("john_doe_resume.pdf")

print(f"Name: {analysis.full_name}")
print(f"Email: {analysis.email}")
print(f"Skills: {', '.join(analysis.skills)}")
print(f"Experience: {analysis.total_experience}")
print(f"Job Titles: {', '.join(analysis.job_titles)}")

# Access raw parsed data
print(analysis.parsed_data)
```

### Full Recruitment Workflow

```python
from aiondtech import ResumeAnalyser

client = ResumeAnalyser(api_key="your-api-key")

# 1. Create a job posting
job = client.jobs.create(
    title="Senior Python Developer",
    description="""
    Requirements:
    - 5+ years Python experience
    - FastAPI or Django expertise
    - PostgreSQL knowledge
    - AWS experience preferred
    """
)

# 2. Upload and compare multiple resumes
resumes = ["candidate1.pdf", "candidate2.pdf", "candidate3.pdf"]
results = []

for resume_path in resumes:
    result = client.resumes.upload_analyze_compare(
        file_path=resume_path,
        job_id=job.job_id
    )
    results.append({
        "resume_id": result.resume_id,
        "name": result.parsed_data.get("full_name"),
        "score": result.comparison_score,
        "matched": result.matched_keywords,
        "missing": result.missing_keywords
    })

# 3. Rank candidates by score
ranked = sorted(results, key=lambda x: x["score"], reverse=True)

for i, candidate in enumerate(ranked, 1):
    print(f"{i}. {candidate['name']} - {candidate['score']}% match")
```

### Error Handling

```python
from aiondtech import (
    ResumeAnalyser,
    AuthenticationError,
    RateLimitError,
    InsufficientCreditsError,
    ValidationError,
    NotFoundError,
)

client = ResumeAnalyser(api_key="your-api-key")

try:
    result = client.resumes.upload_and_analyze("resume.pdf")
except AuthenticationError:
    print("Invalid API key")
except InsufficientCreditsError as e:
    print(f"Not enough credits. Remaining: {e.credits_remaining}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except ValidationError as e:
    print(f"Invalid input: {e.message}")
except NotFoundError:
    print("Resource not found")
```

### Using Environment Variables

```bash
# Set your API key
export AIONDTECH_API_KEY="your-api-key"

# Optional: Use production URL
export AIONDTECH_BASE_URL="https://api.aiondtech.com"
```

```python
from aiondtech import ResumeAnalyser

# Client automatically uses environment variables
client = ResumeAnalyser()
```

### Production vs Development

```python
from aiondtech import ResumeAnalyser

# Development (default)
client = ResumeAnalyser(api_key="your-key")
# Uses: https://api.dev.aiondtech.com

# Production
client = ResumeAnalyser(api_key="your-key", production=True)
# Uses: https://api.aiondtech.com

# Custom URL
client = ResumeAnalyser(api_key="your-key", base_url="https://custom.api.com")
```

## Response Models

All API responses are converted to typed Python objects:

```python
# ResumeUploadResult
result.resume_id      # int
result.message        # str
result.credits_used   # int

# ResumeAnalysisResult
analysis.resume_id    # int
analysis.parsed_data  # dict
analysis.full_name    # str (shortcut)
analysis.email        # str (shortcut)
analysis.skills       # List[str] (shortcut)

# ResumeComparisonResult
comparison.resume_id         # int
comparison.job_id            # int
comparison.comparison_score  # float (0-100)
comparison.comparison_reason # str
comparison.matched_keywords  # List[str]
comparison.missing_keywords  # List[str]
comparison.is_good_match     # bool (score >= 70)
comparison.match_level       # str ("excellent", "good", "fair", "poor")

# JobResult
job.job_id       # int
job.title        # str
job.description  # str
job.created_at   # str
```

## Rate Limits

| Tier | Per Minute | Per Day |
|------|------------|---------|
| Starter | 50 | 500 |
| Growth | 100 | 1,000 |
| Enterprise | 500 | Unlimited |

## Support

- **Documentation**: [https://docs.aiondtech.com](https://docs.aiondtech.com)
- **API Reference**: [https://api.aiondtech.com/docs](https://api.aiondtech.com/docs)
- **Email**: support@aiondtech.com
- **Issues**: [GitHub Issues](https://github.com/aiondtech/aiondtech-python/issues)

## License

MIT License - see [LICENSE](LICENSE) for details.
