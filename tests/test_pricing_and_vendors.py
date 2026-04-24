from homeready_florida.models import RevenueSnapshot
from homeready_florida.pricing import monthly_recurring_revenue
from homeready_florida.vendor_match import Vendor, recommend_vendors


def test_monthly_recurring_revenue() -> None:
    snapshot = RevenueSnapshot(homeowners=100, snowbirds=50, managers=10, vendor_sponsorship_mrr=500)
    assert monthly_recurring_revenue(snapshot) == (100 * 12 + 50 * 19 + 10 * 49 + 500)


def test_vendor_recommendations_prioritize_sponsored_and_county() -> None:
    vendors = [
        Vendor("Alpha Pool", "Lee", {"pool"}, sponsored=False),
        Vendor("Best Storm", "Lee", {"shutters", "generator"}, sponsored=True),
        Vendor("Other County HVAC", "Collier", {"hvac"}, sponsored=True),
    ]

    matches = recommend_vendors(vendors, county="Lee", needed_categories={"generator", "pool"})

    assert len(matches) == 2
    assert matches[0].name == "Best Storm"
