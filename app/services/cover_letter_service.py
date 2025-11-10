"""
Service responsible for generating PDF cover letters for job applications.
Uses ReportLab to produce clean, HR-friendly PDF output.
"""

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from datetime import date


class CoverLetterGenerator:
    """Generates a PDF cover letter for a specific job application."""

    def __init__(self, job_data):
        """
        Initialize the generator with job details.

        Args:
            job_data (dict): A dictionary containing job details
                (title, company, location, description, etc.)
        """
        self.job_data = job_data

    def build_cover_letter_text(self) -> list:
        """
        Build the textual content of the cover letter dynamically.

        Returns:
            list[str]: List of paragraphs.
        """
        job_title = self.job_data.get("title", "Job Position")
        company = self.job_data.get("company", "Company")
        location = self.job_data.get("location", "Location")

        paragraphs = [
            f"{date.today().strftime('%B %d, %Y')}",
            f"Dear Hiring Team at {company},",
            f"I am writing to express my strong interest in the {job_title} position at {company}. "
            f"After reviewing the job description, I am confident that my background in software development, "
            f"problem-solving, and continuous learning aligns closely with your team’s needs.",
            f"My experience with Python, Flask, RESTful APIs, and database-driven web applications "
            f"has allowed me to deliver efficient, maintainable solutions in collaborative environments. "
            f"I am particularly motivated by roles that blend backend logic with clean, user-focused design.",
            f"I would appreciate the opportunity to contribute my skills to {company} and to grow within your team. "
            f"I am excited about the possibility of discussing how I can add value to your organization.",
            "Thank you for considering my application. I look forward to hearing from you.",
            "Sincerely,",
            "Luis Stasi"
        ]
        return paragraphs

    def generate_pdf(self) -> BytesIO:
        """
        Generate a PDF document in memory and return it as a BytesIO stream.

        Returns:
            BytesIO: In-memory PDF file.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()

        content = []
        for text in self.build_cover_letter_text():
            content.append(Paragraph(text, styles["Normal"]))
            content.append(Spacer(1, 0.2 * inch))

        doc.build(content)
        buffer.seek(0)
        return buffer
