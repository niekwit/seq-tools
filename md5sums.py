#!/usr/bin/env python3
"""
Checks md5sums of fastq files
"""
import os
import hashlib
import glob
import csv
import pandas as pd

def md5(file):
    """
    Calculate the md5sum of a file
    """
    file = os.path.join("reads", file)
    hash_md5 = hashlib.md5()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return(hash_md5.hexdigest())

# Get md5sum files
md5sum_files = glob.glob(os.path.join("reads","*.md5"))
if len(md5sum_files) == 0:
    md5sum_files = glob.glob(os.path.join("reads","*.md5sums.txt"))
    if len(md5sum_files) == 0:
        raise ValueError("No md5sum files found with extensions .md5 or .md5sums.txt...")
    
# Read in the md5sum files
files = []
md5sums_txt = []
md5sums_calculated = []
for md5sum_file in md5sum_files:
    with open(md5sum_file, "r") as csvfile:
        reader = csv.reader(csvfile, delimiter=' ')
        for row in reader:
            row = [x for x in row if x != ""]
            print(f"Checking md5sum for {row[1]}...")
            files.append(row[1])
            md5sums_txt.append(row[0])
            md5sums_calculated.append(md5(row[1]))
            
# Create a pandas dataframe
print("Writing results to md5sums.csv...")
df = pd.DataFrame(data={"file": files, 
                        "md5sum_txt": md5sums_txt, 
                        "md5sum_calculated": md5sums_calculated})

df["md5sum_match"] = df["md5sum_txt"] == df["md5sum_calculated"]

# Write df to file
df.to_csv("md5sums.csv", index=False)
print("Done!")