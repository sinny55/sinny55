# HomeReady Florida MVP

This repository now includes a working Python MVP core for **HomeReady Florida** instead of only a business-plan document.

## What is implemented

- **Profile model** for homeowner/snowbird intake data
- **Plan Builder** that produces a complete 15-section readiness plan in Markdown
- **Reminder engine** for recurring maintenance reminders
- **Pricing engine** to estimate MRR and annualized revenue
- **Vendor matching** with county/category filtering + sponsorship prioritization

## Project structure

- `homeready_florida/models.py` — intake + revenue data models
- `homeready_florida/plan_builder.py` — personalized plan generation
- `homeready_florida/reminders.py` — monthly reminder scheduling
- `homeready_florida/pricing.py` — MRR/ARR helpers
- `homeready_florida/vendor_match.py` — vendor recommendation logic
- `tests/` — unit tests for core business logic

## Quickstart

```bash
python -m pip install -U pip pytest
pytest
```

## Example usage

```python
from datetime import date
from homeready_florida import (
    PropertyProfile,
    RevenueSnapshot,
    build_personalized_plan,
    generate_monthly_reminders,
    monthly_recurring_revenue,
)

profile = PropertyProfile(
    full_name="Alex Example",
    email="alex@example.com",
    county="Lee",
    property_type="single_family",
    occupancy_status="seasonal",
    residents=2,
    pets=1,
    has_generator=True,
    has_pool=True,
    departure_month="May",
    return_month="October",
)

plan = build_personalized_plan(profile)
reminders = generate_monthly_reminders(profile, date(2026, 5, 1), months=3)

mrr = monthly_recurring_revenue(
    RevenueSnapshot(homeowners=180, snowbirds=90, managers=30, vendor_sponsorship_mrr=750)
)

print(plan[:400])
print(len(reminders), mrr)
```

## Notes

This code intentionally avoids legal/insurance/public-adjusting guidance and keeps a clear disclaimer boundary in generated plans.
