from samples import Samples
from plotting import Plotting
from os.path import join
from os.path import exists
import pandas as pd
from Bio import SeqIO

s = Samples()
p = Plotting()


def plot_deletions():
    """Plotting the sum of deleted bases in pacbio samples."""
    for strain in s.strains:
        treatments = s.treatments[strain]
        out = pd.DataFrame(columns=treatments,index=[sample['name'] \
            for sample in s.strains[strain] if sample['platform']== 'pacbio'])
        for sample in s.strains[strain]:
            if sample['platform'] == 'pacbio':
                #Summing deleted bases from deletion_detection analysis
                deleted_bases = 0
                no_coverage = join(sample['dir_name'],'no_alignment_regions.tsv')
                if exists(no_coverage):
                    deleted_bases += sum(pd.read_csv(no_coverage,sep='\t',\
                        usecols=['chromosome','position','length']).drop_duplicates()['length'])
                in_read = join(sample['dir_name'],'in_read_deletions.tsv')
                if exists(in_read):
                    deleted_bases += sum(pd.read_csv(in_read,sep='\t',\
                        usecols=['chromosome','position','length']).drop_duplicates()['length'])
                out.at[sample['name'],sample['treatment']] = deleted_bases
        fig = p.subplot_treatments(strain,out)
        title = 'delete bases in '+strain
        fig.update_layout(
            xaxis_title='sample',
            yaxis_title='deleted bp',
            title=title)
        fig.update_traces(showlegend=False)
        fig.write_image(join('..','plots','deleted_bases',title.replace(' ','_')+'.png'))

def plot_genome_length():
    """Plotting assembly length of pacbio data and resulting n contigs of assmblies."""
    for strain in s.strains:
        #Get all treatments of a strain
        treatments = s.treatments[strain]
        #Create subplot titles
        length = pd.DataFrame(columns=treatments,index=[sample['name'] \
            for sample in s.strains[strain] if sample['platform']== 'pacbio'])
        n_contigs = pd.DataFrame(columns=treatments,index=[sample['name'] \
            for sample in s.strains[strain] if sample['platform']== 'pacbio'])
        for counter,treatment in enumerate(treatments):
            #Get all sample names of a treatment
            for sample in s.strains[strain]:
                #Getting genome lenght and n contigs
                if sample['platform'] == 'pacbio':
                    contigs = [contig for contig in SeqIO.parse(join(sample['dir_name'],'assembly.fasta'),'fasta')]
                    n_contigs.at[sample['name'],sample['treatment']] = len(contigs)
                    length.at[sample['name'],sample['treatment']] = sum([len(contig) for contig in contigs])
        fig = p.subplot_treatments(strain,length)
        reference_length = sum([len(contig) for contig in SeqIO.parse(s.references[strain],'fasta')])
        fig.add_hline(y=reference_length,annotation_text='reference',line_dash="dash")
        title = 'assembly length in '+strain
        fig.update_layout(
            xaxis_title='sample',
            yaxis_title='assembly length in bp',
            title=title)
        fig.update_traces(showlegend=False)
        fig.write_image(join('..','plots','genome_length',title.replace(' ','_')+'.png'))
        fig = p.subplot_treatments(strain,n_contigs)
        title = 'n contigs in '+strain
        fig.update_layout(
            xaxis_title='sample',
            yaxis_title='n contigs',
            title=title)
        fig.update_traces(showlegend=False)
        fig.write_image(join('..','plots','contigs',title.replace(' ','_')+'.png'))