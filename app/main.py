# app/main.py
"""
Main Flask controllers for CareerFlow (Day 1).
This file is intentionally small: controllers are thin and delegate to service classes.
"""

from flask import request, jsonify, render_template
from app import create_application
from app.services.linkedin_parser import LinkedInHtmlParser
from app.services.job_service import JobService

# Create app via factory (this will initialize DB tables in development)
app = create_application()


@app.route("/")
def index():
    """
    Render the main dashboard page. The template includes the job list partial.
    """
    jobs = JobService.get_all_jobs_for_display()
    return render_template("index.html", jobs=jobs)


@app.route("/upload-linkedin", methods=["POST"])
def upload_linkedin_file():
    """
    Accept an uploaded LinkedIn saved-jobs HTML file, parse it and import new jobs.
    Returns JSON with inserted count and the HTML fragment for the updated jobs list.
    Frontend expects `jobs_list_html` in the JSON so it can replace the #jobList area.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    uploaded_file = request.files["file"]
    try:
        raw_html = uploaded_file.read().decode("utf-8", errors="replace")
    except Exception:
        # fallback if read/decode fails
        raw_html = uploaded_file.read().decode("latin-1", errors="replace")

    parser = LinkedInHtmlParser(raw_html)
    parsed_jobs = parser.extract_jobs_from_saved_page()
    inserted_count = JobService.import_jobs_from_parser(parsed_jobs)

    # Return both numeric result and updated partial HTML so the frontend can swap it in.
    jobs = JobService.get_all_jobs_for_display()
    jobs_list_html = render_template("jobs_list.html", jobs=jobs)
    return jsonify({"imported": inserted_count, "jobs_list_html": jobs_list_html}), 200


if __name__ == "__main__":
    # Running as a module: python -m app.main
    app.run(debug=True)
