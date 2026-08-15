"""
CV Parser — Extracts skills, experience, education, job titles, and contact info from resumes.
Supports PDF and DOCX formats.
"""
import os
import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional

from utils.time_utils import get_ist_time

import pdfplumber
from docx import Document


@dataclass
class CVProfile:
    email: str = ""
    phone: str = ""
    links: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)        # Technical Skills
    experience_years: int = 0
    job_titles: List[str] = field(default_factory=list)
    education: List[str] = field(default_factory=list)
    raw_text: str = ""
    summary: str = ""


# ── Dictionaries & Regex Patterns ──────────────────────────────────────────

TECHNICAL_SKILLS = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl",
    "dart", "lua", "haskell", "elixir", "clojure", "groovy", "objective-c", "shell", "bash",
    # Web Frameworks & Libraries
    "django", "flask", "fastapi", "spring boot", "springboot", "spring", "react", "react.js", "angular",
    "vue", "vue.js", "next.js", "nextjs", "node.js", "nodejs", "express",
    "express.js", "rails", "ruby on rails", "laravel", "asp.net", ".net",
    "svelte", "nuxt", "gatsby", "remix", "redux", "graphql", "jquery", "tailwind", "bootstrap",
    # Data, ML, & AI
    "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
    "scikit-learn", "pandas", "numpy", "nlp", "natural language processing",
    "computer vision", "opencv", "data science", "data analysis", "data engineering",
    "spark", "pyspark", "hadoop", "airflow", "mlops", "llm", "generative ai",
    "langchain", "hugging face", "transformers", "openai", "pinecone", "milvus", "qdrant",
    # Cloud & DevOps
    "aws", "amazon web services", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
    "terraform", "ansible", "jenkins", "ci/cd", "github actions", "gitlab ci",
    "cloudformation", "helm", "prometheus", "grafana", "datadog", "nginx", "apache",
    # Databases
    "sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "oracle", "sqlite", "neo4j", "firebase", "supabase",
    "mariadb", "cockroachdb", "snowflake", "bigquery", "redshift", "weaviate",
    # Tools & Platforms
    "git", "github", "gitlab", "bitbucket", "jira", "confluence", "linux",
    "unix", "rest", "rest api", "grpc", "microservices", "kafka",
    "rabbitmq", "celery", "redis", "websocket", "postman", "swagger", "oauth", "jwt",
    # Mobile
    "android", "ios", "react native", "flutter", "swiftui", "xamarin",
    # Practices
    "agile", "scrum", "devops", "sre", "system design", "api design", "test driven development", "tdd",
    "selenium", "cypress", "playwright", "jest", "pytest", "junit", "mocha",
    "power bi", "tableau", "looker", "figma",
}

EDUCATION_KEYWORDS = [
    r"b\.?tech", r"m\.?tech", r"b\.?e\.?", r"m\.?e\.?", r"b\.?sc", r"m\.?sc",
    r"b\.?ca", r"m\.?ca", r"mba", r"ph\.?d", r"bachelor", r"master", r"diploma",
    r"b\.?com", r"m\.?com", r"bba", r"pgdm", r"associate degree", r"high school",
    r"computer science", r"information technology", r"electronics",
    r"electrical engineering", r"mechanical engineering", r"university", r"institute", r"college",
]

JOB_TITLE_PATTERNS = [
    r"java\s+(?:developer|engineer|architect)",
    r"(?:senior|junior|lead|staff|principal)\s+java\s+(?:developer|engineer|architect)",
    r"software\s+(?:engineer|developer)",
    r"(?:senior|junior|lead|staff|principal)\s+(?:software\s+)?(?:engineer|developer)",
    r"back[\s-]?end\s+(?:developer|engineer)",
    r"data\s+(?:scientist|engineer|analyst)",
    r"ml\s+engineer",
    r"machine\s+learning\s+engineer",
    r"devops\s+engineer",
    r"cloud\s+engineer",
    r"sre|site\s+reliability\s+engineer",
    r"product\s+manager",
    r"project\s+manager",
    r"technical\s+lead",
    r"team\s+lead",
    r"architect",
    r"(?:qa|test)\s+(?:engineer|analyst|lead)",
    r"business\s+analyst",
    r"system\s+administrator",
    r"database\s+administrator",
    r"network\s+engineer",
    r"cyber\s*security\s+(?:analyst|engineer)",
    r"data\s+science\s+manager",
    r"engineering\s+manager",
    r"vp\s+of\s+engineering",
    r"chief\s+technology\s+officer",
    r"cto"
]

EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
PHONE_PATTERN = r"(?:(?:\+?([1-9]|[0-9][0-9]|[0-9][0-9][0-9])\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([0-9][1-9]|[0-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?"
LINK_PATTERN = r"(?:(?:https?|ftp):\/\/)?(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)"

# ── Extraction Functions ───────────────────────────────────────────────────

def _extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF file."""
    text_parts = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return "\n".join(text_parts)


def _extract_text_from_docx(file_path: str) -> str:
    """Extract all text from a DOCX file."""
    try:
        doc = Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return ""


def _extract_skills(text: str, skill_set: set) -> List[str]:
    """Find known skills mentioned in the text using strict word boundaries."""
    text_lower = text.lower()
    found = []
    for skill in skill_set:
        # Use negative lookbehind and lookahead to act as boundary markers
        # without failing on non-word characters at the edge of strings (like 'c++' or '.net')
        escaped_skill = re.escape(skill)
        pattern = rf"(?<!\w){escaped_skill}(?!\w)"
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(set(found))


def _extract_experience_years(text: str) -> int:
    """
    Estimate total years of experience from the CV text.
    First tries date ranges (e.g. Jan 2018 - Present).
    Falls back to explicitly stated "X years experience".
    """
    total_months = 0
    # Attempt 1: Date Range parsing
    # Look for patterns like "Jan 2018 - Dec 2020" or "Feb 2019 to Present"
    months = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    date_range_pattern = rf"(?i)\b{months}\s*(?:'?\d{{2,4}})\s*(?:-|to|–|—|)\s*(?:{months}\s*(?:'?\d{{2,4}})|present|current|now|date)\b"
    
    matches = re.findall(date_range_pattern, text)
    if matches:
        try:
            # We don't fully parse all dates into objects since formats vary wildly,
            # but we can look closely at 4-digit years found within those matches
            year_pattern = r"\b(199\d|20\d{2})\b"
            years = []
            has_present = False
            for m in matches:
                y = re.findall(year_pattern, m)
                years.extend([int(year) for year in y])
                if re.search(r"(?i)present|current|now|date", m):
                    has_present = True
                    
            if years:
                min_year = min(years)
                max_year = get_ist_time().year if has_present else max(years)
                if max_year > min_year:
                    return max_year - min_year
        except Exception:
            pass

    # Attempt 2: Explicit experience text parsing
    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
        r"experience\s*[:\-]?\s*(\d+)\+?\s*(?:years?|yrs?)",
        r"(\d+)\+?\s*(?:years?|yrs?)\s+in\s+",
    ]
    max_years = 0
    for pattern in patterns:
        exps = re.findall(pattern, text, re.IGNORECASE)
        for m in exps:
            try:
                max_years = max(max_years, int(m))
            except ValueError:
                pass
                
    return max_years


def _extract_education(text: str) -> List[str]:
    """Extract education qualifications and universities."""
    found = []
    # 1. Match specific degree patterns
    for pattern in EDUCATION_KEYWORDS:
        matches = re.findall(rf"\b{pattern}\b", text, re.IGNORECASE)
        found.extend(matches)
        
    # 2. Look for lines that look like university names
    uni_pattern = r"(?i).*\b(?:university|college|institute|academy|school of)\b.*"
    unis = re.findall(uni_pattern, text)
    # clean up the lines
    for u in unis:
        u = u.strip()
        if len(u) < 60: # Avoid grabbing whole paragraphs
            found.append(u)
            
    return sorted(set(m.strip().title() for m in found))


def _extract_job_titles(text: str) -> List[str]:
    """Extract job titles mentioned in the CV."""
    found = []
    for pattern in JOB_TITLE_PATTERNS:
        matches = re.findall(rf"\b{pattern}\b", text, re.IGNORECASE)
        found.extend(matches)
    return sorted(set(m.strip().title() for m in found))


def _extract_contact_info(text: str):
    """Extract email, phone, and links from text."""
    # Email
    emails = re.findall(EMAIL_PATTERN, text)
    email = emails[0] if emails else ""
    
    # Phone (simple heuristic to grab the first likely phone number)
    phones = re.findall(r"\+?[\d\s\-\(\)]{10,20}", text)
    # filter out likely dates or arbitrary numbers
    valid_phones = [p.strip() for p in phones if len(re.sub(r"\D", "", p)) >= 10]
    phone = valid_phones[0] if valid_phones else ""
    
    # Links
    all_links = re.findall(LINK_PATTERN, text)
    filtered_links = []
    for link in all_links:
        l = link.lower()
        if "linkedin.com" in l or "github.com" in l or "gitlab.com" in l or "portfolio" in l:
            # Clean trailing punctuation
            clean_link = re.sub(r"[.)\]}]+$", "", link)
            if clean_link not in filtered_links:
                filtered_links.append(clean_link)
                
    return email, phone, filtered_links


# ── Main Entry Point ───────────────────────────────────────────────────────

def parse_cv(file_path: str) -> CVProfile:
    """
    Parse a CV/resume file and extract structured profile data.

    Args:
        file_path: Path to the CV file (.pdf or .docx)

    Returns:
        CVProfile with extracted skills, experience, education, job titles, and contact info.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        raw_text = _extract_text_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        raw_text = _extract_text_from_docx(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use .pdf, .docx, or .txt")

    # If text extraction failed drastically
    if not raw_text.strip():
        return CVProfile(raw_text="[Could not extract text]")

    # 1. Core Profile Details
    tech_skills = _extract_skills(raw_text, TECHNICAL_SKILLS)
    experience_years = _extract_experience_years(raw_text)
    education = _extract_education(raw_text)
    job_titles = _extract_job_titles(raw_text)
    
    # 2. Contact Information
    email, phone, links = _extract_contact_info(raw_text)

    # 3. Build text summary for matching engine
    summary_parts = []
    if job_titles:
        summary_parts.append("Job Titles: " + ", ".join(job_titles))
    if tech_skills:
        summary_parts.append("Skills: " + ", ".join(tech_skills))
    if education:
        summary_parts.append("Education: " + ", ".join(education))
    
    # Include up to 2000 chars of raw text to give TF-IDF context
    summary_parts.append(raw_text[:2000])

    return CVProfile(
        email=email,
        phone=phone,
        links=links,
        skills=tech_skills,
        experience_years=experience_years,
        job_titles=job_titles,
        education=education,
        raw_text=raw_text,
        summary="\n".join(summary_parts),
    )
