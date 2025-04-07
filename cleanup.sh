#!/bin/bash

# Remove output directory and files
echo "Removing output files..."
rm -rf output/
rm -f structure.yaml

# Remove generated markdown
echo "Removing markdown files..."
rm -f *.md
rm -f output.md

echo "Cleanup complete!" 