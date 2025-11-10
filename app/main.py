# app/main.py
"""
Main Flask controllers for CareerFlow (Day 1).
This file is intentionally small: controllers are thin and delegate to service classes.
"""

from flask import request, jsonify, render_template
from flask import send_file, abort

from app import create_application

from app.services.linkedin_parser import LinkedInHtmlParser
from app.services.job_service import JobService
from app.services.cover_letter_service import CoverLetterGenerator

from app.models.job import Job


# Create app via factory (this will initialize DB tables in development)
app = create_application()


@app.route("/", methods=["GET", "POST"])
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
        print("sono nel try")
    except Exception:
        # fallback if read/decode fails
        raw_html = uploaded_file.read().decode("latin-1", errors="replace")
    print("raw_file ok")
    parser = LinkedInHtmlParser(raw_html)
    parsed_jobs = parser.extract_jobs_from_saved_page()
    print("ho parsato i jobs")
    print(parsed_jobs)
    inserted_count = JobService.import_jobs_from_parser(parsed_jobs)
    print(inserted_count)

    # Return both numeric result and updated partial HTML so the frontend can swap it in.
    jobs = JobService.get_all_jobs_for_display()
    print(jobs)
    jobs_list_html = render_template("jobs_list.html", jobs=jobs)
    return jsonify({"imported": inserted_count, "jobs_list_html": jobs_list_html}), 200


@app.route("/generate-pdf/<int:job_id>")
def generate_pdf(job_id):
    """
    Generate and return a cover letter PDF for the given job ID.
    """
    try:
        job = Job.get_job_by_id(job_id)
        if not job:
            abort(404, "Job not found")

        generator = CoverLetterGenerator(job)
        pdf_buffer = generator.generate_pdf()

        filename = f"cover_letter_{job['company']}_{job['title']}.pdf"
        return send_file(pdf_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype="application/pdf")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        abort(500, "Internal server error during PDF generation.")


if __name__ == "__main__":
    # Running as a module: python -m app.main
    app.run(debug=True)
