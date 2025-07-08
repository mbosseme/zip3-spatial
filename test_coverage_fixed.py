#!/usr/bin/env python3
"""
Fixed coverage test - debugging the area calculation issue
"""

import geopandas as gpd
import pandas as pd

def debug_coverage_calculation():
    """Debug the coverage calculation to fix the percentage issue"""
    print("🔍 Debugging ZIP3 coverage calculation...")
    print("="*50)

    try:
        # Load the dissolved layer
        print("📂 Loading dissolved layer...")
        gdf = gpd.read_file("out/state_zip3_dissolved.gpkg").to_crs(5070)  # equal-area
        print(f"   Loaded {len(gdf)} polygons")
        
        print("\n🔧 Debugging area calculations...")
        
        # Method 1: Original approach (problematic)
        print("Method 1 (Original):")
        zip3_area_by_state = gdf.dissolve(by="STUSPS").area
        state_geometries = gdf[['STUSPS','geometry']].drop_duplicates('STUSPS')
        total_area_by_state = state_geometries.dissolve(by='STUSPS').area
        
        print(f"   ZIP3 dissolved area sample: {zip3_area_by_state.head(3)}")
        print(f"   State total area sample: {total_area_by_state.head(3)}")
        
        # Method 2: Load state boundaries separately for comparison
        print("\nMethod 2 (Using original state boundaries):")
        state_bounds = gpd.read_file("state_shp/cb_2018_us_state_500k.shp").to_crs(5070)
        state_bounds = state_bounds[['STUSPS', 'geometry']].set_index('STUSPS')
        
        print(f"   Original state area sample: {state_bounds.area.head(3)}")
        
        # Method 3: Correct calculation
        print("\nMethod 3 (Corrected):")
        # Get ZIP3 areas by state
        zip3_by_state = gdf.dissolve(by="STUSPS").area
        
        # Get original state areas
        original_state_areas = state_bounds.area
        
        # Calculate coverage only for states that exist in both datasets
        common_states = list(set(zip3_by_state.index) & set(original_state_areas.index))
        coverage = (zip3_by_state[common_states] / original_state_areas[common_states]).sort_values()
        
        print(f"   Coverage calculation sample: {coverage.head(3)}")
        
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
        
        # Show problematic states
        low_coverage = coverage[coverage < 0.5]
        if len(low_coverage) > 0:
            print(f"\n⚠️  States with low coverage:")
            for state, pct in low_coverage.items():
                print(f"   {state}: {pct:.1%}")
        
        return coverage
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    coverage_results = debug_coverage_calculation()
