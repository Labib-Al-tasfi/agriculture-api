""" routers/crops_markets.py
Report 2 — Crop & Market Intelligence Report
Endpoints:
  5. GET /crops/yield-efficiency   → Actual vs benchmark yield per crop
  6. GET /crops/seasonal-trend     → Revenue & quantity by season/year
  7. GET /markets/price-comparison → Price comparison across market channels
  8. GET /crops/quality-breakdown  → Grade distribution + pesticide residue """

from fastapi import APIRouter, Query, HTTPException
from database import get_harvest_df
from validators import validate_filters, build_filters_applied
import pandas as pd

router = APIRouter(tags=["Crop & Market Intelligence"])

#ENDPOINT 5 — GET /crops/yield-efficiency

@router.get("/crops/yield-efficiency", summary="Crop Yield Efficiency vs Benchmark")
def crop_yield_efficiency(
    crop_category: str | None = Query(default=None, description="Cereal | Vegetable | Fruit ..."),
    season: str | None = Query(default=None, description="Spring | Summer | Autumn | Winter"),
    year: int | None = Query(default=None, description="2022 | 2023 | 2024"),
    region: str | None = Query(default=None, description="Filter by region"),
    water_requirement: str | None = Query(default=None, description="Low | Medium | High"),
):
    """ Compares actual yield per hectare against the national benchmark for each crop.
    efficiency_pct > 100 = outperforming national average. """
    validate_filters(
        crop_category=crop_category, season=season, year=year,
        region=region, water_requirement=water_requirement
    )

    df= get_harvest_df()

    if crop_category:
        df= df[df["crop_category"] == crop_category]
    if season:
        df= df[df["season"] == season]
    if year:
        df= df[df["year"] == year]
    if region:
        df= df[df["region"] == region]
    if water_requirement:
        df= df[df["water_requirement"] == water_requirement]

    if df.empty:
        return {
            "filters_applied": build_filters_applied(
                crop_category=crop_category, season=season, year=year,
                region=region, water_requirement=water_requirement
            ),
            "data": []
        }

    #Aggregate per crop — average actual yield, benchmark is fixed per crop
    grouped = df.groupby(
        ["crop_name", "crop_category", "growing_season", "yield_benchmark_ton_per_ha"]
    ).agg(
        actual_avg_yield  = ("yield_ton_per_ha", "mean"),
        total_area_planted = ("area_planted_ha", "sum"),
    ).reset_index()

    #Compute efficiency %
    grouped["efficiency_pct"] = (
        grouped["actual_avg_yield"] / grouped["yield_benchmark_ton_per_ha"] * 100
    ).round(1)

    data = []
    for _, row in grouped.iterrows():
        data.append({
            "crop_name":                    row["crop_name"],
            "crop_category":                row["crop_category"],
            "avg_yield_benchmark_ton_per_ha": round(row["yield_benchmark_ton_per_ha"], 2),
            "actual_avg_yield_ton_per_ha":  round(row["actual_avg_yield"], 2),
            "efficiency_pct":               row["efficiency_pct"],
            "total_area_planted_ha":        round(row["total_area_planted"], 1),
            "season":                       row["growing_season"],
        })

    return {
        "filters_applied": build_filters_applied(
            crop_category=crop_category, season=season, year=year,
            region=region, water_requirement=water_requirement
        ),
        "data": data,
    }


# ENDPOINT 6 — GET /crops/seasonal-trend

@router.get("/crops/seasonal-trend", summary="Seasonal Revenue Trend by Crop")
def seasonal_trend(
    crop_name:     str | None = Query(default=None, description="Filter by specific crop name"),
    crop_category: str | None = Query(default=None, description="Cereal | Vegetable | Fruit ..."),
    year:          int | None = Query(default=None, description="2022 | 2023 | 2024"),
    quarter:       int | None = Query(default=None, description="1 | 2 | 3 | 4"),
    market_type:   str | None = Query(default=None, description="Local | Wholesale | Export ..."),
):
    """ Shows how revenue and quantity sold changes across seasons and years
    for each crop. Useful for finding the most profitable seasons. """
    validate_filters(
        crop_category=crop_category, year=year,
        quarter=quarter, market_type=market_type
    )

    df = get_harvest_df()

    if crop_name:
        df= df[df["crop_name"].str.lower() == crop_name.lower()]
    if crop_category:
        df= df[df["crop_category"] == crop_category]
    if year:
        df= df[df["year"] == year]
    if quarter:
        df= df[df["quarter"] == quarter]
    if market_type:
        df= df[df["market_type"] == market_type]

    if df.empty:
        return {
            "filters_applied": build_filters_applied(
                crop_name=crop_name, crop_category=crop_category,
                year=year, quarter=quarter, market_type=market_type
            ),
            "trend": []
        }

    #Aggregate per crop + year + quarter + season
    grouped = df.groupby(["crop_name", "year", "quarter", "season"]).agg(
        total_quantity_sold_ton= ("quantity_sold_ton", "sum"),
        total_revenue_bdt= ("revenue_bdt", "sum"),
        avg_price_per_ton_bdt= ("price_per_ton_bdt", "mean"),
        num_harvests= ("harvest_quantity_ton", "count"),
    ).reset_index()

    trend = []
    for _, row in grouped.iterrows():
        trend.append({
            "crop_name": row["crop_name"],
            "year": int(row["year"]),
            "quarter": int(row["quarter"]),
            "season": row["season"],
            "total_quantity_sold_ton": round(row["total_quantity_sold_ton"], 1),
            "total_revenue_bdt": round(row["total_revenue_bdt"], 2),
            "avg_price_per_ton_bdt": round(row["avg_price_per_ton_bdt"], 0),
            "num_harvests": int(row["num_harvests"]),
        })

    return {
        "filters_applied": build_filters_applied(
            crop_name=crop_name, crop_category=crop_category,
            year=year, quarter=quarter, market_type=market_type),
        "trend": trend,
    }


# ══════════════════════════════════════════════════════════════════════
# ENDPOINT 7 — GET /markets/price-comparison
# ══════════════════════════════════════════════════════════════════════

@router.get("/markets/price-comparison", summary="Market Price Comparison Across Channels")
def market_price_comparison(
    market_type:   str | None = Query(default=None, description="Local | Wholesale | Export ..."),
    crop_category: str | None = Query(default=None, description="Cereal | Vegetable | Fruit ..."),
    year:          int | None = Query(default=None, description="2022 | 2023 | 2024"),
    season:        str | None = Query(default=None, description="Spring | Summer | Autumn | Winter"),
    price_tier:    str | None = Query(default=None, description="Low | Medium | High | Premium"),
    district:      str | None = Query(default=None, description="Filter by district"),
):
    """
    Compares average selling prices across market types, districts, and price tiers.
    Helps identify which market channel gives the best return per crop.
    """
    validate_filters(
        market_type=market_type, crop_category=crop_category,
        year=year, season=season, price_tier=price_tier
    )

    df = get_harvest_df()

    if market_type:
        df = df[df["market_type"] == market_type]
    if crop_category:
        df = df[df["crop_category"] == crop_category]
    if year:
        df = df[df["year"] == year]
    if season:
        df = df[df["season"] == season]
    if price_tier:
        df = df[df["price_tier"] == price_tier]
    if district:
        df = df[df["district"].str.lower() == district.lower()]

    if df.empty:
        return {
            "filters_applied": build_filters_applied(
                market_type=market_type, crop_category=crop_category,
                year=year, season=season, price_tier=price_tier, district=district
            ),
            "comparison": []
        }

    # Aggregate per market + crop
    grouped = df.groupby(
        ["market_name", "market_type", "price_tier", "district", "crop_name"]
    ).agg(
        avg_price_per_ton_bdt   = ("price_per_ton_bdt", "mean"),
        total_quantity_sold_ton = ("quantity_sold_ton", "sum"),
        total_revenue_bdt       = ("revenue_bdt", "sum"),
    ).reset_index()

    # Sort by avg price descending — best-paying markets first
    grouped = grouped.sort_values("avg_price_per_ton_bdt", ascending=False)

    comparison = []
    for _, row in grouped.iterrows():
        comparison.append({
            "market_name":            row["market_name"],
            "market_type":            row["market_type"],
            "price_tier":             row["price_tier"],
            "district":               row["district"],
            "crop_name":              row["crop_name"],
            "avg_price_per_ton_bdt":  round(row["avg_price_per_ton_bdt"], 0),
            "total_quantity_sold_ton": round(row["total_quantity_sold_ton"], 1),
            "total_revenue_bdt":      round(row["total_revenue_bdt"], 2),
        })

    return {
        "filters_applied": build_filters_applied(
            market_type=market_type, crop_category=crop_category,
            year=year, season=season, price_tier=price_tier, district=district
        ),
        "comparison": comparison,
    }

#ENDPOINT 8 — GET /crops/quality-breakdown

@router.get("/crops/quality-breakdown", summary="Crop Quality Grade Distribution")
def quality_breakdown(
    crop_id:           int | None = Query(default=None, description="Crop ID from dim_crop"),
    crop_category:     str | None = Query(default=None, description="Cereal | Vegetable | Fruit ..."),
    year:              int | None = Query(default=None, description="2022 | 2023 | 2024"),
    region:            str | None = Query(default=None, description="Filter by region"),
    market_type:       str | None = Query(default=None, description="Local | Wholesale | Export ..."),
    pesticide_residue: str | None = Query(default=None, description="None | Trace | Low | High"),
):
    """ Shows distribution of quality grades (A, B, C, D) for crops.
    Also shows pesticide residue breakdown alongside quality grades. """
  
    validate_filters(
        crop_category=crop_category, year=year, region=region,
        market_type=market_type, pesticide_residue=pesticide_residue
    )

    df = get_harvest_df()

    if crop_id is not None:
        df= df[df["crop_id"] == crop_id]
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail={"error": f"No data found for crop_id={crop_id}"}
            )
    if crop_category:
        df= df[df["crop_category"] == crop_category]
    if year:
        df= df[df["year"] == year]
    if region:
        df= df[df["region"] == region]
    if market_type:
        df= df[df["market_type"] == market_type]
    if pesticide_residue:
        df= df[df["pesticide_residue"] == pesticide_residue]

    if df.empty:
        return {
            "filters_applied": build_filters_applied(
                crop_id=crop_id, crop_category=crop_category, year=year,
                region=region, market_type=market_type, pesticide_residue=pesticide_residue
            ),
            "total_records": 0,
            "grade_distribution": {},
            "pesticide_residue_breakdown": {}
        }

    total = len(df)

    #Grade distribution
  
    grade_dist = {}
    for grade in ["A", "B", "C", "D"]:
        subset= df[df["quality_grade"] == grade]
        count= len(subset)
        pct= round(count / total * 100, 1) if total > 0 else 0
        avg_rev= round(subset["revenue_bdt"].mean(), 0) if count > 0 else 0
        grade_dist[grade]= {
            "count": count,
            "pct": pct,
            "avg_revenue_bdt": int(avg_rev),
        }

    #Pesticide residue distribution 
  
    residue_dist = {}
    for level in ["None", "Trace", "Low", "High"]:
        subset= df[df["pesticide_residue"] == level]
        count= len(subset)
        pct= round(count / total * 100, 1) if total > 0 else 0
        residue_dist[level] = {"count": count, "pct": pct}

    return {
        "filters_applied": build_filters_applied(
            crop_id=crop_id, crop_category=crop_category, year=year,
            region=region, market_type=market_type, pesticide_residue=pesticide_residue
        ),
        "total_records": total,
        "grade_distribution": grade_dist,
        "pesticide_residue_breakdown": residue_dist,
    }
