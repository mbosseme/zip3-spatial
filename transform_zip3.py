#!/usr/bin/env python3
"""
ZIP3-State Spatial Transformation Script

This script transforms Census ZCTA (ZIP Code Tabulation Areas) data into 
state-ZIP3 polygons for Tableau visualization. It creates dissolved polygons 
representing the intersection of state boundaries and first-three-digit ZIP prefixes.

Requirements:
- cb_2018_us_zcta510_500k.shp (and associated files) must be present
- Internet connection for downloading state boundaries if needed
- GeoPandas ≥0.14, Pandas, and Requests

Output:
- ./out/state_zip3_dissolved.shp
- ./out/state_zip3_dissolved.gpkg (layer="zip3_state")
"""

import os
import sys
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

def spatial_join_and_filter(zcta_gdf, state_gdf):
    """Perform spatial join and filter problematic geometries"""
    print("🔗 Performing spatial join (ZCTAs to states)...")
    
    # Spatial join using 'intersects' predicate
    joined_gdf = gpd.sjoin(zcta_gdf, state_gdf, how='inner', predicate='intersects')
    
    # Drop the index column created by sjoin
    joined_gdf = joined_gdf.drop(columns=['index_right'])
    
    print(f"   Joined {len(joined_gdf)} ZCTA-state combinations")
    
    # Filter out problematic Alaskan/Hawaiian multipolygons if needed
    # Keep only simple polygons or well-formed multipolygons
    original_count = len(joined_gdf)
    joined_gdf = joined_gdf[joined_gdf.geometry.is_valid].copy()
    
    if len(joined_gdf) < original_count:
        print(f"   Filtered out {original_count - len(joined_gdf)} invalid geometries")
    
    return joined_gdf

def dissolve_by_state_zip3(joined_gdf):
    """Dissolve by state and ZIP3 to create final polygons"""
    print("🔄 Dissolving by State × ZIP3...")
    
    # Group by state and ZIP3, then dissolve
    dissolved_gdf = joined_gdf.dissolve(by=['STUSPS', 'ZIP3']).reset_index()
    
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
    """Export results to both shapefile and GeoPackage"""
    print("💾 Exporting results...")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Export to shapefile
    shp_path = os.path.join(OUTPUT_DIR, "state_zip3_dissolved.shp")
    gdf.to_file(shp_path)
    print(f"   ✅ Shapefile saved: {shp_path}")
    
    # Export to GeoPackage
    gpkg_path = os.path.join(OUTPUT_DIR, "state_zip3_dissolved.gpkg")
    gdf.to_file(gpkg_path, layer="zip3_state", driver="GPKG")
    print(f"   ✅ GeoPackage saved: {gpkg_path} (layer: zip3_state)")
    
    return shp_path, gpkg_path

def print_summary(gdf):
    """Print concise summary of results"""
    num_polygons = len(gdf)
    num_states = gdf['STUSPS'].nunique()
    
    print("\n" + "="*60)
    print("📊 TRANSFORMATION COMPLETE!")
    print("="*60)
    print(f"Created {num_polygons} polygons covering {num_states} states")
    print(f"Output files saved to ./{OUTPUT_DIR}/")
    print("\nFor Tableau:")
    print("  1. Data → Spatial File → Select state_zip3_dissolved.gpkg")
    print("  2. Choose layer: zip3_state")
    print("  3. Join on: STUSPS (state) and ZIP3 (ZIP prefix)")
    print("="*60)

def main():
    """Main execution function"""
    print("🚀 Starting ZIP3-State Spatial Transformation")
    print("="*60)
    
    # Step 1: Safety check
    check_zcta_files()
    
    # Step 2: Download state boundaries if needed
    download_state_boundaries()
    
    # Step 3: Load and prepare data
    zcta_gdf, state_gdf = load_and_prepare_data()
    
    # Step 4: Ensure same CRS
    zcta_gdf, state_gdf = ensure_same_crs(zcta_gdf, state_gdf)
    
    # Step 5: Spatial join and filter
    joined_gdf = spatial_join_and_filter(zcta_gdf, state_gdf)
    
    # Step 6: Dissolve by state and ZIP3
    dissolved_gdf = dissolve_by_state_zip3(joined_gdf)
    
    # Step 7: Simplify geometry (optional)
    simplified_gdf = simplify_geometry(dissolved_gdf)
    
    # Step 8: Export results
    export_results(simplified_gdf)
    
    # Step 9: Print summary
    print_summary(simplified_gdf)

if __name__ == "__main__":
    main()
