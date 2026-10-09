"""US cities used for training data and UI presets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    id: str
    label: str
    region: str
    lat: float
    lon: float


LOCATIONS: list[Location] = [
    Location("pdx", "Portland, OR", "Cool marine", 45.52, -122.68),
    Location("sea", "Seattle, WA", "Marine west coast", 47.61, -122.33),
    Location("chi", "Chicago, IL", "Continental", 41.88, -87.63),
    Location("msp", "Minneapolis, MN", "Upper Midwest", 44.98, -93.27),
    Location("den", "Denver, CO", "High plains", 39.74, -104.99),
    Location("nyc", "New York, NY", "Humid subtropical", 40.71, -74.01),
    Location("bos", "Boston, MA", "Coastal temperate", 42.36, -71.06),
    Location("atl", "Atlanta, GA", "Warm humid", 33.75, -84.39),
    Location("aus", "Austin, TX", "Warm", 30.27, -97.74),
    Location("phx", "Phoenix, AZ", "Desert", 33.45, -112.07),
    Location("mia", "Miami, FL", "Tropical humid", 25.76, -80.19),
    Location("lax", "Los Angeles, CA", "Mediterranean", 34.05, -118.24),
]
