import json
import os
import re
from typing import Any

import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


@st.cache_data
def load_taxonomy(path: str | None = None) -> dict:
    """Load skills taxonomy from JSON file."""
    if path is None:
        path = os.path.join(DATA_DIR, "skills_taxonomy.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_lookup(taxonomy: dict) -> dict[str, tuple[str, str]]:
    """Build a lowercased lookup mapping: term -> (canonical_skill, category).

    Includes both primary skill names and their aliases.
    """
    lookup: dict[str, tuple[str, str]] = {}
    for category, cat_data in taxonomy["categories"].items():
        for skill in cat_data["skills"]:
            lookup[skill.lower()] = (skill, category)
        for alias, canonical in cat_data.get("aliases", {}).items():
            lookup[alias.lower()] = (canonical, category)
    return lookup


def _make_pattern(term: str) -> re.Pattern:
    """Create a word-boundary regex pattern for a skill term.

    Handles terms with special regex characters like C++, C#, .NET, etc.
    """
    escaped = re.escape(term)
    # For terms ending with special chars (C++, C#), don't require trailing word boundary
    if re.search(r"[^\w\s]$", term):
        return re.compile(r"(?<!\w)" + escaped, re.IGNORECASE)
    # For terms starting with special chars (.NET), don't require leading word boundary
    if re.search(r"^[^\w\s]", term):
        return re.compile(escaped + r"(?!\w)", re.IGNORECASE)
    return re.compile(r"\b" + escaped + r"\b", re.IGNORECASE)


def extract_skills(text: str, taxonomy: dict | None = None) -> dict[str, list[str]]:
    """Extract skills from text using the taxonomy.

    Returns:
        Dict mapping category name -> list of unique canonical skill names found.
    """
    if taxonomy is None:
        taxonomy = load_taxonomy()

    lookup = _build_lookup(taxonomy)
    found: dict[str, set[str]] = {}

    # Sort terms by length descending so longer matches are tried first
    sorted_terms = sorted(lookup.keys(), key=len, reverse=True)

    for term in sorted_terms:
        pattern = _make_pattern(term)
        if pattern.search(text):
            canonical, category = lookup[term]
            found.setdefault(category, set()).add(canonical)

    # Convert sets to sorted lists for deterministic output
    return {cat: sorted(skills) for cat, skills in found.items()}


def analyze_gap(
    resume_skills: dict[str, list[str]],
    job_skills: dict[str, list[str]],
) -> dict[str, Any]:
    """Perform categorized skills gap analysis.

    Returns a dict with:
        - "categories": dict per category with matched/missing/extra lists and score
        - "overall": summary with total counts and overall score
    """
    all_categories = sorted(set(list(resume_skills.keys()) + list(job_skills.keys())))

    categories: dict[str, dict] = {}
    total_matched = 0
    total_job_required = 0

    for cat in all_categories:
        resume_set = set(resume_skills.get(cat, []))
        job_set = set(job_skills.get(cat, []))

        matched = sorted(resume_set & job_set)
        missing = sorted(job_set - resume_set)
        extra = sorted(resume_set - job_set)

        if len(job_set) > 0:
            score = round(len(matched) / len(job_set) * 100, 1)
        else:
            score = 100.0 if len(resume_set) == 0 else None  # N/A if job has no requirements

        categories[cat] = {
            "matched": matched,
            "missing": missing,
            "extra": extra,
            "score": score,
            "job_count": len(job_set),
            "resume_count": len(resume_set),
        }

        total_matched += len(matched)
        total_job_required += len(job_set)

    if total_job_required > 0:
        overall_score = round(total_matched / total_job_required * 100, 1)
    else:
        overall_score = 0.0

    # Compute average of per-category scores (where applicable)
    scored_cats = [c["score"] for c in categories.values() if c["score"] is not None and c["job_count"] > 0]
    avg_category_score = round(sum(scored_cats) / len(scored_cats), 1) if scored_cats else 0.0

    total_missing = sum(len(c["missing"]) for c in categories.values())
    total_extra = sum(len(c["extra"]) for c in categories.values())

    return {
        "categories": categories,
        "overall": {
            "matched": total_matched,
            "missing": total_missing,
            "extra": total_extra,
            "job_required": total_job_required,
            "score": overall_score,
            "avg_category_score": avg_category_score,
        },
    }
