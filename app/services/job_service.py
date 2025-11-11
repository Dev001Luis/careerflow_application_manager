# app/services/job_service.py
from typing import List
from app.models.job import Job

class JobService:
    """Service responsible for orchestrating job imports and queries."""

    @staticmethod
    def import_jobs_from_parser(parsed_jobs: List["Job"]) -> int:
        """
        Receives a list of Job objects (not yet saved). For each job:
        - if a job with the same link or title exists, skip
        - otherwise save and count inserted
        Returns the number of inserted records.
        """
        inserted_count = 0
        for parsed_job in parsed_jobs:
            print(f"→ Processing job: {parsed_job.title} ({parsed_job.link})")

            # Safety check
            if not parsed_job.link or not isinstance(parsed_job.link, str):
                print("⚠️ Skipping invalid link:", parsed_job.link)
                continue
            print("DEBUG → parsed_job.link:", parsed_job.link, type(parsed_job.link))

            existing_job = Job.find_job_by_link_or_title(parsed_job.link)
            if existing_job:
                continue

            parsed_job.save_to_database()
            inserted_count += 1

        return inserted_count

    @staticmethod
    def get_all_jobs_for_display() -> List["Job"]:
        """Return a list of Job objects for the UI."""
        return Job.fetch_all_jobs()
