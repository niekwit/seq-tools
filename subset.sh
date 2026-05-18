#!/bin/bash

# Create the output directory if it doesn't exist
mkdir -p subset

# Loop through all .fastq.gz files in the current directory
for file in *.fastq.gz; do
    # Ensure the file exists (prevents errors if no files match the pattern)
    [ -e "$file" ] || continue
    
    echo "Processing $file..."
    
    # Decompress, take first 400k lines (100k reads), and compress to the subfolder
    zcat "$file" | head -n 400000 | gzip > "subset/$file"
done

echo "Done! Subsets are located in the 'subset' folder."