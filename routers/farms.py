""" routers/farms.py

Report 1 — Farm Performance Report
Endpoints:
  1. GET /farms/summary → Farm summary with filters
  2. GET /farms/top → Top N farms by metric
  3. GET /farms/loss-analysis → Post-harvest loss breakdown
  4. GET /farms/{farm_id}/performance → Single farm detail

IMPORTANT: Static routes (/summary, /top, /loss-analysis) must be defined
BEFORE the dynamic route (/{farm_id}/performance) so FastAPI doesn't
accidentally treat "top" or "summary" as a farm_id number. """

from fastapi import APIRouter, Query, HTTPException
from database import get_harvest_df
from validators import validate_filters, build_filters_applied
import pandas as pd

router = APIRouter(prefix="/farms", tags=["Farm Performance"])

#ENDPOINT 1 — GET /farms/summary

@router.get("/summary", summary="Farm Summary Report")
def farm_summary(
    region:    str | None = Query(default=None, description="Filter by region e.g. Dhaka"),
    farm_type: str | None = Query(default=None, description="Small | Medium | Large | Commercial"),
    year:      int | None = Query(default=None, description="2022 | 2023 | 2024"),
    season:    str | None = Query(default=None, description="Spring | Summer | Autumn | Winter"),
):
  
    """ Returns total revenue, cost, profit, and average loss % for each farm.
    No filters = returns ALL farms across all years. """

  
    #Step 1: Validate filters
  
    validate_filters(region=region, farm_type=farm_type, year=year, season=season)
  

    #Step 2: Load data and apply filters
  
    df= get_harvest_df()

    if region:
        df= df[df["region"] == region]
    if farm_type:
        df= df[df["farm_type"] == farm_type]
    if year:
        df= df[df["year"] == year]
    if season:
        df= df[df["season"] == season]

    if df.empty:
        return {
            "total_farms": 0,
            "filters_applied": build_filters_applied(region=region, farm_type=farm_type, year=year, season=season),
            "data": []
        }
      

    #Step 3: Aggregate per farm
  
    grouped = df.groupby(["farm_name", "region", "farm_type"]).agg(
        total_revenue_bdt= ("revenue_bdt", "sum"),
        total_cost_bdt= ("total_cost_bdt", "sum"),
        net_profit_bdt= ("net_profit_bdt", "sum"),
        avg_loss_pct= ("post_harvest_loss_pct", "mean"),
    ).reset_index()

    #Round the loss percentage to 1 decimal
  
    grouped["avg_loss_pct"] = grouped["avg_loss_pct"].round(1)

  
    #Step 4: Build response
    data= grouped.to_dict(orient="records")

    return {
        "total_farms": len(grouped),
        "filters_applied": build_filters_applied(
            region=region, farm_type=farm_type, year=year, season=season
        ),
        "data": data,
    }


#ENDPOINT 3 — GET /farms/top
# Defined before /{farm_id} to avoid routing conflict)
# ════════════════════════════════════════════════════════════════════


@router.get("/top", summary="Top N Farms Ranking")
def top_farms(
    metric:    str      = Query(default="profit",  description="profit | revenue | yield"),
    region:    str | None = Query(default=None,    description="Filter by region"),
    farm_type: str | None = Query(default=None,    description="Small | Medium | Large | Commercial"),
    year:      int | None = Query(default=None,    description="2022 | 2023 | 2024"),
    limit:     int        = Query(default=10,       description="Number of top farms to return"),
):
  
    """ Returns top N farms ranked by profit, revenue, or yield efficiency.
    Default: top 10 by profit. """
    validate_filters(metric=metric, region=region, farm_type=farm_type, year=year)

    if limit <= 0:
        raise HTTPException(status_code=422, detail={"error": "'limit' must be a positive integer"})

    df= get_harvest_df()

    if region:
        df= df[df["region"] == region]
    if farm_type:
        df= df[df["farm_type"] == farm_type]
    if year:
        df= df[df["year"] == year]

    if df.empty:
        return {
            "metric": metric,
            "filters_applied": build_filters_applied(region=region, farm_type=farm_type, year=year, limit=limit),
            "rankings": []
        }

    #Aggregate per farm
  
    grouped = df.groupby(["farm_name", "region", "farm_type"]).agg(
        net_profit_bdt    = ("net_profit_bdt", "sum"),
        total_revenue_bdt = ("revenue_bdt", "sum"),
        avg_yield         = ("yield_ton_per_ha", "mean"),
    ).reset_index()

    #Choose sort column based on metric
  
    sort_column = {
        "profit":  "net_profit_bdt",
        "revenue": "total_revenue_bdt",
        "yield":   "avg_yield",
    }[metric]

    grouped = grouped.sort_values(sort_column, ascending=False).head(limit).reset_index(drop=True)
    grouped["rank"] = grouped.index + 1

    #Build response rows — include avg_yield only for yield metric, keep it clean otherwise
  
    rankings = []
    for _, row in grouped.iterrows():
        entry = {
            "rank": int(row["rank"]),
            "farm_name": row["farm_name"],
            "region": row["region"],
            "farm_type": row["farm_type"],
            "net_profit_bdt": round(row["net_profit_bdt"], 2),
            "total_revenue_bdt": round(row["total_revenue_bdt"], 2),
        }
        if metric == "yield":
            entry["avg_yield_ton_per_ha"] = round(row["avg_yield"], 2)
        rankings.append(entry)

    return {
        "metric": metric,
        "filters_applied": build_filters_applied(
            region=region, farm_type=farm_type, year=year, limit=limit
        ),
      
        "rankings": rankings,
    }


#ENDPOINT 4 — GET /farms/loss-analysis
#(Defined before /{farm_id} to avoid routing conflict)
#══════════════════════════════════════════════════════════════════════

@router.get("/loss-analysis", summary="Post-Harvest Loss Analysis")
def loss_analysis(
    region: str | None = Query(default=None, description="Filter by region"),
    year: int | None = Query(default=None, description="2022 | 2023 | 2024"),
    season: str | None = Query(default=None, description="Spring | Summer | Autumn | Winter"),
    quality_grade: str | None = Query(default=None, description="A | B | C | D"),
    crop_category: str | None = Query(default=None, description="Cereal | Vegetable | Fruit ..."),
):
  
    """ Shows post-harvest loss in tonnes and percentage, broken down by
    region, season, crop category, and quality grade. """
  
    validate_filters(
        region=region, year=year, season=season,
        quality_grade=quality_grade, crop_category=crop_category
    )

    df= get_harvest_df()

    if region:
        df= df[df["region"] == region]
    if year:
        df= df[df["year"] == year]
    if season:
        df= df[df["season"] == season]
    if quality_grade:
        df= df[df["quality_grade"] == quality_grade]
    if crop_category:
        df= df[df["crop_category"] == crop_category]

    if df.empty:
        return {
            "filters_applied": build_filters_applied(
                region=region, year=year, season=season,
                quality_grade=quality_grade, crop_category=crop_category
            ),
            "summary": {"total_harvested_ton": 0, "total_lost_ton": 0, "overall_loss_pct": 0},
            "breakdown": []
        }

    #Overall summary
    total_harvested= df["harvest_quantity_ton"].sum()
    total_lost= df["post_harvest_loss_ton"].sum()
    overall_loss= round((total_lost / total_harvested * 100), 1) if total_harvested > 0 else 0

    #Breakdown by region + crop_category + quality_grade
    grouped= df.groupby(["region", "crop_category", "quality_grade", "pesticide_residue"]).agg(
        total_harvested= ("harvest_quantity_ton", "sum"),
        total_lost_ton = ("post_harvest_loss_ton", "sum"),
    ).reset_index()

    grouped["loss_pct"]= (grouped["total_lost_ton"] / grouped["total_harvested"] * 100).round(1)

    breakdown= []
    for _, row in grouped.iterrows():
        breakdown.append({
            "region": row["region"],
            "crop_category": row["crop_category"],
            "quality_grade": row["quality_grade"],
            "total_lost_ton": round(row["total_lost_ton"], 1),
            "loss_pct": row["loss_pct"],
            "pesticide_residue": row["pesticide_residue"],
        })

    return {
        "filters_applied": build_filters_applied(
            region=region, year=year, season=season,
            quality_grade=quality_grade, crop_category=crop_category
        ),
        "summary": {
            "total_harvested_ton": round(total_harvested, 1),
            "total_lost_ton":      round(total_lost, 1),
            "overall_loss_pct":    overall_loss,
        },
        "breakdown": breakdown,
    }

#ENDPOINT 2 — GET /farms/{farm_id}/performance
#(Defined LAST — dynamic route comes after all static routes)
#══════════════════════════════════════════════════════════════════════

@router.get("/{farm_id}/performance", summary="Single Farm Detailed Performance")
def farm_performance(
    farm_id: int,
    year: int | None = Query(default=None, description="2022 | 2023 | 2024"),
    crop_category: str | None = Query(default=None, description="Cereal | Vegetable | Fruit ..."),
    market_type: str | None = Query(default=None, description="Local | Wholesale | Export ..."),
):
    """ Returns per-crop, per-year, per-market breakdown for a single farm.
    farm_id is an integer from 1 to 30. """
  
    validate_filters(year=year, crop_category=crop_category, market_type=market_type)

    df= get_harvest_df()

    #Filter to this specific farm
    farm_df = df[df["farm_id"] == farm_id]

    if farm_df.empty:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Farm with id={farm_id} not found. Valid IDs are 1–30."}
        )

    #Get farm metadata from first row
    farm_meta = farm_df.iloc[0]

    #Apply optional filters
  
    if year:
        farm_df= farm_df[farm_df["year"] == year]
    if crop_category:
        farm_df= farm_df[farm_df["crop_category"] == crop_category]
    if market_type:
        farm_df= farm_df[farm_df["market_type"] == market_type]

    if farm_df.empty:
        return {
            "farm_id": farm_id,
            "farm_name": farm_meta["farm_name"],
            "owner": farm_meta["owner"],
            "region": farm_meta["region"],
            "filters_applied": build_filters_applied(
                year=year, crop_category=crop_category, market_type=market_type
            ),
            "performance": []
        }

    #Aggregate per crop + year + market_type
  
    grouped= farm_df.groupby(
        ["crop_name", "year", "market_type", "quality_grade"]
    ).agg(
        quantity_sold_ton= ("quantity_sold_ton", "sum"),
        revenue_bdt= ("revenue_bdt", "sum"),
        net_profit_bdt= ("net_profit_bdt", "sum"),
    ).reset_index()

    performance= []
    for _, row in grouped.iterrows():
        performance.append({
            "crop_name":         row["crop_name"],
            "year":              int(row["year"]),
            "market_type":       row["market_type"],
            "quantity_sold_ton": round(row["quantity_sold_ton"], 1),
            "revenue_bdt":       round(row["revenue_bdt"], 2),
            "net_profit_bdt":    round(row["net_profit_bdt"], 2),
            "quality_grade":     row["quality_grade"],
        })

    return {
        "farm_id":   farm_id,
        "farm_name": farm_meta["farm_name"],
        "owner":     farm_meta["owner"],
        "region":    farm_meta["region"],
        "filters_applied": build_filters_applied(
            year=year, crop_category=crop_category, market_type=market_type
        ),
        "performance": performance,
    }
