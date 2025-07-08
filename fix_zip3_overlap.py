#!/usr/bin/env python3
"""
Fix ZIP3 Overlap Script

This script creates a border-trimmed State × ZIP3 layer that removes the >100% 
coverage problem by using 'within' predicate and centroid assignment for 
border-straddling ZIPs, then dissolving by state and ZIP3.

Purpose: Generate clean state-ZIP3 polygons without boundary overshoots
Output: ./out/state_zip3_trimmed.gpkg and .shp
"""

import os
import sys
import time
import geopandas as gpd
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuration
ZCTA_BASE_NAME = "cb_2018_us_zcta510_500k"
STATE_DIR = "state_shp"
STATE_BASE_NAME = "cb_2018_us_state_500k"
OUTPUT_DIR = "out"
REFERENCE_GPKG = "out/state_zip3_dissolved.gpkg"

def check_input_files():
    """Verify all required input files exist"""
    print("🔍 Checking input files...")
    
    required_files = [
        f"{ZCTA_BASE_NAME}.shp",
        f"{STATE_DIR}/{STATE_BASE_NAME}.shp", 
        REFERENCE_GPKG
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ ERROR: Missing required files: {', '.join(missing_files)}")
        print("Please ensure you have run transform_zip3.py first to generate the reference files.")
        sys.exit(1)
    
    print("✅ All required input files found")

def load_reference_data():
    """Load reference data to get CRS and existing states"""
    print("📂 Loading reference data...")
    
    # Load the existing dissolved layer for reference
    ref_gdf = gpd.read_file(REFERENCE_GPKG)
    existing_states = set(ref_gdf['STUSPS'].unique())
    reference_crs = ref_gdf.crs
    
    print(f"   Reference CRS: {reference_crs}")
    print(f"   Existing states in dissolved layer: {len(existing_states)}")
    
    return reference_crs, existing_states

def load_and_prepare_raw_data(target_crs, existing_states):
    """Load raw ZCTA and state data, prepare for processing"""
    print("📊 Loading raw ZCTA data...")
    
    # Load ZCTA data
    zcta_gdf = gpd.read_file(f"{ZCTA_BASE_NAME}.shp")
    print(f"   Loaded {len(zcta_gdf)} ZCTA polygons")
    
    # Keep only required columns and add ZIP3
    zcta_gdf = zcta_gdf[['GEOID10', 'geometry']].copy()
    zcta_gdf['ZIP3'] = zcta_gdf['GEOID10'].str[:3]
    
    # Ensure target CRS
    if zcta_gdf.crs != target_crs:
        print(f"   Reprojecting ZCTA from {zcta_gdf.crs} to {target_crs}")
        zcta_gdf = zcta_gdf.to_crs(target_crs)
    
    print("📊 Loading state boundary data...")
    state_shp_path = os.path.join(STATE_DIR, f"{STATE_BASE_NAME}.shp")
    state_gdf = gpd.read_file(state_shp_path)
    print(f"   Loaded {len(state_gdf)} state polygons")
    
    # Filter states to match existing dissolved layer (keep territories if they exist)
    original_count = len(state_gdf)
    state_gdf = state_gdf[state_gdf['STUSPS'].isin(existing_states)].copy()
    
    if len(state_gdf) < original_count:
        removed_states = original_count - len(state_gdf)
        print(f"   ⚠️  Filtered out {removed_states} states/territories not in reference layer")
    
    # Keep only required state columns and ensure target CRS
    state_gdf = state_gdf[['STATEFP', 'STUSPS', 'geometry']].copy()
    if state_gdf.crs != target_crs:
        print(f"   Reprojecting states from {state_gdf.crs} to {target_crs}")
        state_gdf = state_gdf.to_crs(target_crs)
    
    return zcta_gdf, state_gdf

def assign_zips_to_states(zcta_gdf, state_gdf):
    """Assign each ZIP to exactly one state using within + centroid method"""
    print("🎯 Assigning ZIPs to states using 'within' predicate...")
    
    # First, try direct 'within' join
    within_join = gpd.sjoin(zcta_gdf, state_gdf, how='inner', predicate='within')
    within_join = within_join.drop(columns=['index_right'])
    
    print(f"   {len(within_join)} ZIPs assigned via 'within' predicate")
    
    # Find ZIPs that weren't assigned (border-straddling)
    assigned_zips = set(within_join['GEOID10'])
    unassigned_zips = zcta_gdf[~zcta_gdf['GEOID10'].isin(assigned_zips)].copy()
    
    print(f"   {len(unassigned_zips)} border-straddling ZIPs need centroid assignment")
    
    if len(unassigned_zips) > 0:
        # Calculate centroids for unassigned ZIPs
        unassigned_centroids = unassigned_zips.copy()
        unassigned_centroids['geometry'] = unassigned_centroids.geometry.centroid
        
        # Join centroids to states using 'within'
        centroid_join = gpd.sjoin(unassigned_centroids, state_gdf, how='inner', predicate='within')
        centroid_join = centroid_join.drop(columns=['index_right'])
        
        # Restore original geometry for the centroid-assigned ZIPs
        centroid_join['geometry'] = unassigned_zips.set_index('GEOID10').loc[centroid_join['GEOID10'], 'geometry'].values
        
        print(f"   {len(centroid_join)} ZIPs assigned via centroid method")
        
        # Combine both assignment methods
        final_join = pd.concat([within_join, centroid_join], ignore_index=True)
    else:
        final_join = within_join
    
    print(f"   Total assigned: {len(final_join)} ZIPs to states")
    
    # Check for any remaining unassigned ZIPs
    final_assigned = set(final_join['GEOID10'])
    still_unassigned = len(zcta_gdf) - len(final_assigned)
    
    if still_unassigned > 0:
        print(f"   ⚠️  {still_unassigned} ZIPs could not be assigned to any state")
    
    return final_join

def dissolve_and_validate(joined_gdf):
    """Dissolve by state and ZIP3, then validate geometry"""
    print("🔄 Dissolving by State × ZIP3...")
    
    # Group by state and ZIP3, then dissolve
    dissolved_gdf = joined_gdf.dissolve(by=['STUSPS', 'ZIP3']).reset_index()
    
    # Fix any invalid geometries created by dissolve
    print("🔧 Fixing geometry issues...")
    invalid_before = (~dissolved_gdf.geometry.is_valid).sum()
    if invalid_before > 0:
        print(f"   Found {invalid_before} invalid geometries, applying buffer(0) fix...")
        dissolved_gdf['geometry'] = dissolved_gdf['geometry'].buffer(0)
        
        invalid_after = (~dissolved_gdf.geometry.is_valid).sum()
        if invalid_after > 0:
            print(f"   ⚠️  {invalid_after} geometries still invalid after buffer fix")
        else:
            print("   ✅ All geometries are now valid")
    
    # Keep only the required columns
    dissolved_gdf = dissolved_gdf[['STUSPS', 'ZIP3', 'geometry']].copy()
    
    print(f"   Created {len(dissolved_gdf)} dissolved polygons")
    
    return dissolved_gdf

def simplify_geometry_optional(gdf):
    """Optional geometry simplification for performance"""
    print("⚡ Simplifying geometry for performance...")
    
    original_crs = gdf.crs
    
    # Convert to equal-area projection for simplification
    gdf_albers = gdf.to_crs('EPSG:5070')  # Albers Equal Area
    
    # Simplify with 75m tolerance
    gdf_albers['geometry'] = gdf_albers['geometry'].simplify(tolerance=75)
    
    # Convert back to original CRS
    gdf_simplified = gdf_albers.to_crs(original_crs)
    
    return gdf_simplified

def validate_coverage(gdf, state_gdf):
    """Validate that coverage is ≤ 105% and report statistics"""
    print("📊 Validating coverage...")
    
    # Convert to equal-area projection for accurate area calculations
    gdf_area = gdf.to_crs('EPSG:5070')
    state_area = state_gdf.to_crs('EPSG:5070')
    
    # Calculate ZIP3 areas by state
    zip3_by_state = gdf_area.dissolve(by='STUSPS').area
    
    # Calculate original state areas
    state_areas = state_area.set_index('STUSPS').area
    
    # Calculate coverage for common states
    common_states = list(set(zip3_by_state.index) & set(state_areas.index))
    coverage = (zip3_by_state[common_states] / state_areas[common_states]).sort_values()
    
    # Report statistics
    max_coverage = coverage.max()
    mean_coverage = coverage.mean()
    
    print(f"   📈 Coverage Statistics:")
    print(f"      Max coverage: {max_coverage:.1%}")
    print(f"      Mean coverage: {mean_coverage:.1%}")
    print(f"      States >100%: {(coverage > 1.0).sum()}")
    print(f"      States <95%: {(coverage < 0.95).sum()}")
    
    # Show worst offenders
    if max_coverage > 1.0:
        worst_states = coverage[coverage > 1.0].tail(3)
        print(f"   🔺 Highest coverage states:")
        for state, pct in worst_states.items():
            print(f"      {state}: {pct:.1%}")
    
    # Validate assertion
    if max_coverage > 1.05:
        print(f"❌ ERROR: Maximum coverage {max_coverage:.1%} exceeds 105% threshold!")
        print("The trimming process did not work as expected.")
        sys.exit(1)
    else:
        print(f"✅ Coverage validation passed (max: {max_coverage:.1%} ≤ 105%)")
    
    return coverage

def export_results(gdf):
    """Export trimmed results to GeoPackage and Shapefile"""
    print("💾 Exporting trimmed results...")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Export to GeoPackage
    gpkg_path = os.path.join(OUTPUT_DIR, "state_zip3_trimmed.gpkg")
    gdf.to_file(gpkg_path, layer="zip3_state", driver="GPKG")
    print(f"   ✅ GeoPackage saved: {gpkg_path} (layer: zip3_state)")
    
    # Export to Shapefile
    shp_path = os.path.join(OUTPUT_DIR, "state_zip3_trimmed.shp")
    gdf.to_file(shp_path)
    print(f"   ✅ Shapefile saved: {shp_path}")
    
    return gpkg_path, shp_path

def print_summary(gdf, coverage, elapsed_time):
    """Print final summary"""
    num_polygons = len(gdf)
    num_states = gdf['STUSPS'].nunique()
    worst_coverage = coverage.max()
    
    print("\n" + "="*60)
    print("🎯 TRIMMED ZIP3-STATE LAYER COMPLETE!")
    print("="*60)
    print(f"Created {num_polygons} trimmed polygons covering {num_states} states")
    print(f"Worst coverage: {worst_coverage:.1%} (within 105% threshold)")
    print(f"Processing time: {elapsed_time:.1f} seconds")
    print(f"Output files saved to ./{OUTPUT_DIR}/")
    print("\nFor Tableau:")
    print("  1. Replace old layer with state_zip3_trimmed.gpkg")
    print("  2. Join fields remain: STUSPS (state) + ZIP3 (ZIP prefix)")
    print("  3. Enjoy clean state boundaries! 🎉")
    print("="*60)

def main():
    """Main execution function"""
    start_time = time.time()
    
    print("🚀 Starting ZIP3 Overlap Fix (Border Trimming)")
    print("="*60)
    
    # Step 1: Check input files
    check_input_files()
    
    # Step 2: Load reference data for CRS and state list
    target_crs, existing_states = load_reference_data()
    
    # Step 3: Load raw ZCTA and state data
    zcta_gdf, state_gdf = load_and_prepare_raw_data(target_crs, existing_states)
    
    # Step 4: Assign ZIPs to states using within + centroid method
    joined_gdf = assign_zips_to_states(zcta_gdf, state_gdf)
    
    # Step 5: Dissolve by state and ZIP3
    dissolved_gdf = dissolve_and_validate(joined_gdf)
    
    # Step 6: Optional geometry simplification
    simplified_gdf = simplify_geometry_optional(dissolved_gdf)
    
    # Step 7: Validate coverage ≤ 105%
    coverage = validate_coverage(simplified_gdf, state_gdf)
    
    # Step 8: Export results
    export_results(simplified_gdf)
    
    # Step 9: Print summary
    elapsed_time = time.time() - start_time
    print_summary(simplified_gdf, coverage, elapsed_time)

if __name__ == "__main__":
    main()
