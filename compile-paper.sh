#!/bin/bash
# Zone-Tritone Canon Paper Compilation Script
# Compiles the academic LaTeX paper to PDF

echo "=================================================="
echo "  Zone-Tritone System - Academic Paper Builder   "
echo "=================================================="
echo ""

# Check if pdflatex is available
if ! command -v pdflatex &> /dev/null; then
    echo "ERROR: pdflatex not found!"
    echo ""
    echo "Please install a LaTeX distribution:"
    echo "  - macOS:   brew install --cask mactex"
    echo "  - Linux:   sudo apt install texlive-full"
    echo ""
    exit 1
fi

# Navigate to papers directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PAPERS_DIR="$SCRIPT_DIR/papers"

if [ ! -d "$PAPERS_DIR" ]; then
    echo "ERROR: papers/ directory not found!"
    exit 1
fi

cd "$PAPERS_DIR"
echo "Working directory: $PAPERS_DIR"
echo ""

# Compile the paper (run twice for cross-references)
echo "Compiling zone_tritone_canon.tex..."
echo ""

echo "[Pass 1/2] First compilation..."
pdflatex -interaction=nonstopmode zone_tritone_canon.tex > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "ERROR: First compilation failed!"
    echo "Check zone_tritone_canon.log for details"
    exit 1
fi

echo "[Pass 2/2] Second compilation (for cross-references)..."
pdflatex -interaction=nonstopmode zone_tritone_canon.tex > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "ERROR: Second compilation failed!"
    echo "Check zone_tritone_canon.log for details"
    exit 1
fi

# Check if PDF was generated
if [ -f "zone_tritone_canon.pdf" ]; then
    echo ""
    echo "SUCCESS! Paper compiled successfully."
    echo ""
    echo "Generated file:"
    echo "  papers/zone_tritone_canon.pdf"
    echo ""
    
    # Get file size
    FILE_SIZE=$(du -h zone_tritone_canon.pdf | cut -f1)
    echo "File size: $FILE_SIZE"
    echo ""
    
    # Clean up auxiliary files (optional)
    echo "Cleaning up auxiliary files..."
    rm -f *.aux *.log *.out
    
    echo ""
    echo "To view the PDF, run:"
    echo "  open papers/zone_tritone_canon.pdf    (macOS)"
    echo "  xdg-open papers/zone_tritone_canon.pdf (Linux)"
    echo ""
    
else
    echo "ERROR: PDF was not generated!"
    echo "Check zone_tritone_canon.log for compilation errors"
    exit 1
fi

echo "=================================================="
