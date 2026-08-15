# 🚀 AI-Job-Finder

An automated AI-powered job hunter, resume matcher, and notification agent. It automatically scrapes top IT and consulting career portals, matches openings against your resume profile, and delivers formatted email alerts.

Runs locally, on servers, or **100% free on GitHub Actions** without needing dedicated hosting!

---

## 🌟 Features

- **Multi-Source Scraping**: Scrapes career sites (TCS, Infosys, Wipro, Cognizant, Accenture, Deloitte, PwC, EY, etc.) and job boards using Playwright and BeautifulSoup.
- **Smart Resume Parsing**: Extracts skills, domain keywords, and experience levels from PDF & DOCX resumes.
- **Automated Matching Engine**: Calculates relevance score against your profile, filtering foreign listings and non-matching roles.
- **Email Notifications**: Dispatches instant or scheduled HTML email digests with direct job links.
- **Interactive Web Dashboard**: Local Flask UI to view discovered jobs, upload new resumes, and configure search criteria.
- **Serverless GitHub Actions Automation**: Scheduled cron job that scrapes in the cloud every 6 hours and updates history automatically.

---

## ⚡ 100% Free Automated Hosting via GitHub Actions

You don't need to keep your computer running or pay for a server!

### 1. Fork & Clone
1. Click **Fork** at the top right of this repository.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/AI-Job-Finder.git
   cd AI-Job-Finder
   ```

### 2. Add Your Resume
1. Place your own resume in PDF format in `uploads/` named `Resume.pdf`:
   ```
   uploads/Resume.pdf
   ```
2. Commit and push:
   ```bash
   git add -f uploads/Resume.pdf
   git commit -m "feat: add my resume"
   git push origin main
   ```

### 3. Enable GitHub Actions Write Permissions *(Crucial!)*
1. Go to your repository **Settings** → **Actions** → **General**.
2. Scroll to **Workflow permissions**.
3. Select **Read and write permissions**.
4. Check **Allow GitHub Actions to create and approve pull requests** and click **Save**.

### 4. Configure Repository Secrets
1. Go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
2. Add the following secrets:
   - `EMAIL_SENDER`: Your Gmail address (e.g. `yourname@gmail.com`)
   - `EMAIL_PASSWORD`: 16-character [Google App Password](https://myaccount.google.com/apppasswords)
   - `EMAIL_RECIPIENT`: Your email where you want job alerts delivered
   - `NAUKRI_USER`: *(Optional)* Your Naukri email
   - `NAUKRI_PASSWORD`: *(Optional)* Your Naukri password
   - `TINYFISH_API_KEY`: *(Optional)* TinyFish API key for stealth scraping

### 5. Enable & Test the Workflow
1. Go to the **Actions** tab in your repo.
2. Click **"I understand my workflows, go ahead and enable them"** (if prompted).
3. Click **Job Agent Scheduler** in the left sidebar.
4. Click **Run workflow** → **Run workflow** to trigger an immediate test run.

---

## 💻 Local Setup & Web Dashboard

### 1. Clone & Install
```bash
git clone https://github.com/sandeep8064/AI-Job-Finder.git
cd AI-Job-Finder

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies & Playwright browser
pip install -r requirements.txt
playwright install chromium
```

### 2. Setup Configuration
```bash
cp config.json.example config.json
```
Edit `config.json` with your email, keywords (e.g. `["Java Developer", "Spring Boot"]`), and candidate preferences.

### 3. Run Locally

- **Web Dashboard**:
  ```bash
  python wsgi.py
  # Open http://localhost:5000 in your browser
  ```

- **Run Scraping Once (CLI)**:
  ```bash
  python main.py run-once
  ```

- **Run Background Scheduler**:
  ```bash
  python main.py schedule
  ```

---

## 📁 Repository Structure

```
AI-Job-Finder/
├── .github/workflows/   # GitHub Actions scheduler workflow
├── cv_parser/          # PDF & DOCX resume parser
├── matcher/            # Relevance matching and scoring algorithms
├── notifier/           # HTML email generator and SMTP sender
├── scrapers/           # Modular company and job board scrapers
├── storage/            # SQLite database schema and persistence
├── templates/          # Email notification templates
├── uploads/            # Sample resume location (Resume.pdf)
├── utils/              # Timezone and utility functions
├── web/                # Flask web dashboard and UI templates
├── config.json.example # Template configuration file
├── config.py           # Configuration loader (JSON + Env vars)
├── HOSTING.md          # Cloud hosting instructions (Render / Oracle)
├── main.py             # CLI entry point
├── requirements.txt    # Python dependencies
└── wsgi.py             # Web server entry point
```

---

## 📄 License
This project is open source and available under the [MIT License](LICENSE).
