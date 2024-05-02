#!/usr/bin/env python3
"""
Checks md5sums of fastq files in parsed directory
"""
import os
import hashlib
import glob
import csv
import sys

def md5(file):
    """
    Calculate the md5sum of a file
    """
    file = os.path.join(data_dir, file)
    hash_md5 = hashlib.md5()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return(hash_md5.hexdigest())

# Get reads directory from command line
if len(sys.argv) == 1:
    raise ValueError("Please provide the reads directory as an argument...")
elif len(sys.argv) > 2:
    raise ValueError("Please provide only one directory argument...")
else:
    data_dir = sys.argv[1]

# Get md5sum files
md5sum_files = glob.glob(os.path.join(data_dir, "*.md5"))
if len(md5sum_files) == 0:
    md5sum_files = glob.glob(os.path.join(data_dir, "*.md5sums.txt"))
    if len(md5sum_files) == 0:
        raise ValueError("No md5sum files found with extensions .md5 or .md5sums.txt...")
    
# Read in the md5sum files and check the md5sums
with open("md5sums.csv", "w") as outfile:
    writer = csv.writer(outfile, delimiter=',')
    
    # Write header to outfile
    writer.writerow(["file", 
                     "md5sum_txt", 
                     "md5sum_calculated", 
                     "md5sum_match"])
    
    for md5sum_file in md5sum_files:
        with open(md5sum_file, "r") as csvfile:
            reader = csv.reader(csvfile, delimiter=' ')
            
            for row in reader:
                # Tidy up row
                row = [x for x in row if x != ""]
                print(f"Checking md5sum for {row[1]}...")
                md5sums_txt=row[0]                
                file = row[1]
                md5sums_calculated = md5(row[1])

                # Write to outfile
                writer.writerow([file, 
                                 md5sums_txt, 
                                 md5sums_calculated, 
                                 md5sums_txt == md5sums_calculated])
print("Done!")