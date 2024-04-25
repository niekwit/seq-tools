#!/bin/bash

## Run this script from directory with config, reads and workflow folders present ##

# Check if mamba is installed
CHECK=$(which mamba)
if [ "$CHECK" == "" ]; then
    echo "mamba not found..."
    echo "Please install mamba using 'conda install -c conda-forge mamba'"
    exit 1
fi

# Check if snakemake8 mamba env is available
CHECK=$(mamba env list | grep snakemake8 | awk '{print $1}')
if [ "$CHECK" != "snakemake8" ]; then
    echo "snakemake8 mamba env not found..."
    echo "Creating snakemake8 mamba env..."
    mamba create -c conda-forge -c bioconda -n snakemake8 snakemake
else
    echo "Activating snakemake8 mamba env..."
    mamba activate snakemake8
fi

# Create rule graph
mkdir -p images
snakemake --forceall --rulegraph | grep -v '\-> 0\|0\[label = \"all\"' | dot -Tpng > images/rule_graph.png

# Dry run
echo "Running dry run..."
snakemake -np > dry_run.log
if $? != 0; then
    echo "Dry run failed..."
    cat dry_run.log
    exit 1
else 
    echo "Dry run successful..."
    rm dry_run.log
fi

# Run workflow
PROFILE="/home/niek/.config/snakemake/standard/"
snakemake --profile $PROFILE

# Create report
snakemake --report report.html

