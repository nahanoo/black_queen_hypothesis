from samples import Samples
from plotting import Plotting
from analyze_marcs_deletions import get_gc_content
import pandas as pd
from os.path import join
from os.path import exists
import math
from Bio import SeqIO
import re
import plotly.graph_objects as go
from plotly.subplots import make_subplots


"""
################################################################################
Author: https://github.com/nahanoo
This script analyzes all outputs generated from illumina sample processing.
If you are interested in the sample processing you can check out the Snakemake
workflow: https://github.com/nahanoo/black_queen_hypothesis/blob/main/scripts/workflows/illumina/Snakefile.
All plots call this small plotting class in plotting.py
################################################################################
"""

s = Samples()
p = Plotting()


def plot_effects():
    """This plots the summed effects grouped per treatment per species
    """
    snps = {strain: None for strain in s.strains}
    for strain, samples in s.strains.items():
        effects = []
        for sample in samples:
            if (sample['platform'] == 'illumina') & (sample['timepoint'] == 'T44'):
                f = join(sample['dir_name'], 'snippy', 'snps.tab')
                df = pd.read_csv(f, sep='\t').drop_duplicates()
                df = df[df['EFFECT'].notna()]
                for effect in df['EFFECT']:
                    effects.append(effect.split(' ')[0])
        effects = list(set(effects))
        columns = s.treatments[strain]
        snp = pd.DataFrame(columns=columns, index=effects)
        for sample in samples:
            if (sample['platform'] == 'illumina') & (sample['timepoint'] == 'T44'):
                f = join(sample['dir_name'], 'snippy', 'snps.tab')
                df = pd.read_csv(f, sep='\t').drop_duplicates()
                df = df[df['EFFECT'].notna()]
                effects = []
                for effect in df['EFFECT']:
                    effects.append(effect.split(' ')[0])

                for effect in set(effects):
                    mask = []
                    for e in df['EFFECT']:
                        if re.search(effect, e, flags=re.IGNORECASE):
                            mask.append(True)
                        else:
                            mask.append(False)
                    if pd.isna(snp.at[effect, sample['treatment']]):
                        snp.at[effect, sample['treatment']] = len(df[mask])
                    else:
                        snp.at[effect, sample['treatment']] += len(df[mask])
        snps[strain] = snp
    p.plot_effects(snps)

def plot_all_snps():
    """This function plots the sum of SNPs for a timepoint."""
    snps = {strain: None for strain in s.strains}
    for strain in s.strains:
        treatments = s.treatments[strain]
        snp = pd.DataFrame(columns=treatments, index=[sample['name']
                                                      for sample in s.strains[strain] if sample['platform'] == 'illumina'])
        for sample in s.strains[strain]:
            if (sample['platform'] == 'illumina') & (sample['timepoint'] == 'T44'):
                f = join(sample['dir_name'], 'snippy', 'snps.tab')
                df = pd.read_csv(f, sep='\t').drop_duplicates()
                snp.at[sample['name'], sample['treatment']] = len(df)
        snps[strain] = snp
    fig = p.subplot_violin(snps)

def get_differences_snps(df,strain,treatments,platform):
    """This is a simple function which lets you identify mutations uniquely found
    in one treatment.
    """
    p_mono = dict()
    p_co = dict()
    for sample in s.strains[strain]:
        if (sample['treatment'] in treatments) & (sample['platform'] == platform): 
            f = join(sample['dir_name'],df)
            if platform == 'illumina':
                column = 'PRODUCT'
            else:
                column = 'product'
            products = set(pd.read_csv(f,sep='\t')[column])
            if sample['treatment'] == treatments[0]:
                for product in products:
                    if product in p_mono.keys():
                        p_mono[product] += 1
                    else:
                        p_mono[product] = 1
            if sample['treatment'] == treatments[1]:
                for product in products:
                    if product in p_co.keys():
                        p_co[product] += 1
                    else:
                        p_co[product] = 1

    co_only = set(p_co.keys()) - set(p_mono.keys())
    print(co_only)
    for product in co_only:
        if p_co[product] > 1:
            print(product,p_co[product])

def write_gc_content():
    """Small function to get gc content of references."""
    def get_gc_content(sequence):
        """This function returns gc content for string sequence"""
        return 100.0*len([base for base in sequence if base in "GC"])/len(sequence)
    """This is a little helper function to get the GC content of the wild-type genomes"""
    # Setting up df and iterating over all strains
    df = pd.DataFrame(columns=['gc content'])
    for strain in s.strains:
        sequence = str()
        reference = s.references[strain]
        contigs = [contig for contig in SeqIO.parse(reference, 'fasta')]
        for contig in contigs:
            # Adding sequence as string
            sequence += contig.seq
        # Getting gc content of sequence
        gc_content = get_gc_content(sequence)
        # Writing to df and to file
        df.at[strain, 'gc content'] = gc_content
    df.index.name = 'strain'
    fname = join('..', 'tables', 'gc_content', 'gc_content.csv')
    df.to_csv(fname)
