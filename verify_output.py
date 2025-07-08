#!/usr/bin/env python3
"""
Quick verification script to check the output of the ZIP3-state transformation.
"""

import geopandas as gpd
import pandas as pd

def verify_outputs():
    """Verify the created output files"""
    print("🔍 Verifying ZIP3-State transformation outputs...")
    print("=" * 50)
    
    # Check shapefile
    try:
        shp_gdf = gpd.read_file("out/state_zip3_dissolved.shp")
        print(f"✅ Shapefile loaded: {len(shp_gdf)} polygons")
        print(f"   Columns: {list(shp_gdf.columns)}")
        print(f"   States covered: {shp_gdf['STUSPS'].nunique()}")
        print(f"   ZIP3 prefixes: {shp_gdf['ZIP3'].nunique()}")
    except Exception as e:
        print(f"❌ Error loading shapefile: {e}")
    
    # Check GeoPackage
    try:
        gpkg_gdf = gpd.read_file("out/state_zip3_dissolved.gpkg", layer="zip3_state")
        print(f"✅ GeoPackage loaded: {len(gpkg_gdf)} polygons")
        print(f"   Columns: {list(gpkg_gdf.columns)}")
    except Exception as e:
        print(f"❌ Error loading GeoPackage: {e}")
    
    # Sample data preview
    if 'shp_gdf' in locals():
        print("\n📊 Sample data:")
        print(shp_gdf[['STUSPS', 'ZIP3']].head(10))
        
        # Check for some expected states and ZIP codes
        ca_zips = shp_gdf[shp_gdf['STUSPS'] == 'CA']['ZIP3'].unique()
        ny_zips = shp_gdf[shp_gdf['STUSPS'] == 'NY']['ZIP3'].unique()
        
        print(f"\n🌟 California ZIP3 prefixes: {sorted(ca_zips)[:10]}...")
        print(f"🗽 New York ZIP3 prefixes: {sorted(ny_zips)[:10]}...")
    
    print("\n✅ Verification complete!")

if __name__ == "__main__":
    verify_outputs()
