import argparse
import glob
import logging
import os
import re
import shutil
import sys
from datetime import datetime

VERSION = "v1.0.0"

# Matches e.g. SAMPLE_EKDL260008407-1A_23NKVHLT4_L5_1.fq.gz -> lane "L5", read "1"
LANE_READ_RE = re.compile(r"_(L\d+)_([12])\.fq\.gz$")


def log():
    date_time = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    log_file = os.path.join(os.getcwd(), f"merge-lanes-{date_time}.log")
    logging.basicConfig(
        format="%(levelname)s:%(asctime)s:%(message)s",
        level=logging.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )


def args():
    parser = argparse.ArgumentParser(
        description=(
            "Merge multi-lane *.fq.gz files (one subdirectory per sample) into a "
            "single *.fastq.gz per read, named after the sample subdirectory."
        )
    )
    parser.add_argument(
        "--indir",
        "-i",
        type=str,
        default=".",
        help="Root directory containing one subdirectory per sample (default: current directory)",
    )
    parser.add_argument(
        "--outdir",
        "-o",
        type=str,
        default=".",
        help="Output directory for merged files (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be merged without writing any files",
    )
    parser.add_argument(
        "--version", "-v", action="version", version=f"%(prog)s {VERSION}"
    )
    return parser.parse_args()


def find_sample_files(indir):
    """Return {sample: {read: [file paths sorted by lane]}} for */*.fq.gz under indir."""
    samples = {}
    for path in glob.glob(os.path.join(indir, "*", "*.fq.gz")):
        match = LANE_READ_RE.search(os.path.basename(path))
        if not match:
            logging.warning(f"Skipping file with unexpected name: {path}")
            continue
        lane, read = match.group(1), match.group(2)
        sample = os.path.basename(os.path.dirname(path))
        samples.setdefault(sample, {}).setdefault(read, []).append((lane, path))

    for sample, reads in samples.items():
        for read in reads:
            reads[read].sort()
            reads[read] = [path for _, path in reads[read]]
    return samples


def merge_files(files, outfile, dry_run=False):
    logging.info(f"Merging {len(files)} file(s) into {outfile}")
    for f in files:
        logging.info(f"  {f}")
    if dry_run:
        return
    # Concatenating gzip members is valid gzip and is what every standard
    # reader (zcat, gzip -dc, python gzip, aligners, etc.) expects, so we
    # append the raw compressed bytes rather than decompress/recompress.
    with open(outfile, "wb") as out:
        for f in files:
            with open(f, "rb") as fh:
                shutil.copyfileobj(fh, out, length=1024 * 1024)


def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    samples = find_sample_files(args.indir)

    if not samples:
        logging.error(f"No fq.gz files found under {args.indir}")
        sys.exit(1)

    for sample, reads in sorted(samples.items()):
        multi_read = len(reads) > 1
        for read, files in sorted(reads.items()):
            suffix = f"_R{read}" if multi_read else ""
            outfile = os.path.join(args.outdir, f"{sample}{suffix}.fastq.gz")
            merge_files(files, outfile, args.dry_run)


if __name__ == "__main__":
    args = args()
    log()
    logging.info(" ".join(sys.argv))
    main(args)
