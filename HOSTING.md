# 🚀 Free Hosting & Deployment Guide

This guide covers options for hosting **AI-Job-Finder** for free so that it runs continuously in the cloud.

---

## Option 1: GitHub Actions (Recommended & 100% Free)

GitHub Actions runs the job scraper on GitHub's cloud runners on a schedule (default: every 6 hours).

### Setup Instructions
1. Fork or push this repository to GitHub.
2. In **Settings** → **Actions** → **General** → **Workflow permissions**, choose **Read and write permissions** and click **Save**.
3. In **Settings** → **Secrets and variables** → **Actions**, add your secrets:
   - `EMAIL_SENDER`: Your Gmail address.
   - `EMAIL_PASSWORD`: Gmail App Password.
   - `EMAIL_RECIPIENT`: Your alert destination email.
   - `NAUKRI_USER` *(Optional)*: Naukri login ID.
   - `NAUKRI_PASSWORD` *(Optional)*: Naukri password.
   - `TINYFISH_API_KEY` *(Optional)*: TinyFish stealth API key.
4. Ensure your resume is at `uploads/Resume.pdf`.
5. Go to the **Actions** tab, select **Job Agent Scheduler**, and click **Run workflow**.

---

## Option 2: Oracle Cloud Always-Free VM (Full Web Dashboard 24/7)

If you want the Web Dashboard live and accessible anywhere:

1. Sign up for [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/).
2. Create an **Ampere A1 Compute Instance** (up to 4 OCPUs, 24GB RAM free forever).
3. SSH into your VM and install dependencies:
   ```bash
   sudo apt update && sudo apt install -y python3-pip python3-venv git
   git clone https://github.com/sandeep8064/AI-Job-Finder.git
   cd AI-Job-Finder
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   playwright install --with-deps chromium
   ```
4. Set up systemd service or cron:
   ```bash
   # Crontab for agent:
   crontab -e
   # Add:
   0 */6 * * * cd /home/ubuntu/AI-Job-Finder && /home/ubuntu/AI-Job-Finder/.venv/bin/python main.py run-once >> /home/ubuntu/agent.log 2>&1
   ```

---

## Option 3: Render / Railway / Koyeb (Web Service)

1. Connect your GitHub repository to [Render](https://render.com).
2. Create a **Web Service**.
3. Build Command: `pip install -r requirements.txt && playwright install chromium --with-deps`
4. Start Command: `gunicorn wsgi:app`
5. Configure Environment Variables in the Render dashboard.

---

## 🔒 Security Best Practices
- **Never commit `config.json`** containing real email passwords or account tokens.
- Use **Google App Passwords**, not your primary Google account password.
