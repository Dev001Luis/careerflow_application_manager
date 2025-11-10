# app/models/job.py
"""
Job model: object-oriented representation of a job application entry.

This class encapsulates persistence (save/delete) and a simple factory to load from DB.
Methods use long descriptive names and docstrings.
"""

from typing import Optional, List, Dict
from app.db import get_cursor
from datetime import datetime

class Job:
    """
    Represents a single job application or saved job.
    """
    def __init__(
        self,
        title: str,
        company: Optional[str] = None,
        link: Optional[str] = None,
        category: Optional[str] = None,
        status: str = "Saved",
        applied_date: Optional[str] = None,
        interview_date: Optional[str] = None,
        notes: Optional[str] = None,
        id: Optional[int] = None
    ):
        self.id = id
        self.title = title
        self.company = company
        self.link = link
        self.category = category
        self.status = status
        self.applied_date = applied_date
        self.interview_date = interview_date
        self.notes = notes

    @staticmethod
    def from_row(row: Dict) -> "Job":
        """Create a Job instance from a DB row (dictionary)."""
        return Job(
            title=row.get("title"),
            company=row.get("company"),
            link=row.get("link"),
            category=row.get("category"),
            status=row.get("status"),
            applied_date=str(row.get("applied_date")) if row.get("applied_date") else None,
            interview_date=str(row.get("interview_date")) if row.get("interview_date") else None,
            notes=row.get("notes"),
            id=row.get("id")
        )

    def save_to_database(self) -> "Job":
        """
        Save the Job object to the jobs table.
        Performs INSERT if self.id is None, otherwise UPDATE.
        Returns self with id populated after insert.
        """
        if self.id:
            query = """
                UPDATE jobs
                SET title=%s, company=%s, link=%s, category=%s, status=%s,
                    applied_date=%s, interview_date=%s, notes=%s
                WHERE id=%s
            """
            params = (
                self.title, self.company, self.link, self.category, self.status,
                self.applied_date, self.interview_date, self.notes, self.id
            )
            with get_cursor() as cursor:
                cursor.execute(query, params)
        else:
            query = """
                INSERT INTO jobs (title, company, link, category, status, applied_date, interview_date, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                self.title, self.company, self.link, self.category, self.status,
                self.applied_date, self.interview_date, self.notes
            )
            with get_cursor() as cursor:
                cursor.execute(query, params)
                self.id = cursor.lastrowid
        return self

    def delete_from_database(self) -> None:
        """Delete this job from the database."""
        if not self.id:
            return
        with get_cursor() as cursor:
            cursor.execute("DELETE FROM jobs WHERE id = %s", (self.id,))
        self.id = None

    @staticmethod
    def fetch_all_jobs(limit: int = 200) -> List["Job"]:
        """
        Fetch jobs from DB ordered by applied_date desc then id desc.
        Returns a list of Job instances.
        """
        query = "SELECT * FROM jobs ORDER BY applied_date DESC, id DESC LIMIT %s"
        with get_cursor() as cursor:
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
        return [Job.from_row(row) for row in rows] if rows else []

    @staticmethod
    def find_job_by_link_or_title(link_value: Optional[str], title_value: str) -> Optional["Job"]:
        """
        Try to find an existing job either by exact link or by title/company combination.
        Returns Job or None.
        """
        if link_value:
            with get_cursor() as cursor:
                cursor.execute("SELECT * FROM jobs WHERE link = %s LIMIT 1", (link_value,))
                row = cursor.fetchone()
                if row:
                    return Job.from_row(row)

        # Fallback: try by title and company (may yield duplicates but prevents obvious duplication)
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM jobs WHERE title = %s LIMIT 1", (title_value,))
            row = cursor.fetchone()
            if row:
                return Job.from_row(row)

        return None

    @classmethod
    def get_job_by_id(job_id: int):
        """
        Fetch a single job entry from the database by its ID.

        Args:
            job_id (int): The ID of the job in the jobs table.

        Returns:
            dict | None: A dictionary of job data or None if not found.
        """
        from app.db import get_cursor
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None

            columns = [col[0] for col in cursor.description]
            print(columns)
            return dict(zip(columns, row))
