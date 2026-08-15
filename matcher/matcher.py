"""
Job Matcher — Scores and ranks job listings against a CV profile.
Uses TF-IDF cosine similarity + keyword bonus scoring.
"""
from dataclasses import dataclass
import re
from typing import List

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


from cv_parser.parser import CVProfile
from scrapers.base_scraper import JobListing


@dataclass
class ScoredJob:
    job: JobListing
    score: float  # 0.0 to 1.0
    match_reasons: List[str]

    @property
    def score_pct(self) -> int:
        return int(self.score * 100)


def _build_job_text(job: JobListing) -> str:
    """Build a searchable text blob from a job listing."""
    parts = [
        job.title or "",
        job.description or "",
        job.company or "",
        job.location or "",
        " ".join(job.skills) if job.skills else "",
        job.experience or "",
    ]
    return " ".join(parts)


def _extract_job_experience_years(exp_str: str) -> tuple[int, int]:
    """Parse a job experience string (e.g. '2-5 Yrs', '3+ years', '5 Yrs') into min, max years."""
    if not exp_str:
        return 0, 99
        
    exp_str = exp_str.lower()
    
    # 1. Look for range: "2-5 Yrs", "2 to 5 years"
    range_match = re.search(r"(\d+)\s*(?:-|to)\s*(\d+)", exp_str)
    if range_match:
        return int(range_match.group(1)), int(range_match.group(2))
        
    # 2. Look for explicit requirements: "3+ years", "Min 3 yrs"
    num_match = re.search(r"(\d+)\+?\s*y", exp_str)
    if num_match:
        val = int(num_match.group(1))
        # Check if it means "up to" instead of "at least"
        if "up to" in exp_str or "max" in exp_str:
            return 0, val
        return val, 99
        
    return 0, 99


def match_jobs(
    cv_profile: CVProfile,
    jobs: List[JobListing],
    threshold: float = 0.15,
) -> List[ScoredJob]:
    """
    Score and rank jobs against a CV profile.

    Uses:
    1. TF-IDF cosine similarity between CV summary and job text
    2. Bonus scoring for skill keyword matches
    3. Bonus scoring for matching job titles
    4. Bonus for location preference matches

    Args:
        cv_profile: Parsed CV profile
        jobs: List of job listings to score
        threshold: Minimum score to include (0.0-1.0)

    Returns:
        Sorted list of ScoredJob (highest score first)
    """
    if not jobs:
        return []

    cv_text = cv_profile.summary
    job_texts = [_build_job_text(job) for job in jobs]

    # ── TF-IDF Cosine Similarity ─────────────────────────────────────────
    all_texts = [cv_text] + job_texts
    try:
        if HAS_SKLEARN:
            vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=5000,
                ngram_range=(1, 2),
            )
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            cv_vector = tfidf_matrix[0:1]
            job_vectors = tfidf_matrix[1:]
            similarities = cosine_similarity(cv_vector, job_vectors)[0]
        else:
            similarities = [0.0] * len(jobs)
    except Exception:
        # Fallback if TF-IDF fails (e.g. empty texts)
        similarities = [0.0] * len(jobs)

    # ── Score each job ───────────────────────────────────────────────────
    scored_jobs = []
    cv_skills_lower = {s.lower() for s in cv_profile.skills}
    cv_titles_lower = {t.lower() for t in cv_profile.job_titles}

    for i, job in enumerate(jobs):
        score = similarities[i]
        reasons = []

        # Skill match bonus
        job_text_lower = _build_job_text(job).lower()
        skill_matches = [s for s in cv_skills_lower if s in job_text_lower]
        if skill_matches:
            skill_bonus = min(len(skill_matches) * 0.03, 0.30)  # up to 30% bonus
            score += skill_bonus
            reasons.append(f"Skills match: {', '.join(skill_matches[:5])}")

        # Job title match bonus
        title_lower = job.title.lower()
        title_matches = [t for t in cv_titles_lower if t.lower() in title_lower]
        if title_matches:
            score += 0.15
            reasons.append(f"Title match: {', '.join(title_matches[:3])}")
            
        # Extra boost for exact Java/Backend profile alignment
        if "java" in title_lower or "backend" in title_lower:
            score += 0.10
            reasons.append("High Profile Alignment (Java/Backend)")


        # Location preference bonus (Mumbai gets slight priority)
        if job.location and "mumbai" in job.location.lower():
            score += 0.05
            reasons.append("Location Preference (Mumbai)")

        # Experience Match Logic
        if job.experience:
            min_y, max_y = _extract_job_experience_years(job.experience)
            user_exp = cv_profile.experience_years
            
            # STRICT FILTER: The user specifically requested jobs in the 1-4 year range.
            # Discard jobs requiring 5+ years or explicitly targeting only freshers (<1 year)
            if min_y > 4 or max_y < 1:
                continue
            
            # If user falls perfectly in the requested range
            if min_y <= user_exp <= max_y and max_y != 99:
                score += 0.20
                reasons.append(f"Exp match ({user_exp} yrs in {min_y}-{max_y} range)")
            elif min_y <= user_exp:
                score += 0.10
                reasons.append(f"Exp match (meets min {min_y} yrs)")
            elif user_exp < min_y:
                # Penalty: user lacks experience
                shortfall = min_y - user_exp
                if shortfall >= 2:
                    # Huge penalty for wanting Senior level (e.g. asks for 5, user has 3)
                    score -= 0.50
                    reasons.append(f"Exp penalty (requires {min_y} yrs, has {user_exp})")
                else:
                    score -= 0.15
                    reasons.append(f"Exp penalty (slightly under {min_y} yrs)")

        # Cap score between 0.0 and 1.0 (some penalties might push it below 0)
        score = max(0.0, min(score, 1.0))

        if not reasons:
            reasons.append("Content similarity")

        if score >= threshold:
            scored_jobs.append(ScoredJob(job=job, score=score, match_reasons=reasons))

    # Sort by score descending
    scored_jobs.sort(key=lambda x: x.score, reverse=True)
    return scored_jobs
