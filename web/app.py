"""
Flask Web Dashboard — Upload CV, view jobs, configure settings.
"""
import os
import json
from datetime import datetime

from utils.time_utils import get_ist_strftime

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from config import load_config, save_config, UPLOAD_DIR, DB_PATH
from cv_parser.parser import parse_cv
from storage.db import JobDatabase


def create_app():
    """Create and configure the Flask application."""
    # Determine template and static directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, "templates")

    app = Flask(__name__, template_folder=template_dir)
    app.secret_key = "job-agent-secret-key-change-in-production"

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Initial status
    SCRAPE_STATUS = {
        "status": "idle",
        "last_run": None,
        "message": "Ready"
    }

    @app.route("/api/status")
    def get_status():
        """Get the current scraping status."""
        return jsonify(SCRAPE_STATUS)

    def background_scrape(config):
        """Helper to run pipeline and update global status."""
        from main import run_pipeline
        nonlocal SCRAPE_STATUS
        SCRAPE_STATUS["status"] = "running"
        SCRAPE_STATUS["message"] = "Scraping in progress..."
        try:
            run_pipeline(config, False)
            SCRAPE_STATUS["status"] = "completed"
            SCRAPE_STATUS["last_run"] = get_ist_strftime("%H:%M:%S")
            SCRAPE_STATUS["message"] = f"Last run completed at {SCRAPE_STATUS['last_run']} IST"
        except Exception as e:
            SCRAPE_STATUS["status"] = "error"
            SCRAPE_STATUS["message"] = f"Error: {str(e)}"

    @app.route("/")
    def index():
        """Dashboard — show recent jobs, CV status, system stats."""
        page = request.args.get("page", 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page

        config = load_config()
        db = JobDatabase(DB_PATH)
        
        total_jobs = db.get_total_jobs_count()
        recent_jobs = db.get_recent_jobs(limit=per_page, offset=offset)
        stats = db.get_stats()
        
        total_pages = (total_jobs + per_page - 1) // per_page

        # Get CV info
        cv_info = None
        if config.cv_path and os.path.exists(config.cv_path):
            try:
                profile = parse_cv(config.cv_path)
                cv_info = {
                    "path": config.cv_path,
                    "email": getattr(profile, 'email', ''),
                    "phone": getattr(profile, 'phone', ''),
                    "links": getattr(profile, 'links', []),
                    "skills": getattr(profile, 'skills', []),
                    "experience_years": getattr(profile, 'experience_years', 0),
                    "job_titles": getattr(profile, 'job_titles', [])[:5],
                    "education": getattr(profile, 'education', [])[:5],
                }
            except Exception:
                cv_info = {"path": config.cv_path, "error": True}

        return render_template(
            "index.html",
            jobs=recent_jobs,
            stats=stats,
            cv_info=cv_info,
            config=config,
            page=page,
            total_pages=total_pages,
            total_jobs=total_jobs
        )

    @app.route("/upload", methods=["POST"])
    def upload_cv():
        """Handle CV file upload."""
        if "cv_file" not in request.files:
            flash("No file selected", "error")
            return redirect(url_for("index"))

        file = request.files["cv_file"]
        if file.filename == "":
            flash("No file selected", "error")
            return redirect(url_for("index"))

        # Check file extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in (".pdf", ".docx", ".doc", ".txt"):
            flash("Unsupported file format. Use PDF, DOCX, or TXT.", "error")
            return redirect(url_for("index"))

        # Save file
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        file.save(file_path)

        # Update config
        config = load_config()
        config.cv_path = file_path
        save_config(config)

        # Parse and validate
        try:
            profile = parse_cv(file_path)
            flash(
                f"CV uploaded! Found {len(profile.skills)} skills, "
                f"{profile.experience_years} years experience, "
                f"{len(profile.job_titles)} job titles.",
                "success",
            )
        except Exception as e:
            flash(f"CV uploaded but parsing failed: {e}", "warning")

        return redirect(url_for("index"))

    @app.route("/remove-cv", methods=["POST"])
    def remove_cv():
        """Remove the uploaded CV."""
        config = load_config()
        if config.cv_path and os.path.exists(config.cv_path):
            try:
                os.remove(config.cv_path)
            except Exception as e:
                flash(f"Error deleting file: {e}", "warning")
        
        config.cv_path = ""
        save_config(config)
        flash("CV removed successfully.", "success")
        return redirect(url_for("index"))

    @app.route("/jobs")
    def jobs():
        """View all scraped jobs."""
        db = JobDatabase(DB_PATH)
        recent_jobs = db.get_recent_jobs(limit=100)
        return jsonify(recent_jobs)

    @app.route("/run", methods=["POST"])
    def run_scrape():
        """Trigger a manual scrape run."""
        import threading
        
        config = load_config()
        if not config.cv_path:
            flash("Please upload a CV first!", "error")
            return redirect(url_for("index"))

        if SCRAPE_STATUS["status"] == "running":
            flash("Scrape already in progress!", "warning")
            return redirect(url_for("index"))

        # Run in background thread
        thread = threading.Thread(target=background_scrape, args=(config,))
        thread.daemon = True
        thread.start()

        flash("Scraping started!", "success")
        return redirect(url_for("index"))

    @app.route("/settings")
    def settings():
        """Show settings page."""
        config = load_config()
        return render_template("settings.html", config=config)

    @app.route("/settings", methods=["POST"])
    def save_settings():
        """Save settings from form."""
        config = load_config()

        # Email settings
        config.email.sender_email = request.form.get("sender_email", "").strip()
        config.email.sender_password = request.form.get("sender_password", "").strip()
        config.email.recipient_email = request.form.get("recipient_email", "").strip()
        config.email.smtp_server = request.form.get("smtp_server", "smtp.gmail.com").strip()
        try:
            config.email.smtp_port = int(request.form.get("smtp_port", "587"))
        except ValueError:
            config.email.smtp_port = 587

        # Search settings
        keywords_raw = request.form.get("keywords", "").strip()
        config.search.keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

        locations_raw = request.form.get("locations", "").strip()
        config.search.locations = [l.strip() for l in locations_raw.split(",") if l.strip()]

        career_urls_raw = request.form.get("career_page_urls", "").strip()
        config.search.career_page_urls = [u.strip() for u in career_urls_raw.split("\n") if u.strip()]

        try:
            config.search.max_pages = int(request.form.get("max_pages", "3"))
        except ValueError:
            config.search.max_pages = 3

        try:
            config.match_threshold = float(request.form.get("match_threshold", "0.15"))
        except ValueError:
            config.match_threshold = 0.15

        try:
            config.scrape_interval_hours = int(request.form.get("scrape_interval_hours", "6"))
        except ValueError:
            config.scrape_interval_hours = 6

        # Naukri settings
        config.naukri.naukri_user = request.form.get("naukri_user", "").strip()
        config.naukri.naukri_password = request.form.get("naukri_password", "").strip()

        # TinyFish settings
        config.tinyfish.api_key = request.form.get("tinyfish_api_key", "").strip()
        config.tinyfish.enabled = "tinyfish_enabled" in request.form
        tinyfish_urls_raw = request.form.get("tinyfish_target_urls", "").strip()
        config.tinyfish.target_urls = [u.strip() for u in tinyfish_urls_raw.split("\n") if u.strip()]
        config.tinyfish.browser_profile = request.form.get("tinyfish_browser_profile", "stealth").strip()

        save_config(config)
        flash("Settings saved successfully!", "success")
        return redirect(url_for("settings"))

    @app.route("/connect-naukri", methods=["POST"])
    def connect_naukri():
        """Quickly save Naukri credentials from the dashboard."""
        config = load_config()
        config.naukri.naukri_user = request.form.get("naukri_user", "").strip()
        config.naukri.naukri_password = request.form.get("naukri_password", "").strip()
        save_config(config)
        flash("Naukri account connected!", "success")
        return redirect(url_for("index"))

    return app
