"""
web_tools.py — Web fetch and search tools for career-ops agent.
Uses requests + BeautifulSoup for JD fetching, DuckDuckGo for search.
No API keys required for search.
"""

import re
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 15
MAX_JD_CHARS = 10_000


def _clean_html(html: str) -> str:
    """Strip HTML to readable text, remove noise tags."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "advertisement", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:MAX_JD_CHARS]


@tool
def fetch_job_posting(url: str) -> str:
    """
    Fetch a job description from a URL.
    Handles LinkedIn, Greenhouse, Ashby, Lever, and generic pages.
    Returns cleaned text of the job description.
    """
    domain = urlparse(url).netloc.lower()

    # LinkedIn — try direct job API first
    if "linkedin.com" in domain:
        job_id_match = re.search(r"currentJobId=(\d+)|/view/(\d+)", url)
        if job_id_match:
            job_id = job_id_match.group(1) or job_id_match.group(2)
            api_url = f"https://www.linkedin.com/jobs/view/{job_id}/"
            try:
                resp = requests.get(api_url, headers=HEADERS, timeout=TIMEOUT)
                if resp.status_code == 200:
                    return _clean_html(resp.text)
            except requests.RequestException:
                pass

    # Greenhouse direct API
    greenhouse_match = re.search(r"boards\.greenhouse\.io/([^/]+)/jobs/(\d+)", url)
    if greenhouse_match:
        company, job_id = greenhouse_match.groups()
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs/{job_id}"
        try:
            data = requests.get(api_url, timeout=TIMEOUT).json()
            content = data.get("content", "") or data.get("title", "")
            soup = BeautifulSoup(content, "html.parser")
            return f"Title: {data.get('title', '')}\n\n{soup.get_text()}"[:MAX_JD_CHARS]
        except Exception:
            pass

    # Ashby direct API
    ashby_match = re.search(r"jobs\.ashbyhq\.com/([^/?#]+)/([^/?#]+)", url)
    if ashby_match:
        company, job_id = ashby_match.groups()
        api_url = (
            f"https://api.ashbyhq.com/posting-api/job-board/{company}"
            f"?includeCompensation=true"
        )
        try:
            data = requests.get(api_url, timeout=TIMEOUT).json()
            for job in data.get("jobs", []):
                if job_id.lower() in job.get("id", "").lower():
                    desc = BeautifulSoup(
                        job.get("descriptionHtml", ""), "html.parser"
                    ).get_text()
                    return f"Title: {job.get('title', '')}\n\n{desc}"[:MAX_JD_CHARS]
        except Exception:
            pass

    # Lever direct API
    lever_match = re.search(r"jobs\.lever\.co/([^/]+)/([^/?#]+)", url)
    if lever_match:
        company, job_id = lever_match.groups()
        api_url = f"https://api.lever.co/v0/postings/{company}/{job_id}"
        try:
            data = requests.get(api_url, timeout=TIMEOUT).json()
            desc = BeautifulSoup(
                data.get("descriptionPlain", data.get("description", "")),
                "html.parser"
            ).get_text()
            return f"Title: {data.get('text', '')}\n\n{desc}"[:MAX_JD_CHARS]
        except Exception:
            pass

    # Generic fallback
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return _clean_html(resp.text)
    except requests.RequestException as e:
        return f"Failed to fetch URL ({e}). Please paste the job description text directly."


@tool
def search_web(query: str) -> str:
    """
    Search the web using DuckDuckGo (free, no API key).
    Use for: comp research, company news, layoff signals, hiring freeze info.
    Examples:
      'AI Product Manager salary Bengaluru 2026 site:levels.fyi'
      'Libra AI funding layoffs 2026'
      'AI PM salary India Glassdoor'
    """
    try:
        searcher = DuckDuckGoSearchRun()
        time.sleep(0.5)  # be polite to DDG
        return searcher.run(query)
    except Exception as e:
        return f"Search failed: {e}. Try rephrasing the query."
