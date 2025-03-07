import argparse
import csv
import os
import subprocess
import logging
import datetime
import sys

VERSION = "v0.5.0"


def log():
    # Set up logging
    date_time = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    cwd = os.getcwd()
    log = os.path.join(cwd, f"ebi-fastq-{date_time}.log")
    logging.basicConfig(
        format="%(levelname)s:%(asctime)s:%(message)s",
        level=logging.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(log), logging.StreamHandler()],
    )


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outdir",
        "-o",
        type=str,
        default=".",
        help="Output directory (default: current directory)",
    )
    parser.add_argument(
        "--csv",
        "-c",
        type=str,
        required=True,
        help="CSV file with SRA accession and sample name on different rows",
    )
    parser.add_argument("--paired", "-p", action="store_true", help="Paired-end reads")
    parser.add_argument(
        "--version", "-v", action="version", version=f"%(prog)s {VERSION}"
    )
    return parser.parse_args()


def download_file(url, file_name):
    cmd = ["curl", "-L", url, "-o", file_name]
    logging.info(f" Downloading {url} to {file_name}")
    logging.info(" ".join(cmd))
    # Run and if failed, try again (at most 3 times)
    # If failed after 3 times, log error and continue
    for i in range(3):
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to download {url} to {file_name}")
            logging.error(e)
            if i == 2:
                logging.error(
                    f"Failed to download {url} to {file_name} after 3 attempts"
                )
            else:
                logging.info(f"Retrying download of {url} to {file_name}")
        else:
            break


def get_fastq(srr, sample_name, paired):
    EBI_BASE_URL = "ftp://ftp.sra.ebi.ac.uk/vol1/fastq"

    # Get last two characters of SRR
    srr_suffix = f"0{srr[-2:]}"

    # Get first six characters of SRR
    ssr_prefix = srr[:6]

    # Construct URLs for read 1 and read 2
    base_url = f"{EBI_BASE_URL}/{ssr_prefix}/{srr_suffix}/{srr}/{srr}"
    if paired:
        read_suffix = ["1", "2"]
        for suffix in read_suffix:
            url = f"{base_url}_{suffix}.fastq.gz"
            outfile = os.path.join(OUTDIR, f"{sample_name}_R{suffix}_001.fastq.gz")
            download_file(url, outfile)
    else:
        url = f"{base_url}.fastq.gz"
        outfile = os.path.join(OUTDIR, f"{sample_name}.fastq.gz")
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
            get_fastq(srr, sample_name, args.paired)


if __name__ == "__main__":
    args = args()
    log()
    command_line_args = " ".join(sys.argv)
    logging.info(command_line_args)
    main(args)
