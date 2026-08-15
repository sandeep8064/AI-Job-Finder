"""
SQLite storage — Tracks seen jobs to avoid sending duplicate notifications.
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional

from utils.time_utils import get_ist_iso

from scrapers.base_scraper import JobListing


class JobDatabase:
    """SQLite database for tracking seen jobs and notification history."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS seen_jobs (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    url TEXT,
                    source TEXT,
                    score REAL DEFAULT 0.0,
                    first_seen TEXT,
                    notified INTEGER DEFAULT 0,
                    notified_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scrape_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    jobs_found INTEGER,
                    jobs_new INTEGER,
                    jobs_notified INTEGER
                )
            """)

    def _connect(self) -> sqlite3.Connection:
        """Create a database connection."""
        return sqlite3.connect(self.db_path)

    def is_new_job(self, job: JobListing) -> bool:
        """Check if a job has been seen before."""
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT id FROM seen_jobs WHERE id = ?",
                (job.unique_id,)
            )
            return cursor.fetchone() is None

    def was_notified(self, job: JobListing) -> bool:
        """Check if a job has already been notified in an email."""
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT notified FROM seen_jobs WHERE id = ? AND notified = 1",
                (job.unique_id,)
            )
            return cursor.fetchone() is not None

    def add_job(self, job: JobListing, score: float = 0.0):
        """Add a job to the seen jobs database."""
        with self._connect() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO seen_jobs (id, title, company, location, url, source, score, first_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.unique_id,
                job.title,
                job.company,
                job.location,
                job.url,
                job.source,
                score,
                get_ist_iso(),
            ))

    def mark_notified(self, job: JobListing):
        """Mark a job as notified."""
        with self._connect() as conn:
            conn.execute("""
                UPDATE seen_jobs SET notified = 1, notified_at = ?
                WHERE id = ?
            """, (get_ist_iso(), job.unique_id))

    def log_scrape_run(self, jobs_found: int, jobs_new: int, jobs_notified: int):
        """Log a scrape run for history."""
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO scrape_runs (timestamp, jobs_found, jobs_new, jobs_notified)
                VALUES (?, ?, ?, ?)
            """, (get_ist_iso(), jobs_found, jobs_new, jobs_notified))

    def get_recent_jobs(self, limit: int = 50, offset: int = 0) -> list:
        """Get recently seen jobs with their scores (paginated)."""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM seen_jobs
                ORDER BY first_seen DESC, score DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    def get_total_jobs_count(self) -> int:
        """Get the total number of jobs in the database."""
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM seen_jobs").fetchone()[0]

    def get_stats(self) -> dict:
        """Get database statistics."""
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM seen_jobs").fetchone()[0]
            notified = conn.execute("SELECT COUNT(*) FROM seen_jobs WHERE notified = 1").fetchone()[0]
            runs = conn.execute("SELECT COUNT(*) FROM scrape_runs").fetchone()[0]
            last_run = conn.execute(
                "SELECT timestamp FROM scrape_runs ORDER BY id DESC LIMIT 1"
            ).fetchone()
            return {
                "total_jobs_seen": total,
                "total_notified": notified,
                "total_runs": runs,
                "last_run": last_run[0] if last_run else "Never",
            }
