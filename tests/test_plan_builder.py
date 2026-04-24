from homeready_florida.models import PropertyProfile
from homeready_florida.plan_builder import build_personalized_plan


def test_plan_contains_required_sections() -> None:
    profile = PropertyProfile(
        full_name="Test User",
        email="test@example.com",
        county="Lee",
        property_type="condo",
        occupancy_status="primary",
    )

    plan = build_personalized_plan(profile)

    assert "## 1. Home profile summary" in plan
    assert "## 15. Disclaimer" in plan
    assert "1 gallon of water" in plan
    assert "7 days" in plan


def test_seasonal_notes_added_for_seasonal_profiles() -> None:
    profile = PropertyProfile(
        full_name="Snow Bird",
        email="snow@example.com",
        county="Collier",
        property_type="villa",
        occupancy_status="seasonal",
        departure_month="May",
        return_month="October",
    )

    plan = build_personalized_plan(profile)

    assert "### Seasonal resident custom notes" in plan
    assert "Expected departure month: May" in plan
