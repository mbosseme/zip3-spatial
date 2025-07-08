#!/usr/bin/env python3
"""
Quick test to analyze ZIP3 coverage by state
"""

import geopandas as gpd
import pandas as pd

def test_zip3_coverage():
    """Test ZIP3 coverage by state using equal-area projection"""
    print("🔍 Testing ZIP3 coverage by state...")
    print("="*50)

    try:
        # Load the dissolved layer
        print("📂 Loading dissolved layer...")
        gdf = gpd.read_file("out/state_zip3_dissolved.gpkg").to_crs(5070)  # equal-area
        print(f"   Loaded {len(gdf)} polygons")
        
        # Calculate % of each state that has a ZIP-3 polygon
        print("📊 Calculating coverage by state...")
        
        # Get total area by state from ZIP3 polygons
        zip3_area_by_state = gdf.dissolve(by="STUSPS").area
        
        # Get unique state geometries and their total areas
        state_geometries = gdf[['STUSPS','geometry']].drop_duplicates('STUSPS')
        total_area_by_state = state_geometries.dissolve(by='STUSPS').area
        
        # Calculate coverage percentage
        coverage = (zip3_area_by_state / total_area_by_state).sort_values()
        
        print("\n🔻 States with LOWEST ZIP3 coverage:")
        print("-" * 40)
        for state, pct in coverage.head(8).items():
            print(f"   {state}: {pct:.1%}")
        
        print("\n🔺 States with HIGHEST ZIP3 coverage:")
        print("-" * 40)
        for state, pct in coverage.tail(8).items():
            print(f"   {state}: {pct:.1%}")
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Mean coverage: {coverage.mean():.1%}")
        print(f"   Median coverage: {coverage.median():.1%}")
        print(f"   States with >95% coverage: {(coverage > 0.95).sum()}")
        print(f"   States with <50% coverage: {(coverage < 0.50).sum()}")
        
        # Additional insights
        print(f"\n🎯 Key Insights:")
        low_coverage = coverage[coverage < 0.5]
        if len(low_coverage) > 0:
            print(f"   Low coverage states: {', '.join(low_coverage.index.tolist())}")
        
        territories = ['AS', 'GU', 'MP', 'VI']
        territory_coverage = coverage[coverage.index.isin(territories)]
        if len(territory_coverage) > 0:
            print(f"   Territory coverage: {territory_coverage.to_dict()}")
        
        return coverage
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    coverage_results = test_zip3_coverage()
