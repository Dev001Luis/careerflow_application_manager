# app/services/linkedin_parser.py
"""
LinkedIn HTML parser service.

Parses an uploaded LinkedIn saved/jobs HTML file and extracts job entries.
The exact selectors may differ with LinkedIn changes — this parser is resilient
and returns Job objects with best-effort extraction.
"""

from bs4 import BeautifulSoup
from typing import List
from app.models.job import Job

class LinkedInHtmlParser:
    """
    Given raw HTML (from LinkedIn saved jobs page), attempt to extract job cards.
    """
    def __init__(self, raw_html: str):
        self.soup = BeautifulSoup(raw_html, "html.parser")

    def extract_jobs_from_saved_page(self) -> List[Job]:
        """
        Extract job entries and return a list of Job objects.
        Note: selectors are intentionally permissive; LinkedIn markup changes often.
        """
        extracted_jobs: List[Job] = []

        # Try some common patterns for job items — adjust if LinkedIn page structure differs
        # We look for anchor tags with job title or list items that appear like job cards.
        possible_job_elements = self.soup.select("a")  # fallback: iterate anchors and inspect attributes

        for element in possible_job_elements:
            # Heuristics: anchor with href that contains '/jobs/view/' or contains keywords
            href = element.get("href", "")
            text = element.get_text(separator=" ", strip=True)
            if not text:
                continue

            # very lightweight filtering heuristics:
            if "/jobs/view/" in href or "jobs" in href and (" · " in text or "|" in text or "-" in text):
                # derive title and company by splitting text heuristically
                title_text = text
                company_text = None
                # if there is a newline or separator, try to split
                for separator in ["\n", " | ", " · ", " - "]:
                    if separator in text:
                        parts = [p.strip() for p in text.split(separator) if p.strip()]
                        if len(parts) >= 2:
                            title_text = parts[0]
                            company_text = parts[1]
                            break

                job = Job(
                    title=title_text[:250],
                    company=company_text[:250] if company_text else None,
                    link=href,
                    category=None
                )
                extracted_jobs.append(job)

        # If none found by heuristics, try a different strategy: find elements that look like saved job cards
        if not extracted_jobs:
            # Example: look for list items with job-card classes (LinkedIn changes often)
            card_elements = self.soup.select("li")
            for card in card_elements:
                text = card.get_text(separator=" ", strip=True)
                if not text:
                    continue
                if "Applied" in text or "Saved" in text or "See job" in text:
                    # best effort
                    anchor = card.find("a", href=True)
                    href = anchor["href"] if anchor else None
                    title_candidate = card.find(["h3", "h4"])
                    company_candidate = card.find(["h4", "h5", "span"])
                    title_text = title_candidate.get_text(strip=True) if title_candidate else text[:120]
                    company_text = company_candidate.get_text(strip=True) if company_candidate else None
                    extracted_jobs.append(Job(title=title_text, company=company_text, link=href, category=None))

        return extracted_jobs
