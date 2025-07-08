# ZIP3-State Spatial Transformation

# ZIP3-State Spatial Transformation

This project transforms Census ZIP Code Tabulation Areas (ZCTAs) into state-ZIP3 polygons for Tableau visualization. The main script creates border-trimmed dissolved polygons that eliminate overlaps by clipping ZIP polygons to exact state boundaries before dissolving.

## 📋 Prerequisites

- Python 3.8 or higher
- Census ZCTA shapefile: `cb_2018_us_zcta510_500k.zip` from [Census Cartographic Boundary Files](https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html)
- Internet connection (for downloading state boundaries if needed)

## 🔧 Installation

### 1. Install Dependencies

```bash
python -m pip install geopandas requests pyogrio
```

Or install from requirements file:

```bash
python -m pip install -r requirements.txt
```

### 2. Download Required Census Data

Visit: https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html

Download: **2018 ZIP Code Tabulation Areas (ZCTAs)** → `cb_2018_us_zcta510_500k.zip`

Extract the following files to the project root:
- `cb_2018_us_zcta510_500k.shp`
- `cb_2018_us_zcta510_500k.dbf`
- `cb_2018_us_zcta510_500k.shx`
- `cb_2018_us_zcta510_500k.prj`
- `cb_2018_us_zcta510_500k.cpg`

## 🚀 Usage

### Main Transformation (Border-Trimmed)
The main script produces border-trimmed results by default:

```bash
python transform_zip3.py
```

### Legacy Scripts
For comparison purposes, the project includes legacy scripts:
- `fix_zip3_overlap.py` - Original border-trimmed implementation  
- `analyze_coverage.py` - Coverage analysis tool

### Automated Workflow with Makefile
Use the provided Makefile for streamlined processing:

```bash
# Install dependencies
make install

# Generate border-trimmed layer (main script)
make transform

# Legacy: Generate with fix_zip3_overlap.py
make fix

# Analyze coverage
make coverage

# Complete workflow (all steps)
make all

# Clean output files
make clean
```

## 📊 Key Features

### Border-Trimmed Approach
- **No overlaps**: ZCTAs are clipped to state boundaries before dissolving
- **Accurate coverage**: Eliminates >100% coverage issues
- **Spatial precision**: Uses `within` predicate with centroid fallback for boundary-straddling ZIPs
- **Topology fixes**: Applies buffer(0) and optional simplification
- **Coverage validation**: Enforces reasonable coverage thresholds

## 📊 Output Files

The script creates output files in the `./out/` directory:

### Trimmed Layer (Recommended)
- `state_zip3_trimmed.shp` (plus .dbf, .shx, .prj files)
- `state_zip3_trimmed.gpkg` (layer: "zip3_state") - **Recommended for Tableau**

## 🎯 Using with Tableau

### Recommended: Border-Trimmed Layer
For precise coverage without overlaps:

1. **Connect to Spatial File:**
   - Data → Spatial File
   - Select `state_zip3_trimmed.gpkg`
   - Choose layer: `zip3_state`

### Available Fields:
   - `STUSPS`: State abbreviation (e.g., "CA", "TX", "NY")
   - `ZIP3`: Three-digit ZIP prefix (e.g., "900", "021", "100")
   - `geometry`: Polygon geometry

### Data Joining:
   - Join your business data on `STUSPS` (state) and `ZIP3` (ZIP prefix)
   - Use these fields to create choropleth maps by state-ZIP3 regions

## 📁 Project Structure

```
zip3-spatial/
├── cb_2018_us_zcta510_500k.*     # Input ZCTA files (user downloads)
├── transform_zip3.py              # Main transformation script (border-trimmed)
├── fix_zip3_overlap.py            # Legacy border-trimmed implementation
├── analyze_coverage.py            # Data quality analysis script
├── verify_output.py               # Output verification script
├── requirements.txt               # Python dependencies
├── Makefile                       # Automation targets
├── DATA.md                        # Data download instructions
├── README.md                      # This file
├── state_shp/                     # Downloaded state boundaries (auto-created)
│   └── cb_2018_us_state_500k.*
└── out/                           # Output files (auto-created)
    ├── state_zip3_trimmed.gpkg    # Main output (recommended)
    ├── state_zip3_trimmed.shp
    └── associated files...
```

## ⚙️ Script Features

- **Border-Trimmed Approach**: Clips ZIPs to state boundaries for precise coverage
- **Automatic Downloads**: State boundaries downloaded automatically if missing
- **CRS Handling**: Ensures consistent coordinate reference systems
- **Geometry Validation**: Fixes invalid geometries created during processing
- **Performance Optimization**: Simplifies geometry for faster Tableau performance
- **Multiple Output Formats**: Both shapefile and GeoPackage formats
- **Comprehensive Logging**: Detailed progress messages throughout execution

## 🔍 Troubleshooting

### Missing Dependencies
```bash
# Install GeoPandas with all spatial dependencies
conda install -c conda-forge geopandas
# or
pip install geopandas[complete]
```

### Large File Processing
The script includes geometry simplification to handle large datasets efficiently. If you encounter memory issues:
- Ensure you have sufficient RAM (4GB+ recommended)
- Consider processing subsets of states if needed

### Coordinate System Issues
The script automatically handles CRS transformations. All outputs use the same CRS as the input ZCTA data.

## 📈 Expected Results

- **Coverage**: All 50 US states + DC + territories
- **Polygons**: ~900-1,200 state-ZIP3 combinations (border-trimmed)
- **File Sizes**: 
  - Shapefile: ~40-80 MB
  - GeoPackage: ~30-60 MB
- **Coverage**: Maximum ~100-105% (eliminates overlap issues)

## 🤝 Contributing

Feel free to submit issues or improvements to the transformation script.

## 📄 Data Sources

- **ZCTAs**: US Census Bureau 2018 Cartographic Boundary Files
  - Source: https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html
  - File: `cb_2018_us_zcta510_500k.zip`
- **States**: US Census Bureau 2018 Cartographic Boundary Files (500k scale, auto-downloaded)

---

*Generated on ${new Date().toLocaleDateString()}*
- **Accurate coverage**: Eliminates >100% coverage issues
- **Spatial precision**: Uses `within` predicate with centroid fallback for boundary-straddling ZIPs
- **Topology fixes**: Applies buffer(0) and optional simplification
- **Coverage validation**: Enforces max 105% coverage threshold

### Usage
```bash
# Generate border-trimmed layer
python fix_zip3_overlap.py

# Or use Makefile targets
make fix           # Generate trimmed layer
make coverage      # Analyze coverage
make all           # Complete workflow (transform + fix + coverage)
```

### Output
Creates `state_zip3_trimmed.gpkg` in `./out/` directory with:
- Precise state-ZIP3 polygons clipped to state boundaries
- Validated coverage ≤105% for all regions
- Optimized geometry for visualization

## 🚀 Usagetransforms Census ZIP Code Tabulation Areas (ZCTAs) into state-ZIP3 polygons for Tableau visualization. The script creates dissolved polygons representing the intersection of state boundaries and the first three digits of ZIP codes.

## 📋 Prerequisites

- Python 3.8 or higher
- Census ZCTA shapefile: `cb_2018_us_zcta510_500k.shp` (and associated files)
- Internet connection (for downloading state boundaries if needed)

## 🔧 Installation

### 1. Install Dependencies

```bash
python -m pip install geopandas requests pyogrio
```

Or install from requirements file:

```bash
python -m pip install -r requirements.txt
```

### 2. Verify Required Files

Ensure the following Census ZCTA files are in the project root:
- `cb_2018_us_zcta510_500k.shp`
- `cb_2018_us_zcta510_500k.dbf`
- `cb_2018_us_zcta510_500k.shx`
- `cb_2018_us_zcta510_500k.prj`

## � Data Quality & Coverage

The transformation creates high-quality ZIP3-state polygons with excellent coverage:

### Coverage Analysis Results
- **46 states (82%)**: Excellent coverage (≥95%)
- **4 states (7%)**: Good coverage (85-94%) 
- **3 states (5%)**: Fair coverage (75-84%)
- **3 states (5%)**: Poor coverage (<75%): AK, MP, NV

### Coverage Limitations
- **Alaska (AK)**: 41% coverage due to sparse population and vast wilderness
- **Northern Mariana Islands (MP)**: 64% coverage 
- **Nevada (NV)**: 72% coverage due to large desert areas
- **Some states show >100% coverage** due to ZIP boundary overlaps or differences between Census boundaries

### Quality Validation
Run the coverage analysis: `python analyze_coverage.py`

## �🚀 Usage

Run the transformation script:

```bash
python transform_zip3.py
```

### Validate Results (Optional)

Check data quality and coverage:

```bash
python analyze_coverage.py
```

Verify output files:

```bash
python verify_output.py
```

The script will:
1. ✅ Verify required ZCTA files exist
2. 📥 Download state boundaries if needed (automatic)
3. 🔗 Spatially join ZCTAs to states
4. 🔄 Dissolve by state and ZIP3 prefix
5. ⚡ Simplify geometry for performance
6. 💾 Export results to multiple formats

## 📊 Output Files

The script creates two output files in the `./out/` directory:

### Shapefile
- `state_zip3_dissolved.shp` (plus .dbf, .shx, .prj files)

### GeoPackage (Recommended for Tableau)
- `state_zip3_dissolved.gpkg` (layer: "zip3_state")

## 🎯 Using with Tableau

### Recommended: Border-Trimmed Layer
For precise coverage without overlaps, use the trimmed layer:

1. **Connect to Spatial File:**
   - Data → Spatial File
   - Select `state_zip3_trimmed.gpkg`
   - Choose layer: `zip3_state`

### Alternative: Standard Dissolved Layer
For general use (may have minor overlaps):

1. **Connect to Spatial File:**
   - Data → Spatial File
   - Select `state_zip3_dissolved.gpkg`
   - Choose layer: `zip3_state`

### Available Fields (Both Layers):
   - `STUSPS`: State abbreviation (e.g., "CA", "TX", "NY")
   - `ZIP3`: Three-digit ZIP prefix (e.g., "900", "021", "100")
   - `geometry`: Polygon geometry

### Data Joining:
   - Join your business data on `STUSPS` (state) and `ZIP3` (ZIP prefix)
   - Use these fields to create choropleth maps by state-ZIP3 regions

## 📁 Project Structure

```
zip3-spatial/
├── cb_2018_us_zcta510_500k.*     # Input ZCTA files
├── transform_zip3.py              # Original transformation script
├── fix_zip3_overlap.py            # Border-trimmed layer script (recommended)
├── analyze_coverage.py            # Data quality analysis script
├── verify_output.py               # Output verification script
├── requirements.txt               # Python dependencies
├── Makefile                       # Automation targets
├── README.md                      # This file
├── state_shp/                     # Downloaded state boundaries (auto-created)
│   └── cb_2018_us_state_500k.*
└── out/                           # Output files (auto-created)
    ├── state_zip3_dissolved.shp   # Standard dissolved layer
    ├── state_zip3_dissolved.gpkg
    ├── state_zip3_trimmed.gpkg    # Border-trimmed layer (recommended)
    └── associated files...
```

## ⚙️ Script Features

- **Automatic Downloads**: State boundaries downloaded automatically if missing
- **CRS Handling**: Ensures consistent coordinate reference systems
- **Geometry Validation**: Fixes invalid geometries created during processing
- **Performance Optimization**: Simplifies geometry for faster Tableau performance
- **Multiple Output Formats**: Both shapefile and GeoPackage formats
- **Comprehensive Logging**: Detailed progress messages throughout execution

## 🔍 Troubleshooting

### Missing Dependencies
```bash
# Install GeoPandas with all spatial dependencies
conda install -c conda-forge geopandas
# or
pip install geopandas[complete]
```

### Large File Processing
The script includes geometry simplification to handle large datasets efficiently. If you encounter memory issues:
- Ensure you have sufficient RAM (4GB+ recommended)
- Consider processing subsets of states if needed

### Coordinate System Issues
The script automatically handles CRS transformations. All outputs use the same CRS as the input ZCTA data.

## 📈 Expected Results

- **Coverage**: All 50 US states + DC
- **Polygons**: ~1,500-2,000 state-ZIP3 combinations
- **File Sizes**: 
  - Shapefile: ~50-100 MB
  - GeoPackage: ~40-80 MB

## 🤝 Contributing

Feel free to submit issues or improvements to the transformation script.

## 📄 Data Sources

- **ZCTAs**: US Census Bureau 2018 Cartographic Boundary Files
- **States**: US Census Bureau 2018 Cartographic Boundary Files (500k scale)

---

*Generated on ${new Date().toLocaleDateString()}*
