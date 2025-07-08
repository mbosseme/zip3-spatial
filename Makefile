# ZIP3-State Spatial Transformation Makefile
# Simple automation for common tasks

.PHONY: help transform fix coverage clean install

# Default target
help:
	@echo "ZIP3-State Spatial Transformation"
	@echo "================================="
	@echo ""
	@echo "Available targets:"
	@echo "  install     Install Python dependencies"
	@echo "  transform   Run initial ZIP3-state transformation"
	@echo "  fix         Run border-trimmed ZIP3-state fix"
	@echo "  coverage    Analyze coverage quality"
	@echo "  clean       Remove output files"
	@echo "  all         Run complete pipeline (transform + fix + coverage)"
	@echo ""
	@echo "Usage examples:"
	@echo "  make install"
	@echo "  make transform"
	@echo "  make fix"

# Install dependencies
install:
	@echo "📦 Installing Python dependencies..."
	python -m pip install -r requirements.txt

# Run initial transformation
transform:
	@echo "🚀 Running initial ZIP3-state transformation..."
	python transform_zip3.py

# Run overlap fix
fix:
	@echo "🎯 Running border-trimmed ZIP3-state fix..."
	python fix_zip3_overlap.py

# Run coverage analysis
coverage:
	@echo "📊 Running coverage analysis..."
	python analyze_coverage.py

# Clean output files
clean:
	@echo "🧹 Cleaning output files..."
	rm -rf out/
	rm -rf state_shp/

# Run complete pipeline
all: transform fix coverage
	@echo "✅ Complete pipeline finished!"

# Windows-compatible targets (using PowerShell)
clean-win:
	@echo "🧹 Cleaning output files (Windows)..."
	if exist out rmdir /s /q out
	if exist state_shp rmdir /s /q state_shp
