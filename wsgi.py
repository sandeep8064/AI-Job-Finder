"""WSGI entry point for Render deployment."""
import os
import sys

# Ensure the job_agent directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
