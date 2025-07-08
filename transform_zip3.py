#!/usr/bin/env python3
"""
ZIP3-State Spatial Transformation Script (Border-Trimmed Version)

This script transforms Census ZCTA (ZIP Code Tabulation Areas) data into 
state-ZIP3 polygons for Tableau visualization. It creates dissolved polygons 
with precise state boundaries by clipping ZIPs to state borders before dissolving.

This replaces the original script and produces border-trimmed polygons that 
eliminate >100% coverage issues caused by ZIP boundary overlaps.

Requirements:
- cb_2018_us_zcta510_500k.shp (and associated files) from Census Bureau
- Internet connection for downloading state boundaries if needed
- GeoPandas ≥0.14, pyogrio, Pandas, and Requests

Output:
- ./out/state_zip3_trimmed.shp
- ./out/state_zip3_trimmed.gpkg (layer="zip3_state")
"""

import os
import sys
import time
import zipfile
import requests
import geopandas as gpd
import pandas as pd
from pathlib import Path
import warnings
import urllib3
warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
ZCTA_BASE_NAME = "cb_2018_us_zcta510_500k"
STATE_URL = "https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_500k.zip"
STATE_DIR = "state_shp"
OUTPUT_DIR = "out"
STATE_BASE_NAME = "cb_2018_us_state_500k"

def check_zcta_files():
    """Safety check: verify ZCTA files exist"""
    required_extensions = ['.shp', '.dbf', '.shx', '.prj']
    missing_files = []
    
    for ext in required_extensions:
        file_path = f"{ZCTA_BASE_NAME}{ext}"
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ ERROR: Missing required ZCTA files: {', '.join(missing_files)}")
        print(f"Please ensure {ZCTA_BASE_NAME}.shp and associated files are in the current directory.")
        sys.exit(1)
    
    print("✅ ZCTA files found successfully")

def download_state_boundaries():
    """Download state boundary shapefile if not present"""
    state_shp_path = os.path.join(STATE_DIR, f"{STATE_BASE_NAME}.shp")
    
    if os.path.exists(state_shp_path):
        print("✅ State boundary files already exist")
        return
    
    print("📥 Downloading state boundary shapefile...")
    os.makedirs(STATE_DIR, exist_ok=True)
    
    try:
        # Handle SSL issues that may occur with some environments
        response = requests.get(STATE_URL, stream=True, verify=False)
        response.raise_for_status()
        
        zip_path = os.path.join(STATE_DIR, "states.zip")
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("📦 Extracting state boundary files...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(STATE_DIR)
        
        # Clean up zip file
        os.remove(zip_path)
        print("✅ State boundary files downloaded and extracted")
        
    except requests.RequestException as e:
        print(f"❌ ERROR: Failed to download state boundaries: {e}")
        sys.exit(1)
    except zipfile.BadZipFile as e:
        print(f"❌ ERROR: Invalid zip file downloaded: {e}")
        sys.exit(1)

def load_and_prepare_data():
    """Load both shapefiles and prepare data"""
    print("📊 Loading ZCTA data...")
    
    # Load ZCTA data
    zcta_gdf = gpd.read_file(f"{ZCTA_BASE_NAME}.shp")
    print(f"   Loaded {len(zcta_gdf)} ZCTA polygons")
    
    # Keep only required columns and add ZIP3
    zcta_gdf = zcta_gdf[['GEOID10', 'geometry']].copy()
    zcta_gdf['ZIP3'] = zcta_gdf['GEOID10'].str[:3]
    
    # Load state data
    print("📊 Loading state boundary data...")
    state_shp_path = os.path.join(STATE_DIR, f"{STATE_BASE_NAME}.shp")
    state_gdf = gpd.read_file(state_shp_path)
    print(f"   Loaded {len(state_gdf)} state polygons")
    
    # Keep only required state columns
    state_gdf = state_gdf[['STATEFP', 'STUSPS', 'geometry']].copy()
    
    return zcta_gdf, state_gdf

def ensure_same_crs(zcta_gdf, state_gdf):
    """Ensure both layers share the same CRS"""
    print("🗺️  Checking coordinate reference systems...")
    
    zcta_crs = zcta_gdf.crs
    state_crs = state_gdf.crs
    
    print(f"   ZCTA CRS: {zcta_crs}")
    print(f"   State CRS: {state_crs}")
    
    if zcta_crs != state_crs:
        print("   Reprojecting state boundaries to match ZCTA CRS...")
        state_gdf = state_gdf.to_crs(zcta_crs)
    
    return zcta_gdf, state_gdf

def spatial_join_and_clip(zcta_gdf, state_gdf):
    """Assign ZIPs to states and clip to state boundaries (border-trimmed approach)"""
    print("🎯 Assigning ZIPs to states using 'within' predicate...")
    
    # First, try spatial join with 'within' predicate for clean assignments
    within_join = gpd.sjoin(zcta_gdf, state_gdf, how='inner', predicate='within')
    within_join = within_join.drop(columns=['index_right'])
    print(f"   {len(within_join)} ZIPs assigned via 'within' predicate")
    
    # Find ZIPs that straddle state boundaries (not captured by 'within')
    assigned_zips = set(within_join['GEOID10'])
    straddling_zips = zcta_gdf[~zcta_gdf['GEOID10'].isin(assigned_zips)].copy()
    print(f"   {len(straddling_zips)} border-straddling ZIPs need centroid assignment")
    
    # For straddling ZIPs, use centroid-based assignment
    if len(straddling_zips) > 0:
        centroids = straddling_zips.copy()
        centroids['geometry'] = centroids.geometry.centroid
        centroid_join = gpd.sjoin(centroids, state_gdf, how='inner', predicate='within')
        centroid_join = centroid_join.drop(columns=['index_right'])
        
        # Restore original geometry for centroid-assigned ZIPs
        centroid_join['geometry'] = straddling_zips.set_index('GEOID10').loc[centroid_join['GEOID10'], 'geometry'].values
        
        print(f"   {len(centroid_join)} ZIPs assigned via centroid method")
        
        # Combine both assignment methods
        all_assigned = pd.concat([within_join, centroid_join], ignore_index=True)
    else:
        all_assigned = within_join
    
    print(f"   Total assigned: {len(all_assigned)} ZIPs to states")
    
    # Warn about unassigned ZIPs
    total_unassigned = len(zcta_gdf) - len(all_assigned)
    if total_unassigned > 0:
        print(f"   ⚠️  {total_unassigned} ZIPs could not be assigned to any state")
    
    # Now clip ZIP geometries to state boundaries
    print("✂️  Clipping ZIP geometries to state boundaries...")
    clipped_parts = []
    
    for state in state_gdf['STUSPS'].unique():
        state_geom = state_gdf[state_gdf['STUSPS'] == state].geometry.iloc[0]
        state_zips = all_assigned[all_assigned['STUSPS'] == state].copy()
        
        if len(state_zips) > 0:
            # Clip ZIPs to state boundary
            state_zips['geometry'] = state_zips.geometry.intersection(state_geom)
            clipped_parts.append(state_zips)
    
    if clipped_parts:
        clipped_gdf = pd.concat(clipped_parts, ignore_index=True)
        # Remove any empty geometries created by clipping
        clipped_gdf = clipped_gdf[~clipped_gdf.geometry.is_empty].copy()
        print(f"   Clipped to {len(clipped_gdf)} state-constrained ZIP polygons")
        return clipped_gdf
    else:
        print("   ❌ No valid clipped geometries created")
        return gpd.GeoDataFrame()

def dissolve_by_state_zip3(clipped_gdf):
    """Dissolve by state and ZIP3 to create final trimmed polygons"""
    print("🔄 Dissolving by State × ZIP3...")
    
    # Group by state and ZIP3, then dissolve
    dissolved_gdf = clipped_gdf.dissolve(by=['STUSPS', 'ZIP3']).reset_index()
    
    print("🔧 Fixing geometry issues...")
    # Fix any invalid geometries created by dissolve
    dissolved_gdf['geometry'] = dissolved_gdf['geometry'].buffer(0)
    
    # Keep only the required columns
    dissolved_gdf = dissolved_gdf[['STUSPS', 'ZIP3', 'geometry']].copy()
    
    print(f"   Created {len(dissolved_gdf)} dissolved polygons")
    
    return dissolved_gdf

def simplify_geometry(gdf):
    """Simplify geometry for better performance (optional)"""
    print("⚡ Simplifying geometry for performance...")
    
    original_crs = gdf.crs
    
    # Convert to Web Mercator for simplification
    gdf_mercator = gdf.to_crs('EPSG:3857')
    
    # Simplify with 100m tolerance
    gdf_mercator['geometry'] = gdf_mercator['geometry'].simplify(tolerance=100)
    
    # Convert back to original CRS
    gdf_simplified = gdf_mercator.to_crs(original_crs)
    
    return gdf_simplified

def export_results(gdf):
    """Export trimmed results to both shapefile and GeoPackage"""
    print("💾 Exporting trimmed results...")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Export to shapefile
    shp_path = os.path.join(OUTPUT_DIR, "state_zip3_trimmed.shp")
    gdf.to_file(shp_path)
    print(f"   ✅ Shapefile saved: {shp_path}")
    
    # Export to GeoPackage
    gpkg_path = os.path.join(OUTPUT_DIR, "state_zip3_trimmed.gpkg")
    gdf.to_file(gpkg_path, layer="zip3_state", driver="GPKG")
    print(f"   ✅ GeoPackage saved: {gpkg_path} (layer: zip3_state)")
    
    return shp_path, gpkg_path

def print_summary(gdf, processing_time=None):
    """Print concise summary of results"""
    num_polygons = len(gdf)
    num_states = gdf['STUSPS'].nunique()
    
    print("\n" + "="*60)
    print("🎯 BORDER-TRIMMED ZIP3-STATE LAYER COMPLETE!")
    print("="*60)
    print(f"Created {num_polygons} trimmed polygons covering {num_states} states")
    if processing_time:
        print(f"Processing time: {processing_time:.1f} seconds")
    print(f"Output files saved to ./{OUTPUT_DIR}/")
    print("\nFor Tableau:")
    print("  1. Data → Spatial File → Select state_zip3_trimmed.gpkg")
    print("  2. Choose layer: zip3_state")
    print("  3. Join on: STUSPS (state) and ZIP3 (ZIP prefix)")
    print("  4. Enjoy clean state boundaries! 🎉")
    print("="*60)

def main():
    """Main execution function"""
    start_time = time.time()
    
    print("🚀 Starting ZIP3-State Border-Trimmed Transformation")
    print("="*60)
    
    # Step 1: Safety check
    check_zcta_files()
    
    # Step 2: Download state boundaries if needed
    download_state_boundaries()
    
    # Step 3: Load and prepare data
    zcta_gdf, state_gdf = load_and_prepare_data()
    
    # Step 4: Ensure same CRS
    zcta_gdf, state_gdf = ensure_same_crs(zcta_gdf, state_gdf)
    
    # Step 5: Spatial join and clip to state boundaries
    clipped_gdf = spatial_join_and_clip(zcta_gdf, state_gdf)
    
    # Step 6: Dissolve by state and ZIP3
    dissolved_gdf = dissolve_by_state_zip3(clipped_gdf)
    
    # Step 7: Simplify geometry (optional)
    simplified_gdf = simplify_geometry(dissolved_gdf)
    
    # Step 8: Export results
    export_results(simplified_gdf)
    
    # Step 9: Print summary with timing
    processing_time = time.time() - start_time
    print_summary(simplified_gdf, processing_time)

if __name__ == "__main__":
    main()
