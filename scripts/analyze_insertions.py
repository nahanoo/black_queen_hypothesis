from Bio import SeqIO
import pandas as pd
from glob import glob
from os.path import join
from samples import Samples

s = Samples()


def get_contigs(fasta):
    """Parses fastas and returns dictionary with contig name as 
    key and sequence as value."""
    contigs = [contig for contig in SeqIO.parse(fasta, "fasta")]
    c = {contig.id: contig.seq for contig in contigs}
    return c


def parse_insertions():
    """Parses all identified Pacbio sequences and stors them with
    inserted sequence in a dataframe."""
    dfs = []
    for strain, samples in s.strains.items():
        for sample in samples:
            if sample["platform"] == "pacbio":
                df = pd.read_csv(
                    join(sample["dir_name"], "mutant_to_parent.noalignments.tsv"),
                    sep="\t",
                    usecols=["chromosome", "position", "length"],
                ).drop_duplicates()
                df.insert(0, "sample_name", sample["name"])
                df.insert(4, "sequence", None)
                df.insert(5,'fasta',None)
                fasta = join(sample["dir_name"], "assembly.fasta")
                contigs = get_contigs(fasta)
                for i, row in df.iterrows():
                    df.at[i, "sequence"] = str(
                        contigs[row.chromosome][
                            row.position - 1 : row.position - 1 + row.length
                        ]
                    )
                    df.at[i,'fasta'] = contigs
                dfs.append(df)
    out = pd.concat(dfs)
    out.index = range(len(out))
    return out


def filter_insertions(insertions,min_distance):
    """To rule out assembly bias we look at insertion sequence
    which are not located at the end or the start of the assembly."""
    to_pop = []
    for i, row in insertions.iterrows():
        contig_length = len(row['fasta'][row['chromosome']])
        if row['length'] == contig_length:
            pass
        elif row['position'] < min_distance:
            to_pop.append(i)
        elif contig_length - row['position'] < min_distance:
            to_pop.append(i)
        else:
            pass
    print('To drop')
    for element in to_pop:
        row = insertions.loc[element]
        print(row['sample_name'],row['chromosome'],row['position'],row['length'],len(row['fasta'][row['chromosome']]))
        insertions = insertions.drop(element)
    print('To keep')
    for i,row in insertions.iterrows():
        print(row['sample_name'],row['chromosome'],row['position'],row['length'],len(row['fasta'][row['chromosome']]))
    #return insertions

def get_sequences():
    work = "/users/eulrich/work/genome_size/data"
    df = pd.read_csv("sequences_of_interest.csv")
    df.insert(5, "sequence", None)
    for i, row in df.iterrows():
        c = row.chromosome
        p = row.position
        l = row.length
        s = row.sample_name
        fasta = join(work, s, "assembly.fasta")
        contigs = get_contigs(fasta)
        df.at[i, "sequence"] = str(contigs[c][p : p + l])
    return df