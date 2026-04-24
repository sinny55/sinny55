from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Vendor:
    name: str
    county: str
    categories: set[str]
    sponsored: bool = False


def recommend_vendors(vendors: list[Vendor], county: str, needed_categories: set[str], limit: int = 5) -> list[Vendor]:
    filtered = [
        v
        for v in vendors
        if v.county.lower() == county.lower() and (v.categories & needed_categories)
    ]
    filtered.sort(key=lambda v: (not v.sponsored, v.name.lower()))
    return filtered[:limit]
