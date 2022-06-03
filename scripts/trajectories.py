import vcfpy
from samples import Samples
from os.path import join, exists
import pandas as pd
import plotly.express as px
from Bio import SeqIO

s = Samples()


class SNPs:
    def __init__(self, filter=20):
        self.snps = {strain: [] for strain in s.strains}
        for strain, samples in s.strains.items():
            for sample in samples:
                if sample['platform'] == 'illumina':
                    snps = []
                    f = join(sample['dir_name'], 'var.vcf')
                    if exists(f):
                        reader = vcfpy.Reader.from_path(f)
                        for record in reader:
                            snp = {}
                            snp['chrom'] = record.CHROM
                            snp['pos'] = record.POS
                            snp['qual'] = record.QUAL
                            snp['depth'] = record.INFO['DP']
                            snp['freq_sum'] = sum(
                                record.INFO['AO'])/record.INFO['DP']
                            snp['alt_depth_sum'] = sum(record.INFO['AO'])
                            snp['alt_depth'] = record.INFO['AO']
                            snp['freq'] = [freq / record.INFO['DP']
                                           for freq in record.INFO['AO']]
                            snp['alt'] = record.ALT
                            if filter is None:
                                snps.append(snp)
                            else:
                                if snp['qual'] >= filter:
                                    snps.append(snp)
                    else:
                        if strain == s.abbreviations['at']:
                            print(f)
                    sample['snps'] = snps
                    self.snps[strain].append(sample)

    def join_genbank(self):
        genbanks = {}
        for strain in s.strains:
            f = s.references[strain].replace('.fasta', '_stripped.gbk')
            contigs = [contig for contig in SeqIO.parse(
                f, 'genbank')]
            genbank = {contig.id: {} for contig in contigs}
            for contig in contigs:
                for feature in contig.features:
                    # Some features don't have all desired keys
                    try:
                        start = feature.location.start
                        end = feature.location.end
                        product = feature.qualifiers['product']
                        genbank[contig.id][(start, end)] = product[0]
                    except KeyError:
                        pass
            genbanks[strain] = genbank
        for strain, samples in self.snps.items():
            for sample in samples:
                for snp in sample['snps']:
                    snp['product'] = 'intergenic'
                    for (start, end), product in genbanks[strain][snp['chrom']].items():
                        if (snp['pos'] >= start) & (snp['pos'] <= end):
                            snp['product'] = product

    def get_data_frame(self,strain,filter_genes=False):
        self.df = pd.DataFrame(
            columns=['micro_treat', 'timepoint', 'freq', 'qual', 'color', 'product'])
        i = 0
        for sample in self.snps[strain]:
            for snp in sample['snps']:
                key = '.'.join([str(item) for item in [snp['chrom'],
                                                       snp['pos'], sample['treatment'], sample['cosm']]])
                self.df.at[i, 'freq'] = snp['freq_sum']
                self.df.at[i, 'micro_treat'] = str(
                    sample['treatment']) + '.' + str(sample['cosm'])
                self.df.at[i, 'timepoint'] = sample['timepoint']
                self.df.at[i, 'qual'] = snp['qual']
                self.df.at[i, 'color'] = key
                self.df.at[i, 'product'] = snp['product']
                i += 1

        if filter_genes:
            self.df = self.df.drop_duplicates(['product','timepoint','micro_treat'])

    def plot_phred_score(self,out):
        fig = px.histogram(self.df, x='qual', facet_col='micro_treat', log_y=True,
                           facet_col_wrap=3, title='SNP phred scores',
                           category_orders={'micro_treat': list(sorted(self.df['micro_treat']))})
        fig.write_html(out + '_phred_score.html')

    def plot_trajectories(self,out):
        mask = []
        for i in self.df['color']:
            if 'AGTU001.0001.c01.2351' in i:
                mask.append(True)
            else:
                mask.append(False)
        #df = df[mask]
        fig = px.line(self.df, x='timepoint', y='freq', color='color',
                      facet_col='micro_treat', facet_col_wrap=3,
                      hover_data=['product'],
                      category_orders={'micro_treat': list(sorted(self.df['micro_treat']))})
        fig.update_xaxes(categoryorder='array', categoryarray=[
                         'T11', 'T22', 'T33', 'T44'])
        fig.update_traces(showlegend=False)
        fig.write_html(out + '_trajectories.html')

    def plot_frequencies(self,out):
        fig = px.histogram(self.df, x='freq', facet_col='micro_treat', log_y=True,
                           facet_col_wrap=3, title='SNP frequencies',
                           category_orders={'micro_treat': list(sorted(self.df['micro_treat']))})
        fig.write_html(out + '_frequencies.html')

snps = SNPs(filter=20)
snps.join_genbank()
for strain in s.strains:
    out = s.abbreviations[strain]
    snps.get_data_frame(strain)
    snps.plot_phred_score(out)
    snps.plot_frequencies(out)
    snps.plot_trajectories(out)
    snps.get_data_frame(strain,filter_genes=True)
    out = 'unique_genes_' + out
    snps.plot_frequencies(out)
    snps.plot_trajectories(out)
"""freqs = snps.plot_trajectories()
cosms = set(freqs['micro_treat'])
for cosm in cosms:
    tmp = freqs[freqs['micro_treat'] == cosm]
    print(cosm,len(tmp))"""