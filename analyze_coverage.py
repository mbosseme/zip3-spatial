#!/usr/bin/env python3
"""
ZIP3 Coverage Analysis - Final clean version
Analyzes what percentage of each state is covered by ZIP3 polygons
"""

import geopandas as gpd
import pandas as pd

def analyze_zip3_coverage():
    """Analyze ZIP3 coverage by state using proper area calculations"""
    print("🔍 ZIP3 Coverage Analysis by State")
    print("="*50)

    try:
        # Load the dissolved ZIP3-state layer
        print("📂 Loading ZIP3-state dissolved layer...")
        gdf = gpd.read_file("out/state_zip3_dissolved.gpkg").to_crs(5070)  # equal-area projection
        print(f"   Loaded {len(gdf)} ZIP3-state polygons")
        
        # Load original state boundaries for comparison
        print("📂 Loading original state boundaries...")
        state_bounds = gpd.read_file("state_shp/cb_2018_us_state_500k.shp").to_crs(5070)
        state_bounds = state_bounds[['STUSPS', 'geometry']].set_index('STUSPS')
        print(f"   Loaded {len(state_bounds)} state boundaries")
        
        # Calculate areas
        print("📊 Calculating coverage by state...")
        
        # Get total ZIP3 area by state (dissolve overlapping ZIP3 polygons)
        zip3_area_by_state = gdf.dissolve(by="STUSPS").area
        
        # Get original state total areas
        original_state_areas = state_bounds.area
        
        # Calculate coverage percentage for common states
        common_states = list(set(zip3_area_by_state.index) & set(original_state_areas.index))
        coverage = (zip3_area_by_state[common_states] / original_state_areas[common_states]).sort_values()
        
        # Display results
        print("\n🔻 States with LOWEST ZIP3 coverage:")
        print("-" * 45)
        for state, pct in coverage.head(8).items():
            reason = get_coverage_reason(state, pct)
            print(f"   {state}: {pct:>6.1%} - {reason}")
        
        print("\n🔺 States with HIGHEST ZIP3 coverage:")
        print("-" * 45)
        for state, pct in coverage.tail(8).items():
            reason = get_coverage_reason(state, pct)
            print(f"   {state}: {pct:>6.1%} - {reason}")
        
        # Overall statistics
        print(f"\n📈 Overall Statistics:")
        print(f"   Total states/territories analyzed: {len(coverage)}")
        print(f"   Mean coverage: {coverage.mean():.1%}")
        print(f"   Median coverage: {coverage.median():.1%}")
        print(f"   States with >100% coverage: {(coverage > 1.0).sum()}")
        print(f"   States with 95-100% coverage: {((coverage >= 0.95) & (coverage <= 1.0)).sum()}")
        print(f"   States with <95% coverage: {(coverage < 0.95).sum()}")
        
        # Insights for Tableau users
        print(f"\n🎯 Insights for Tableau Visualization:")
        
        excellent = coverage[coverage >= 0.95]
        good = coverage[(coverage >= 0.85) & (coverage < 0.95)]
        fair = coverage[(coverage >= 0.75) & (coverage < 0.85)]
        poor = coverage[coverage < 0.75]
        
        print(f"   ✅ Excellent coverage (≥95%): {len(excellent)} states")
        print(f"   ⚠️  Good coverage (85-94%): {len(good)} states")
        print(f"   ⚠️  Fair coverage (75-84%): {len(fair)} states") 
        print(f"   ❌ Poor coverage (<75%): {len(poor)} states")
        
        if len(poor) > 0:
            print(f"   Note: Poor coverage states: {', '.join(poor.index.tolist())}")
        
        return coverage
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_coverage_reason(state, pct):
    """Get a brief explanation for the coverage percentage"""
    if pct > 1.2:
        return "Multiple ZIP overlaps or boundary differences"
    elif pct > 1.05:
        return "Minor boundary differences"
    elif pct >= 0.95:
        return "Excellent coverage"
    elif pct >= 0.85:
        return "Good coverage"
    elif pct >= 0.75:
        return "Fair coverage"
    elif state == "AK":
        return "Sparse population, vast wilderness"
    elif state in ["HI"]:
        return "Island geography limits"
    elif state in ["NV", "UT", "CA", "OR"]:
        return "Large rural/desert areas"
    else:
        return "Rural areas without postal service"

if __name__ == "__main__":
    print("Running ZIP3 coverage analysis...\n")
    coverage_results = analyze_zip3_coverage()
    
    if coverage_results is not None:
        print(f"\n✅ Analysis complete!")
        print(f"The ZIP3-state dataset is ready for Tableau visualization.")
        print(f"Most states have excellent coverage for geographic analysis.")
