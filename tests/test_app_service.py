from homeready_florida.app import HomeReadyService


def _sample_profile_payload() -> dict:
    return {
        "full_name": "Alex Example",
        "email": "alex@example.com",
        "county": "Lee",
        "property_type": "single_family",
        "occupancy_status": "seasonal",
        "residents": 2,
        "pets": 1,
        "has_generator": True,
        "has_pool": True,
        "departure_month": "May",
        "return_month": "October",
    }


def test_create_profile_and_fetch_plan_and_reminders() -> None:
    service = HomeReadyService()
    created = service.create_profile(_sample_profile_payload())

    profile_id = created["profile_id"]
    assert created["tier_suggestion"] == "snowbird"
    assert "HomeReady Florida Personalized Plan" in created["plan_preview"]

    full_plan = service.get_plan(profile_id)
    assert "## 15. Disclaimer" in full_plan

    reminders = service.get_reminders(profile_id, months=2)
    assert len(reminders) == 7  # 3/month * 2 + seasonal departure reminder


def test_revenue_and_vendor_recommendations() -> None:
    service = HomeReadyService()

    revenue = service.estimate_revenue(
        {"homeowners": 100, "snowbirds": 50, "managers": 10, "vendor_sponsorship_mrr": 500}
    )
    assert revenue["mrr"] == 3140

    recommendations = service.recommend_vendors_for_request(
        {
            "county": "Lee",
            "needed_categories": ["generator", "pool"],
            "limit": 2,
            "vendors": [
                {"name": "Alpha Pool", "county": "Lee", "categories": ["pool"], "sponsored": False},
                {
                    "name": "Best Storm",
                    "county": "Lee",
                    "categories": ["generator", "shutters"],
                    "sponsored": True,
                },
                {"name": "Other HVAC", "county": "Collier", "categories": ["hvac"], "sponsored": True},
            ],
        }
    )

    assert len(recommendations) == 2
    assert recommendations[0]["name"] == "Best Storm"
