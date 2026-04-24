from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

PropertyType = Literal["single_family", "condo", "villa", "rental", "airbnb"]
OccupancyStatus = Literal["primary", "second_home", "seasonal", "rental"]
PlanTier = Literal["homeowner", "snowbird", "manager"]


@dataclass(slots=True)
class PropertyProfile:
    full_name: str
    email: str
    county: str
    property_type: PropertyType
    occupancy_status: OccupancyStatus
    residents: int = 1
    pets: int = 0
    has_generator: bool = False
    has_pool: bool = False
    has_boat: bool = False
    has_elevator: bool = False
    has_solar: bool = False
    vendors: list[str] = field(default_factory=list)
    departure_month: str | None = None
    return_month: str | None = None


@dataclass(slots=True)
class Membership:
    tier: PlanTier
    monthly_price: int
    annual_price: int


@dataclass(slots=True)
class RevenueSnapshot:
    homeowners: int = 0
    snowbirds: int = 0
    managers: int = 0
    vendor_sponsorship_mrr: int = 0

