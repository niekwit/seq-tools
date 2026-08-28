#!/bin/bash

# Down-sample every paired-end fastq.gz in a folder to N reads per mate.
#
# Uses `seqtk sample` with a fixed seed so R1 and R2 stay in sync.
# Requires seqtk:  conda install -c bioconda seqtk
#
# Usage:
#   ./subsample.sh [-n READS] [-s SEED] [-o OUTDIR] [INPUT_DIR]
#
# Defaults: READS=5000000, SEED=100, OUTDIR=subset, INPUT_DIR=.
#
# Recognised mate naming (case-sensitive on the R1/R2 or 1/2 token):
#   *_R1_*.fastq.gz / *_R2_*.fastq.gz
#   *_R1.fastq.gz   / *_R2.fastq.gz
#   *_1.fastq.gz    / *_2.fastq.gz
# Also matches .fq.gz.

set -euo pipefail

READS=5000000
SEED=100
OUTDIR=subset

while getopts ":n:s:o:h" opt; do
    case "$opt" in
        n) READS=$OPTARG ;;
        s) SEED=$OPTARG ;;
        o) OUTDIR=$OPTARG ;;
        h) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        \?) echo "Unknown option: -$OPTARG" >&2; exit 1 ;;
        :) echo "Option -$OPTARG requires an argument" >&2; exit 1 ;;
    esac
done
shift $((OPTIND - 1))

INDIR=${1:-.}

if ! command -v seqtk >/dev/null 2>&1; then
    echo "Error: seqtk not found. Install it with:  conda install -c bioconda seqtk" >&2
    exit 1
fi

if [ ! -d "$INDIR" ]; then
    echo "Error: input directory '$INDIR' does not exist" >&2
    exit 1
fi

mkdir -p "$OUTDIR"

shopt -s nullglob

# Find R1 files via the three supported patterns, then derive the R2 name.
r1_files=()
for f in "$INDIR"/*_R1_*.fastq.gz "$INDIR"/*_R1_*.fq.gz \
         "$INDIR"/*_R1.fastq.gz   "$INDIR"/*_R1.fq.gz \
         "$INDIR"/*_1.fastq.gz    "$INDIR"/*_1.fq.gz; do
    r1_files+=("$f")
done

if [ ${#r1_files[@]} -eq 0 ]; then
    echo "No R1 fastq.gz files found in '$INDIR'." >&2
    exit 1
fi

n_pairs=0
for r1 in "${r1_files[@]}"; do
    case "$r1" in
        *_R1_*) r2=${r1/_R1_/_R2_} ;;
        *_R1.fastq.gz) r2=${r1/_R1.fastq.gz/_R2.fastq.gz} ;;
        *_R1.fq.gz)    r2=${r1/_R1.fq.gz/_R2.fq.gz} ;;
        *_1.fastq.gz)  r2=${r1/_1.fastq.gz/_2.fastq.gz} ;;
        *_1.fq.gz)     r2=${r1/_1.fq.gz/_2.fq.gz} ;;
        *) echo "Skipping (cannot derive mate): $r1" >&2; continue ;;
    esac

    if [ ! -e "$r2" ]; then
        echo "Skipping (mate not found): $r1  ->  expected $r2" >&2
        continue
    fi

    out1=$OUTDIR/$(basename "$r1")
    out2=$OUTDIR/$(basename "$r2")

    echo "Sub-sampling $(basename "$r1") + $(basename "$r2") to $READS reads..."
    seqtk sample -s"$SEED" "$r1" "$READS" | gzip > "$out1"
    seqtk sample -s"$SEED" "$r2" "$READS" | gzip > "$out2"
    n_pairs=$((n_pairs + 1))
done

echo "Done! $n_pairs pair(s) written to '$OUTDIR/'."
echo "Note: files with fewer than $READS reads are copied in full (all reads kept)."
