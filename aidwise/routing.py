from __future__ import annotations


def classify_query(query: str, has_structured_inputs: bool = False) -> str:
    text = query.lower().strip()

    if any(term in text for term in {"what if", "compare", "decrease", "increase"}):
        return "what_if"
    if any(term in text for term in {"why", "explain", "how come"}):
        return "explanation" if has_structured_inputs else "informational"
    if any(
        term in text
        for term in {
            "calculate",
            "estimate",
            "compute",
            "sai",
            "pell",
            "eligibility",
        }
    ):
        return "calculation" if has_structured_inputs else "informational"
    return "informational"
