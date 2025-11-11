"""
LinkedIn HTML parser (robust).

This parser is resilient to LinkedIn's common patterns:
 - embedded JSON inside <code> or <script> tags that is HTML-escaped (e.g. &quot;)
 - fragmented JSON where many fields are null but navigationUrl or job URL is present
 - cases where JSON parsing fails, using regex fallback to find /jobs/view/ links

It returns a list of dicts: { "title": str, "company": str, "link": str }
"""

from bs4 import BeautifulSoup
import json
import re
import html
from typing import List, Dict, Any


class LinkedInHtmlParser:
    def __init__(self, raw_html: str):
        self.soup = BeautifulSoup(raw_html, "html.parser")

    def extract_jobs_from_saved_page(self):
        """
        Top-level entrypoint.
        Parse the LinkedIn HTML, extract job data (title, company, link),
        deduplicate by link, and return a list of Job objects.

        This version is defensive:
        - ensures 'link' is a real string before using string methods
        - skips common LinkedIn placeholder values
        - converts the final deduplicated dicts into Job instances
        """
        from app.models.job import Job  # local import to avoid circular dependency
        import logging

        logger = logging.getLogger(__name__)

        collected_jobs: List[Dict[str, str]] = []

        # Look in <code> and <script> tags for embedded JSON
        candidate_tags = self.soup.find_all(["code", "script"])
        numero = len(candidate_tags)
        logger.debug("Number of candidate tags found: %s", numero)

        for tag in candidate_tags:
            text = tag.get_text(separator="", strip=True)
            if not text:
                continue

            # Decode HTML entities (turn &quot; into ")
            unescaped_text = html.unescape(text)

            # Try JSON parse first
            try:
                parsed_jobs = self._try_parse_json_and_extract_jobs(unescaped_text)
            except Exception as e:
                logger.debug("JSON parse attempt raised: %s", e)
                parsed_jobs = []

            if parsed_jobs:
                # Expect parsed_jobs to be a list of dicts like {"title":..., "company":..., "link":...}
                collected_jobs.extend(parsed_jobs)
                continue

            # Fallback to regex
            try:
                fallback_jobs = self._regex_extract_jobs_from_text(unescaped_text)
            except Exception as e:
                logger.debug("Regex fallback raised: %s", e)
                fallback_jobs = []

            if fallback_jobs:
                collected_jobs.extend(fallback_jobs)

        # Deduplicate by link (prefer non-empty title/company)
        unique_by_link: Dict[str, Dict[str, str]] = {}
        for job in collected_jobs:
            link = job.get("link")
            # Skip if no link or link is not a string
            if not link or not isinstance(link, str):
                continue

            # Clean whitespace early
            link_clean = link.strip()

            # Skip obvious placeholder values that LinkedIn sometimes includes
            # (adjust these patterns to match any observed placeholders)
            if link_clean.lower() in ("string", "null") or "com.linkedin.common.Url" in link_clean:
                continue

            if link_clean not in unique_by_link:
                unique_by_link[link_clean] = job.copy()
                unique_by_link[link_clean]["link"] = link_clean
            else:
                # merge missing fields
                existing = unique_by_link[link_clean]
                if not existing.get("title") and job.get("title"):
                    existing["title"] = job["title"]
                if not existing.get("company") and job.get("company"):
                    existing["company"] = job["company"]

        # Convert dicts → Job objects for consistency with the service layer
        job_objects: List[Job] = []
        for link, job_data in unique_by_link.items():
            # Defensive extraction of title/company
            raw_title = job_data.get("title") or ""
            raw_company = job_data.get("company") or ""

            title = raw_title.strip() if isinstance(raw_title, str) else "Untitled"
            company = raw_company.strip() if isinstance(raw_company, str) else "Unknown company"

            # Final safety: ensure link is string and non-empty
            if not link or not isinstance(link, str):
                logger.debug("Skipping non-string or empty link during final conversion: %r", link)
                continue
            job_instance = Job(
                title=title,
                company=company,
                link=link.strip(),
            )
            job_objects.append(job_instance)


        logger.debug("Extracted %d Job objects", len(job_objects))
        return job_objects



    # --------------------------
    # JSON parsing & recursive search
    # --------------------------
    def _try_parse_json_and_extract_jobs(self, text: str) -> List[Dict[str, str]]:
        """
        Attempt to json.loads(text) and recursively search for job nodes containing:
        - navigationUrl (or similar)
        - title or titleText / primary fields
        - companyName / secondary fields
        """
        try:
            data = json.loads(text)
        except Exception:
            return []

        # Recursively walk the JSON looking for nodes with job URL hints
        found = self._recursive_search_for_job_nodes(data)
        return found

    def _recursive_search_for_job_nodes(self, node: Any) -> List[Dict[str, str]]:
        """
        Walk dictionaries/lists looking for job info. Heuristics:
        - node contains 'navigationUrl' -> candidate job
        - or node contains 'jobPosting' / 'jobCard' structures
        """
        jobs = []

        if isinstance(node, dict):
            # Common LinkedIn keys that might include the URL
            possible_url_fields = ["navigationUrl", "navigationUrlForTracking", "navigationUrlForJob", "jobUrl", "url"]
            for field in possible_url_fields:
                if field in node and node[field]:
                    link = node[field]
                    print("link : %s " % link)
                    link_normal = self._normalize_link(link)
                    print("linnk normal : %s " % link_normal)
                    if not link_normal or isinstance(link, dict):
                        continue
                    title = self._extract_title_from_node(node)
                    company = self._extract_company_from_node(node)
                    jobs.append({"title": title or None, "company": company or None, "link": link_normal})
                    # continue scanning children; more info may exist deeper
            # Some payloads wrap job info under specific keys
            num = len(jobs)
            print("la len di jobs ora è : %s " % num)
            for key in ["jobPosting", "jobCard", "job", "jobPostings", "item", "elements"]:
                if key in node and node[key]:
                    jobs.extend(self._recursive_search_for_job_nodes(node[key]))
            # Iterate children
            print("la len di jobs ora è : %s " % num)
            for value in node.values():
                jobs.extend(self._recursive_search_for_job_nodes(value))
            print("la len di jobs ora è : %s " % num)

        elif isinstance(node, list):
            for item in node:
                jobs.extend(self._recursive_search_for_job_nodes(item))
        print(jobs)
        return jobs

    def _extract_title_from_node(self, node: Dict[str, Any]) -> str:
        """
        Try several common title locations in the node.
        """
        candidates = [
            node.get("title"),
            (node.get("titleText") or {}).get("text") if isinstance(node.get("titleText"), dict) else None,
            (node.get("primaryText") or {}).get("text") if isinstance(node.get("primaryText"), dict) else None,
            (node.get("headline") or {}).get("text") if isinstance(node.get("headline"), dict) else None,
            node.get("name"),
        ]
        for c in candidates:
            if c and isinstance(c, str) and c.strip():
                return c.strip()
        return None

    def _extract_company_from_node(self, node: Dict[str, Any]) -> str:
        """
        Try several common company fields.
        """
        candidates = [
            node.get("companyName"),
            (node.get("secondaryTitleText") or {}).get("text") if isinstance(node.get("secondaryTitleText"), dict) else None,
            (node.get("subtitle") or {}).get("text") if isinstance(node.get("subtitle"), dict) else None,
            (node.get("company") or {}).get("name") if isinstance(node.get("company"), dict) else None,
        ]
        for c in candidates:
            if c and isinstance(c, str) and c.strip():
                return c.strip()
        return None

    def _normalize_link(self, link):
        """
        Normalize link: make absolute if it's relative, strip HTML-encoded sequences.
        Handles non-string values safely.
        """
        if not link:
            return None

        # If LinkedIn gave us a nested object, try to extract something like {"url": "..."}
        if isinstance(link, dict):
            # Try to extract a useful value
            possible_keys = ["url", "navigationUrl", "href"]
            for key in possible_keys:
                if key in link and isinstance(link[key], str):
                    link = link[key]
                    break
            else:
                # No valid string found
                return None

        # Make sure we’re dealing with a string
        if not isinstance(link, str):
            return None

        # Unescape HTML entities
        link = html.unescape(link).strip()

        # Some links come as "/jobs/view/1234"; make them absolute
        if link.startswith("/"):
            link = f"https://www.linkedin.com{link}"

        # Remove "navigationUrl:" prefix if present
        if link.startswith("navigationUrl:"):
            link = link.replace("navigationUrl:", "").strip()
        print(link)

        return link


    # --------------------------
    # Regex fallback extraction
    # --------------------------
    JOB_URL_REGEX = re.compile(r"(https?:\/\/www\.linkedin\.com\/jobs\/view\/[0-9]+[^\s\"'>]*)", flags=re.IGNORECASE)

    def _regex_extract_jobs_from_text(self, text: str) -> List[Dict[str, str]]:
        """
        Fallback: search raw text for LinkedIn job URLs and try to extract title/company
        from nearby text fragments.
        """
        jobs = []
        for match in self.JOB_URL_REGEX.finditer(text):
            url = match.group(1)
            # attempt to find nearby title/company by searching some chars before/after the match
            start, end = match.span()
            window = text[max(0, start - 300): min(len(text), end + 300)]
            title = self._extract_title_from_plain_text(window)
            company = self._extract_company_from_plain_text(window)
            jobs.append({"title": title or None, "company": company or None, "link": self._normalize_link(url)})
        return jobs

    # heuristics for plain-text title/company extraction
    PLAIN_TITLE_REGEX = re.compile(r"\"title\"\s*:\s*\"([^\"]{3,200})\"", flags=re.IGNORECASE)
    PLAIN_COMPANY_REGEX = re.compile(r"\"companyName\"\s*:\s*\"([^\"]{3,200})\"", flags=re.IGNORECASE)

    def _extract_title_from_plain_text(self, text: str) -> str:
        m = self.PLAIN_TITLE_REGEX.search(text)
        if m:
            return m.group(1).strip()
        # fallback: look for human-readable phrases (very heuristic)
        alt = re.search(r"([A-Z][A-Za-z0-9&\-\s]{3,60})\s*(?:at|@)\s*([A-Z][A-Za-z0-9&\-\s]{2,60})", text)
        if alt:
            return alt.group(1).strip()
        return None

    def _extract_company_from_plain_text(self, text: str) -> str:
        m = self.PLAIN_COMPANY_REGEX.search(text)
        if m:
            return m.group(1).strip()
        alt = re.search(r"(?:at|@)\s*([A-Z][A-Za-z0-9&\-\s]{2,60})", text)
        if alt:
            return alt.group(1).strip()
        return None
