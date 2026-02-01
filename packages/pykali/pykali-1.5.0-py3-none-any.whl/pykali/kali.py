#!/usr/bin/env python3
"""
KALI: A tool for performing genomic distance calculations based on k-mer frequencies and restriction enzyme motif simulations.

This script allows users to:
- Input one or more genome files.
- Specify a k-mer size and the number of bins for simulating gel electrophoresis.
- Calculate pairwise distances between genomes using various distance metrics.
- Output the distance matrix to a CSV file.

The script uses the following components:
- `Genome`: Represents individual genomes.
- `GenomeSet`: A collection of Genome objects that can be processed collectively.
- `Bands`: Handles fragment patterns and calculates pairwise distances based on motifs.
- Supports distance metrics: Cosine, Euclidean, and Jaccard.

Usage:
    python3 kali.py -g genome1.fasta genome2.fasta -k 6 -b 50 -d cosine -o output.csv

Arguments:
    -v, --verbosity   : Increase output verbosity (optional).
    -g, --genome      : One or more genome files to be processed.
    -k, --kmer        : Size of the k-mers to use for motif simulation (default: 10).
    -b, --bin         : Number of bins for fragment size distribution during electrophoresis (default: 30).
    -o, --output      : Output CSV file where the distance matrix will be saved (default: 'kali_out.csv').
    -d, --distance    : The distance metric to use ('cosine', 'euclidean', 'jaccard') (default: 'cosine').
    -p, --plot        : Plot the electrophoresis results as a heatmap (default: kali_out.png).

Author:
    Natapol Pornputtapong (natapol.p@chula.ac.th)

Version:
    1.5.0

Date:
    Feb 1, 2026
"""

import importlib
import sys
import argparse
import itertools

import numpy as np
import pandas as pd
from scipy.spatial import distance
from tqdm import tqdm

from pykali.modules.genome import Genome
from pykali.modules.genomeset import GenomeSet
from pykali.modules.bands import Bands

__author__ = "Natapol Pornputtapong (natapol.p@chula.ac.th)"
__version__ = "1.5.0"
__date__ = "Feb 1, 2026"


def main():
    """
    Main function to execute the KALI tool for genomic distance calculation.

    This function parses command-line arguments, loads genome data, simulates restriction enzyme activity
    using k-mers, and calculates pairwise distances between genomes. The results are saved as a CSV file.

    Command-line arguments:
        -g, --genome      : One or more genome files (FASTA format) to be processed.
        -k, --kmer        : Size of the k-mer to use for motif generation (default: 10).
        -b, --bin         : Number of bins for simulating gel electrophoresis (default: 30).
        -r, --reduce      : Reduction method 'mean' or 'median' (default: 'mean')
        -o, --output      : Path to the output CSV file (default: "kali_out.csv").
        -d, --distance    : Distance metric to use ('cosine', 'euclidean', or 'jaccard') (default: 'cosine').
        -v, --verbosity   : Increase the verbosity of output (optional).
        -p, --plot        : Plot the electrophoresis results as a heatmap (default: kali_out.png).

    Workflow:
        1. Parse command-line arguments.
        2. Load genomes and create a `GenomeSet`.
        3. For each k-mer (based on the specified k-mer size), simulate electrophoresis and calculate pairwise distances.
        4. Average the distances across all k-mers.
        5. Output the final distance matrix as a CSV file.

    Example:
        kali -g genome1.fasta genome2.fasta -k 6 -b 50 -r mean -d cosine -o output.csv
    """
    parser = argparse.ArgumentParser(description="calculate X to the power of Y")
    parser.add_argument('-v', '--verbosity', action='count', default=0,
                        help='increase output verbosity')
    parser.add_argument('-g', '--genome', nargs='+')
    parser.add_argument('-k', '--kmer', type=int, default=10)
    parser.add_argument('-b', '--bin', type=int, default=30)
    parser.add_argument('-r', '--reduce', type=str, default="mean", choices=[
                            'mean', 
                            'median'])
    parser.add_argument('-o', '--output', type=str, default="kali_out.csv")
    parser.add_argument('-p', '--plot', type=str, default="kali_out.png") 
    parser.add_argument('-d', '--distance', type=str, 
                        default='cosine', 
                        choices=[
                            'cosine', 
                            'euclidean',
                            'jaccard'])
    args = parser.parse_args()

    genomeset = GenomeSet()
    array = []

    for name in args.genome:
        genome = Genome(name)
        genomeset.add(genome)
        

    bases=['A','T','G','C']
    for motif in [''.join(p) for p in itertools.product(bases, repeat=args.kmer)]:
        bands = genomeset.electrophorese(motif, args.bin)
        array.append(bands.calculate_distance(metric=args.distance))

    if args.reduce == 'mean':
        distances = np.array(array).mean(axis=0)
    elif args.reduce == 'median':
        distances = np.array(array).median(axis=0)

    df = pd.DataFrame(
        distance.squareform(
            distances
        ), 
        columns=genomeset.names(), index=genomeset.names()
    )

    df.to_csv(args.output)

    bands.plot(args.plot)

if __name__ == "__main__":
    main()