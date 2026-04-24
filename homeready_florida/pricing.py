from __future__ import annotations

from .models import Membership, RevenueSnapshot

HOMEOWNER = Membership("homeowner", 12, 99)
SNOWBIRD = Membership("snowbird", 19, 149)
MANAGER_BASE = Membership("manager", 49, 499)


def annualized_revenue(snapshot: RevenueSnapshot) -> int:
    monthly = (
        snapshot.homeowners * HOMEOWNER.monthly_price
        + snapshot.snowbirds * SNOWBIRD.monthly_price
        + snapshot.managers * MANAGER_BASE.monthly_price
        + snapshot.vendor_sponsorship_mrr
    )
    return monthly * 12


def monthly_recurring_revenue(snapshot: RevenueSnapshot) -> int:
    return annualized_revenue(snapshot) // 12

