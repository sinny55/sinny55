from __future__ import annotations

from .models import PropertyProfile

DISCLAIMER = (
    "HomeReady Florida provides organizational tools and preparedness information only. "
    "It does not provide legal advice, insurance advice, public adjusting services, "
    "or emergency response. Follow official guidance from county emergency management, "
    "the Florida Division of Emergency Management, and the National Hurricane Center."
)


def _features(profile: PropertyProfile) -> list[str]:
    features: list[str] = []
    if profile.has_generator:
        features.append("generator")
    if profile.has_pool:
        features.append("pool")
    if profile.has_boat:
        features.append("boat")
    if profile.has_elevator:
        features.append("elevator")
    if profile.has_solar:
        features.append("solar")
    return features


def build_personalized_plan(profile: PropertyProfile) -> str:
    features = _features(profile)
    feature_text = ", ".join(features) if features else "standard home systems"

    sections = [
        "# HomeReady Florida Personalized Plan",
        "",
        "## 1. Home profile summary",
        f"- Owner: {profile.full_name}",
        f"- County: {profile.county}",
        f"- Property type: {profile.property_type}",
        f"- Occupancy status: {profile.occupancy_status}",
        f"- Household size: {profile.residents} residents, {profile.pets} pets",
        f"- Key features: {feature_text}",
        "",
        "## 2. Top readiness priorities",
        "- Verify evacuation zone and nearest shelter options.",
        "- Keep policy documents and photo inventory in cloud + local copy.",
        "- Schedule pre-season checks for shutters, roof, and HVAC.",
        "",
        "## 3. Hurricane-season checklist",
        "- Keep at least 1 gallon of water per person per day.",
        "- Stock non-perishable food for at least 7 days.",
        "- Charge battery banks and test emergency lighting.",
        "- Confirm alert subscriptions (NOAA weather radio + county alerts).",
        "",
        "## 4. Evacuation planning checklist",
        "- Save two routes: primary + flood-safe alternate.",
        "- Prepare go-bags with IDs, meds, and chargers.",
        "- Pre-arrange family contact check-in protocol.",
        "",
        "## 5. Shelter-in-place checklist",
        "- Fill water containers and secure outdoor furniture.",
        "- Move valuables to elevated interior locations.",
        "- Pre-cool home and keep freezer doors closed during outages.",
        "",
        "## 6. Pet plan",
        "- Keep pet food/water for 7+ days.",
        "- Maintain collar tags, microchip info, and carrier readiness.",
        "",
        "## 7. Medical/special-needs plan",
        "- Maintain refill buffer for medications and essential supplies.",
        "- Document backup power needs for medical devices.",
        "",
        "## 8. Insurance document organization checklist",
        "- Store policy declarations, contact numbers, and claim instructions.",
        "- Keep copies of IDs and proof of residency.",
        "",
        "## 9. Home inventory checklist",
        "- Photograph each room + major items.",
        "- Capture serial numbers and estimated replacement value.",
        "",
        "## 10. Vendor contact checklist",
        "- Confirm pool, HVAC, landscaping, and home-watch contacts.",
        "- Define storm response SLA expectations with each vendor.",
        "",
        "## 11. Monthly maintenance reminders",
        "- Test generator under load.",
        "- Replace HVAC filter.",
        "- Inspect roof drains and shutters.",
        "",
        "## 12. Seasonal departure/arrival checklist",
        "- Departure: shut off water, set thermostat, secure lanai furniture.",
        "- Arrival: test utilities, inspect for leaks/pests, refresh supplies.",
        "",
        "## 13. Post-storm re-entry checklist",
        "- Re-enter only when local authorities permit.",
        "- Document visible damage before cleanup.",
        "- Contact insurers/vendors with timestamped photos.",
        "",
        "## 14. What to review every year",
        "- Review insurance limits and deductibles.",
        "- Re-test shutters and generator; update inventory values.",
        "",
        "## 15. Disclaimer",
        f"- {DISCLAIMER}",
    ]

    if profile.occupancy_status == "seasonal":
        sections.extend(
            [
                "",
                "### Seasonal resident custom notes",
                f"- Expected departure month: {profile.departure_month or 'not set'}",
                f"- Expected return month: {profile.return_month or 'not set'}",
                "- Schedule home-watch check-ins every 14 days while away.",
            ]
        )

    return "\n".join(sections)
