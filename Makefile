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
	@echo "  transform   Run main border-trimmed transformation"
	@echo "  fix         Run legacy border-trimmed script"
	@echo "  coverage    Analyze coverage quality"
	@echo "  clean       Remove output files"
	@echo "  all         Run complete pipeline (transform + coverage)"
	@echo ""
	@echo "Usage examples:"
	@echo "  make install"
	@echo "  make transform"
	@echo "  make coverage"

# Install dependencies
install:
	@echo "📦 Installing Python dependencies..."
	python -m pip install -r requirements.txt

# Run main border-trimmed transformation
transform:
	@echo "🚀 Running main border-trimmed ZIP3-state transformation..."
	python transform_zip3.py

# Run legacy border-trimmed script
fix:
	@echo "🎯 Running legacy border-trimmed ZIP3-state script..."
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
all: transform coverage
	@echo "✅ Complete pipeline finished!"

# Windows-compatible targets (using PowerShell)
clean-win:
	@echo "🧹 Cleaning output files (Windows)..."
	if exist out rmdir /s /q out
	if exist state_shp rmdir /s /q state_shp
