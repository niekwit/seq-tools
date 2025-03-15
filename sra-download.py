"""
Before running the script, create a conda environment with the following packages:
conda create -n sra bioconda::sra-tools=3.2.0 conda-forge::python=3.13.2 conda-forge::pigz=2.8
conda activate sra
"""

import argparse
import datetime
import os
import shutil
import subprocess
import csv
import logging
import glob as glob
import tempfile

VERSION = "v0.5"

def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", "-o", 
                        type=str, 
                        help="Output directory")
    parser.add_argument("--csv", "-c", 
                        type=str, 
                        help="CSV file with SRA accession and sample name on different rows")
    parser.add_argument("--threads", "-t", 
                        type=int, 
                        help="Number of CPU threads to use")
    parser.add_argument("--paired", "-p",
                        action="store_true",
                        help="Paired-end reads")
    parser.add_argument("--version", "-v",
                        action="version",
                        version=f"%(prog)s {VERSION}")
    return parser.parse_args()


def download(sra, tmpdir):
    logging.info(f"Downloading {sra}...")
    cmd = [
        "prefetch", "--progress", "--max-size", "100G", sra, 
        "--output-directory", tmpdir
        ]
    subprocess.run(cmd)
    
    # Return the downloaded file path
    file = glob.glob(os.path.join(tmpdir, "*", f"*.sra"))
    assert len(file) == 1
    validate(file[0])
    convert(file[0], tmpdir)


def validate(sra_file):
    logging.info(f"Validating {sra_file}...")
    cmd = ["vdb-validate", sra_file]
    subprocess.run(cmd)


def convert(sra_file, tmpdir):
   logging.info(f"Converting {sra_file} to fastq...")
   cmd = ["fasterq-dump", sra_file, "--progress","--split-files", "--threads", THREADS, "--outdir", tmpdir]
   subprocess.run(cmd)


def compress(name, tmpdir, targetdir):
    # Get fastq files
    fastq_files = glob.glob(os.path.join(tmpdir, "*.fastq"))
    
    for i, file in enumerate(fastq_files):
        outfile = os.path.join(targetdir, f"{name}_R{i+1}_001.fastq.gz")
        logging.info(f"Compressing {file} to {outfile}...")
        cmd = ["pigz", "--processes", THREADS, file]
        subprocess.run(cmd)
        shutil.move(f"{file}.gz", outfile)
        
    logging.info("Compressing fastq files complete...")    


def main(outdir, csv_file):
    # Set up logging    
    current_time = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
    log = f"sra-download-{current_time}.log"
    logging.basicConfig(
        format="%(levelname)s:%(asctime)s:%(message)s",
        level=logging.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(log),
                              logging.StreamHandler()],
    )
    
    # Create outdir
    os.makedirs(outdir, exist_ok=True)
    
    # Read CSV file and download SRA files
    with open(csv_file, "r") as f:
        reader = csv.reader(f)
        
        for row in reader:
            sra = row[0]
            name = row[1]
            
            with tempfile.TemporaryDirectory() as tmpdirname:
                logging.info(f"Created temporary directory {tmpdirname}...")
                download(sra, tmpdirname)
                compress(name, tmpdirname, outdir)
                logging.info(f"Finished processing {sra}...")
                
    logging.info("Finished processing all SRA files!")       


if __name__ == "__main__":
    # Get command line arguments
    args = args()
    
    global THREADS
    THREADS = str(args.threads)
    outdir = args.outdir
    csv_file = args.csv
    
    main(outdir, csv_file)
            
