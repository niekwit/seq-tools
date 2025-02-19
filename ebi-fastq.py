"""
Before running the script, create a conda environment with the following packages:
conda create -n ena conda-forge::python=3.13.2 conda-forge::requests=2.32.3 conda-forge::bs4=4.13.3 conda-forge::tqdm=4.67.1
conda activate ena
"""

import argparse
import csv
import os
import subprocess

VERSION = "v0.5.0"

def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", "-o", 
                        type=str,
                        required=True,
                        help="Output directory")
    parser.add_argument("--csv", "-c", 
                        type=str,
                        required=True,
                        help="CSV file with SRA accession and sample name on different rows")
    parser.add_argument("--paired", "-p",
                        action="store_true",
                        help="Paired-end reads")
    parser.add_argument("--version", "-v",
                        action="version",
                        version=f"%(prog)s {VERSION}")
    return parser.parse_args()


def download_file(url, file_name):
    cmd = ["curl", "-L", url, "-o", file_name]
    subprocess.run(cmd)


def get_fastq(srr, sample_name):
    EBI_BASE_URL = "ftp://ftp.sra.ebi.ac.uk/vol1/fastq"
    
    # Get last two characters of SRR
    srr_suffix = f"0{srr[-2:]}"

    # Get first six characters of SRR
    ssr_prefix = srr[:6]
    
    # Construct URLs for read 1 and read 2
    base_url = f"{EBI_BASE_URL}/{ssr_prefix}/{srr_suffix}/{srr}/{srr}"
    read_suffix = ["1", "2"] #if args.paired else ["1"]
    for suffix in read_suffix:
        url = f"{base_url}_{suffix}.fastq.gz"
        outfile = f"{OUTDIR}/{sample_name}_R{suffix}_001.fastq.gz"
        print(f"Downloading {url} to {outfile}")
        download_file(url, outfile)
    

def main(args):
    """Read CSV and process each sample."""
    global OUTDIR
    OUTDIR = args.outdir
    os.makedirs(OUTDIR, exist_ok=True)
    csv_file = args.csv
    paired = args.paired
    
    with open(csv_file, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            srr, sample_name = row
            get_fastq(srr, sample_name)


if __name__ == "__main__":
    args = args()
    main(args)
