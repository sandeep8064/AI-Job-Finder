"""
Configuration management for the Ai Job finder System.
Loads/saves settings from config.json with sensible defaults.
"""
import json
import os
from dataclasses import dataclass, field, asdict
from typing import List

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs.db"))


@dataclass
class EmailConfig:
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str = ""
    sender_password: str = ""  # Gmail App Password
    recipient_email: str = ""


@dataclass
class SearchConfig:
    keywords: List[str] = field(default_factory=lambda: ["java"])
    locations: List[str] = field(default_factory=lambda: ["India"])
    min_experience: int = 0
    max_experience: int = 10
    max_pages: int = 3
    target_companies: List[str] = field(default_factory=list)
    career_page_urls: List[str] = field(default_factory=list)


@dataclass
class NaukriConfig:
    naukri_user: str = ""
    naukri_password: str = ""


@dataclass
class TinyFishConfig:
    api_key: str = ""
    enabled: bool = True
    target_urls: List[str] = field(default_factory=lambda: [
        # Big 4 / Consulting
        "https://southasiacareers.deloitte.com/search/",
        "https://www.pwc.in/careers/experienced-jobs/results.html",
        "https://careers.ey.com/ey/search/",
        "https://ejgk.fa.em2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/jobs",
        
        # IT Services & Consulting
        "https://ibegin.tcsapps.com/candidate/jobs/search",
        "https://career.infosys.com/joblist",
        "https://careers.wipro.com/search/",
        "https://www.accenture.com/in-en/careers/jobsearch",
        "https://www.capgemini.com/in-en/careers/jobs/",
        "https://careers.cognizant.com/india-en/jobs",
        "https://careers.hcltech.com/search/",
        "https://www.ibm.com/in-en/careers/search",
        "https://careers.techmahindra.com/currentopportunity.aspx",
        "https://careers.ltimindtree.com/search/",
        "https://careers.genpact.com/search-results",
        "https://careers.nttdata.com/search/",
        "https://jobs.hexaware.com/search/",
        "https://careers.mphasis.com/home/jobs.html",
        "https://www.epam.com/careers/job-listings",
        "https://careers.publicissapient.com/job-search/",
        "https://www.virtusa.com/careers/job-search",
        "https://www.synechron.com/careers/jobs",



        # Banking
        "https://careers.hdfcbank.com/",
    ])
    browser_profile: str = "stealth"  # "lite" or "stealth"


@dataclass
class AgentConfig:
    email: EmailConfig = field(default_factory=EmailConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    naukri: NaukriConfig = field(default_factory=NaukriConfig)
    tinyfish: TinyFishConfig = field(default_factory=TinyFishConfig)
    scrape_interval_hours: int = 6
    match_threshold: float = 0.35
    rate_limit_seconds: float = 2.0
    cv_path: str = ""


def load_config() -> AgentConfig:
    """Load configuration from config.json or environment variables."""
    # Start with defaults
    config = AgentConfig()

    # Load from config.json if it exists
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        email_data = data.get("email", {})
        config.email.smtp_server = str(email_data.get("smtp_server", config.email.smtp_server))
        config.email.smtp_port = int(email_data.get("smtp_port", config.email.smtp_port))
        config.email.sender_email = str(email_data.get("sender_email", config.email.sender_email))
        config.email.sender_password = str(email_data.get("sender_password", config.email.sender_password))
        config.email.recipient_email = str(email_data.get("recipient_email", config.email.recipient_email))
        
        search_data = data.get("search", {})
        config.search.keywords = list(search_data.get("keywords", config.search.keywords))
        config.search.locations = list(search_data.get("locations", config.search.locations))
        config.search.min_experience = int(search_data.get("min_experience", config.search.min_experience))
        config.search.max_experience = int(search_data.get("max_experience", config.search.max_experience))
        config.search.max_pages = int(search_data.get("max_pages", config.search.max_pages))
        config.search.target_companies = list(search_data.get("target_companies", config.search.target_companies))
        config.search.career_page_urls = list(search_data.get("career_page_urls", config.search.career_page_urls))
        
        naukri_data = data.get("naukri", {})
        config.naukri.naukri_user = str(naukri_data.get("naukri_user", config.naukri.naukri_user))
        config.naukri.naukri_password = str(naukri_data.get("naukri_password", config.naukri.naukri_password))

        tinyfish_data = data.get("tinyfish", {})
        config.tinyfish.api_key = str(tinyfish_data.get("api_key", config.tinyfish.api_key))
        config.tinyfish.enabled = bool(tinyfish_data.get("enabled", config.tinyfish.enabled))
        config.tinyfish.target_urls = list(tinyfish_data.get("target_urls", config.tinyfish.target_urls))
        config.tinyfish.browser_profile = str(tinyfish_data.get("browser_profile", config.tinyfish.browser_profile))
        
        config.scrape_interval_hours = int(data.get("scrape_interval_hours", config.scrape_interval_hours))
        config.match_threshold = float(data.get("match_threshold", config.match_threshold))
        config.rate_limit_seconds = float(data.get("rate_limit_seconds", config.rate_limit_seconds))
        config.cv_path = str(data.get("cv_path", config.cv_path))

    # Override with Environment Variables (for Hosting)
    config.email.sender_email = os.getenv("EMAIL_SENDER", config.email.sender_email)
    config.email.sender_password = os.getenv("EMAIL_PASSWORD", config.email.sender_password)
    config.email.recipient_email = os.getenv("EMAIL_RECIPIENT", config.email.recipient_email)
    
    config.naukri.naukri_user = os.getenv("NAUKRI_USER", config.naukri.naukri_user)
    config.naukri.naukri_password = os.getenv("NAUKRI_PASSWORD", config.naukri.naukri_password)

    # TinyFish env override
    config.tinyfish.api_key = os.getenv("TINYFISH_API_KEY", config.tinyfish.api_key)
    
    env_cv_path = os.getenv("CV_PATH")
    if env_cv_path:
        config.cv_path = env_cv_path

    return config


def save_config(config: AgentConfig):
    """Save configuration to config.json."""
    os.makedirs(os.path.dirname(CONFIG_FILE) or ".", exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(asdict(config), f, indent=2)
