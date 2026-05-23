"""
validators.py
-------------
Contains all accepted filter values as defined in the PRD (Section 6).
Every endpoint uses validate_filters() before processing data.
"""

from fastapi import HTTPException

# ──────────────────────────────────────────────
# All valid values per filter — from PRD Section 6
# ──────────────────────────────────────────────

VALID_VALUES = {
    "region": [
        "Dhaka", "Chittagong", "Sylhet", "Rajshahi",
        "Khulna", "Rangpur", "Barisal", "Mymensingh"
    ],
    "farm_type": ["Small", "Medium", "Large", "Commercial"],
    "crop_category": [
        "Cereal", "Vegetable", "Fruit", "Pulse",
        "Oilseed", "Cash Crop", "Spice"
    ],
    "season": ["Spring", "Summer", "Autumn", "Winter"],
    "growing_season": ["Rabi", "Kharif", "Zaid", "Year-Round"],
    "market_type": [
        "Local", "Wholesale", "Export", "Retail", "Government Procurement"
    ],
    "price_tier": ["Low", "Medium", "High", "Premium"],
    "quality_grade": ["A", "B", "C", "D"],
    "pesticide_residue": ["None", "Trace", "Low", "High"],
    "water_requirement": ["Low", "Medium", "High"],
    "year": [2022, 2023, 2024],
    "quarter": [1, 2, 3, 4],
    "metric": ["profit", "revenue", "yield"],
}


def validate_filters(**kwargs) -> None:
    """
    Validates all provided filter values against the allowed list.
    Raises HTTP 422 with a clear message if anything is invalid.

    Usage:
        validate_filters(region=region, year=year, season=season)
    """
    for field, value in kwargs.items():
        if value is None:
            continue  # Filter was not provided — that's fine, skip it

        if field not in VALID_VALUES:
            continue  # Unknown field — skip silently

        allowed = VALID_VALUES[field]
        if value not in allowed:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": f"Invalid value for '{field}'",
                    "provided": value,
                    "accepted_values": allowed
                }
            )


def build_filters_applied(**kwargs) -> dict:
    """
    Builds the 'filters_applied' dict for JSON responses.
    Only includes filters that were actually provided (not None).
    """
    return {k: v for k, v in kwargs.items() if v is not None}
