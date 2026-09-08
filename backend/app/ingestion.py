"""Fetch jobs from supported official career-board APIs.

Each board is opt-in through environment variables because board identifiers and
credentials vary by company. The fetcher uses public read-only endpoints and
upserts by source URL.
"""
import json
import os
from datetime import date
from urllib.parse import quote
from urllib.request import Request, urlopen

from .models import Opportunity
from .matching import infer_eligible_branches


SOURCE_CONFIG = {
    "greenhouse": ("GREENHOUSE_BOARDS", "https://boards-api.greenhouse.io/v1/boards/{board}/jobs"),
    "lever": ("LEVER_SITES", "https://api.lever.co/v0/postings/{board}?mode=json"),
    "ashby": ("ASHBY_BOARDS", "https://api.ashbyhq.com/posting-api/job-board/{board}"),
    "smartrecruiters": ("SMARTRECRUITERS_COMPANIES", "https://api.smartrecruiters.com/v1/companies/{board}/postings"),
    "workday": ("WORKDAY_ENDPOINTS", "{board}"),
}


def configured_sources():
    return {
        provider: [item.strip() for item in os.getenv(variable, "").split(",") if item.strip()]
        for provider, (variable, _) in SOURCE_CONFIG.items()
    }


def fetch_json(url, body=None):
    encoded_body = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(url, data=encoded_body, headers={"User-Agent": "Oppora job-ingestion/1.0", "Accept": "application/json", "Content-Type": "application/json"}, method="POST" if body is not None else "GET")
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return None


def normalize_job(provider, board, raw):
    if provider == "greenhouse":
        title = raw.get("title")
        url = raw.get("absolute_url")
        description = raw.get("content", "")
        location = (raw.get("location") or {}).get("name", "India")
    elif provider == "lever":
        title = raw.get("text")
        url = raw.get("hostedUrl")
        description = raw.get("descriptionPlain", "")
        location = ", ".join(item.get("name", "") for item in raw.get("categories", {}).get("allLocations", [])) or "India"
    elif provider == "ashby":
        title = raw.get("title")
        url = raw.get("jobUrl")
        description = raw.get("descriptionPlain", "")
        location = ", ".join(raw.get("locationNames", [])) or "India"
    elif provider == "smartrecruiters":
        title = raw.get("name")
        reference = raw.get("ref", {}).get("jobAd", {})
        description_section = reference.get("sections", {}).get("jobDescription", {})
        url = reference.get("url") or raw.get("url")
        description = description_section.get("text", "")
        location = (raw.get("location") or {}).get("city", "India")
    else:
        title = raw.get("title") or raw.get("jobPostingTitle")
        url = raw.get("externalUrl") or raw.get("url")
        description = raw.get("description", "")
        location = raw.get("location", "India") if isinstance(raw.get("location", "India"), str) else "India"

    if not title or not url:
        return None
    return {
        "title": title,
        "organization": board,
        "opportunity_type": "Job",
        "role": title,
        "description": description[:5000],
        "eligible_branches": ",".join(infer_eligible_branches(title, description)),
        "source_url": url,
        "source_name": f"{board} Careers ({provider.title()})",
        "deadline": _date(raw.get("deadline")),
        "location": location,
        "verified": True,
    }


def fetch_provider(provider, board):
    _, template = SOURCE_CONFIG[provider]
    payload = fetch_json(
        board if provider == "workday" else template.format(board=quote(board)),
        {"appliedFacets": {}, "limit": 100, "offset": 0, "searchText": ""} if provider == "workday" else None,
    )
    if provider == "smartrecruiters":
        return payload.get("content", [])
    if provider == "workday":
        return payload.get("jobPostings", payload.get("jobs", []))
    return payload.get("jobs", payload) if isinstance(payload, dict) else payload


def ingest_configured(db):
    summary = {"created": 0, "updated": 0, "failed": []}
    for provider, boards in configured_sources().items():
        for board in boards:
            try:
                for raw in fetch_provider(provider, board):
                    job = normalize_job(provider, board, raw)
                    if not job:
                        continue
                    existing = db.query(Opportunity).filter(Opportunity.source_url == job["source_url"]).first()
                    if existing:
                        for key, value in job.items():
                            setattr(existing, key, value)
                        summary["updated"] += 1
                    else:
                        db.add(Opportunity(**job))
                        summary["created"] += 1
                db.commit()
            except Exception as error:
                db.rollback()
                summary["failed"].append({"provider": provider, "board": board, "error": str(error)[:300]})
    return summary