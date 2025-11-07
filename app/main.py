# app/main.py
"""
Main Flask routes. Controllers remain thin: they delegate parsing and business logic
to service classes and model objects.
"""

from flask import request, jsonify, render_template, url_for, redirect
from app import create_application
from app.services.linkedin_parser import LinkedInHtmlParser
from app.services.job_service import JobService

app = create_application()

@app.route("/")
def index():
    """
    Render main dashboard: the template will expect a partial jobs list that can
    be replaced asynchronously.
    """
    jobs = JobService.get_all_jobs_for_display()
    return render_template("index.html", jobs=jobs)

@app.route("/upload-linkedin", methods=["POST"])
def upload_linkedin_file():
    """
    Accept an uploaded LinkedIn saved jobs HTML file, parse it and import new jobs.
    Returns JSON { imported: n } on success.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    uploaded_file = request.files["file"]
    raw_html = uploaded_file.read().decode("utf-8", errors="replace")
    parser = LinkedInHtmlParser(raw_html)
    parsed_jobs = parser.extract_jobs_from_saved_page()
    inserted_count = JobService.import_jobs_from_parser(parsed_jobs)

    # Optionally return the updated jobs partial HTML to replace the job list in the UI
    jobs = JobService.get_all_jobs_for_display()
    jobs_list_html = render_template("_jobs_list.html", jobs=jobs)
    return jsonify({"imported": inserted_count, "jobs_list_html": jobs_list_html}), 200
