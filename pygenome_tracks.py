"""
From a set of bigWig files, plot the regions of the genes in a list with pyGenomeTracks.

A base .ini file has to be prepared first

1. For each gene, extract the region of the gene.
2. Find the maximum in that region in all bigwig files.
3. Change .ini file for each gene with found maximum.
4. Run pygenometracks. 

Run from Conda environment:
mamba create -n tracks pybigwig=0.3.22 pygenometracks=3.9
mamba activate tracks
"""
import datetime
import os
import subprocess
import shutil
import argparse
import logging
import math
import pyBigWig

# Create command line parser
parser = argparse.ArgumentParser(description="Plot gene regions with pyGenomeTracks from a list of genes")
parser.add_argument("--ini", "-i", 
                    type=str,
                    required=True,
                    help="pyGenomeTracks base .ini file")
parser.add_argument("--genes", "-g",
                    type=str,
                    required=True,
                    help="List of genes to plot (each gene on a new line)")
parser.add_argument("--gtf",
                    type=str,
                    help="GTF file with gene annotations")
parser.add_argument("--upstream", "-a",
                    type=int,
                    default=500,
                    help="Upstream region to add to gene region to plot")
parser.add_argument("--downstream", "-d",
                    type=int,
                    default=500,
                    help="Downstream region to add to gene region to plot")
parser.add_argument("--outdir", "-o",
                    type=str,
                    default=".",
                    help="Output directory")
parser.add_argument("--format",
                    type=str,
                    default="pdf",
                    help="Output format")
parser.add_argument("--dpi",
                    type=int,
                    default=300,
                    help="DPI of the output figure")

# Parse arguments
args = parser.parse_args()

# Create output dir
os.makedirs(args.outdir, exist_ok=True)

# Setup log file
log_file = f"pyGenomeTracks_{os.path.basename(args.genes).split('.')[0]}.log"
logging.basicConfig(format='%(levelname)s:%(message)s', 
                    level=logging.DEBUG,
                    handlers=[logging.FileHandler(log_file),
                              logging.StreamHandler()])

# Log start time
logging.info(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# Open bigWig files from ini file
logging.info("Loading bigWig files...")
bigwigs = []
with open(args.ini, "r") as f:
    for line in f:
        if "file = " in line and ".bw" in line.lower() or ".bigwig" in line.lower():
            file = line.split("=")[1].strip()
            bw = pyBigWig.open(file)
            bigwigs.append(bw)
            
# Open gene list
genes = []
with open(args.genes, "r") as f:
    for line in f:
        genes.append(line.strip())

# Create tracks for each gene
for gene in genes:
    logging.info(f"Extracting coordinates for {gene}...")
    # Open GTF file and find gene regions
    cmd = f"""awk '{{if ($3 == "gene") {{print $0}}}}' {args.gtf} | grep -w 'gene_name "{gene}";' |awk '{{print $1, $4, $5, $7}}'"""
    logging.debug(f"Running command: {cmd}")
    gene_info = subprocess.check_output(cmd, shell=True).decode("utf-8").strip().split("\n")
    assert len(gene_info) == 1, f"Gene {gene} not found in GTF file or too many lines found"
    chr, start, end, strand = gene_info[0].split()
    
    if strand == "+":
        start = int(start) - args.upstream
        end = int(end) + args.downstream
    elif strand == "-":
        start = int(start) - args.downstream
        end = int(end) + args.upstream

    # Find maximum in the gene region of all bigwig files
    logging.info(f"Finding maximum plotting value for {gene}...")
    max_values = []
    for bw in bigwigs:
        #https://www.biostars.org/p/244898/
        max_values.append(bw.stats(chr, start, end, type="max"))
    max_value = math.ceil(max(max_values)[0] * 1.05)

    # Copy ini file with gene specific values
    logging.info(f"Creating ini file for {gene}...")
    new_ini = os.path.join(os.path.dirname(args.ini), gene + ".ini")
    shutil.copy(args.ini, new_ini)
    sed = f"sed -i 's/#max_value = auto/max_value= {max_value}/g' {new_ini}"
    logging.debug(f"Running command: {sed}")
    subprocess.run(sed, shell=True)
    
    # Run pyGenomeTracks
    logging.info(f"Running pyGenomeTracks for {gene}...")
    output = os.path.join(args.outdir, gene + "." + args.format)
    tracks = f"pyGenomeTracks --tracks {new_ini} --region {chr}:{start}-{end} --outFileName {output} --dpi {args.dpi}"
    logging.debug(f"Running command: {tracks}")
    try:
        stdout = subprocess.check_output(tracks, 
                                        shell=True,
                                        stderr=subprocess.STDOUT).decode("utf-8")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running pyGenomeTracks for {gene}")
        logging.error(e.output.decode("utf-8"))
        continue
    
logging.info("All done!")
# Log end time
logging.info(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))