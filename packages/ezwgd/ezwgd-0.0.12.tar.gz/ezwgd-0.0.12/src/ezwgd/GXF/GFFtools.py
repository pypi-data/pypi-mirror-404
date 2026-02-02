#  Copyright (C) 2025-2026, HYLi360.
#  Free software distributed under the terms of the GNU GPL-3.0 license,
#  and comes with ABSOLUTELY NO WARRANTY.
#  See at <https://www.gnu.org/licenses/gpl-3.0.en.html>
"""
A series of GFF-handle tools.

GFF2 is not currently supported, due to inherent limitations of the GFF2 format
itself.

("Converting a file from GFF2 to GFF3 format is problematic for several reasons.
 However, there are several GFF2 to GFF3 converters available on the web, but e-
 ach makes specific assumptions about  the GFF2 data that limit its applicabili-
 ty. GMOD does not endorse (or disparage) any particular converter. If you have
 GFF2 data from an external source, and they don’t also provide it in GFF3 form-
 at, then you may be stuck with GFF2."
 From <https://gmod.org/wiki/GFF2#converting-gff2-to-gff3>)

`parse`:
`examine`:
`give_fecture`:
`build_bed`:
"""

import pandas as pd
import re
import mmap
from collections import defaultdict
from rich.table import Table
from ezwgd import console

class GFF3:
    pass

def build_gff3_indices(gff3_file_path: str):
    # line_re: Only parse which column 3 has gene/mRNA/transcript/CDS feature.
    # id_re: Extract the ID=(...) in attribule column.
    # parent_re: Extract the Parent=(..) in attribule column.
    line_re = re.compile(
        rb'^(?P<chr>[^\t#][^\t]*)\t[^\t]*\t(?P<type>gene|mRNA|transcript'
        rb'|CDS)\t(?P<start>\d+)\t(?P<end>\d+)\t[^\t]*\t(?P<strand>[+-])\t(?P<p'
        rb'hase>[^\t]*)\t(?P<attrs>[^\n]*)$',
        re.M
    )
    id_re = re.compile(rb'(?:^|;)ID=([^;]+)')
    parent_re = re.compile(rb'Parent=([^;]+)')

    # Prepare result collector.
    _df = []
    tx_gene = {}
    gene_txs = defaultdict(list)
    tx_cds = defaultdict(list)

    # Load gff3 file as memory-mapped file.
    with open(gff3_file_path, 'rb') as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        for m in line_re.finditer(mm):
            # Unpack line
            chro, feature_type, start, end, strand, phase, attrs = m.groups()

            # Check id and parent (may return None in gene feature line)
            id_m = id_re.search(attrs)
            parent_m = parent_re.search(attrs)

            if feature_type == b'gene' and id_m:
                # 1    ensembl    gene    1    201    .    +    .    ID=gene;...
                gene_id = id_m.group(1).decode('ascii', 'ignore')
                # chr, gene_id, start, end, strand
                _df.append({
                    'chr': str(chro.decode('ascii', 'ignore')),
                    'gene_id': gene_id,
                    'start': int(start),
                    'end': int(end),
                    'strand': strand.decode('ascii'),
                })

            elif feature_type in (b'mRNA', b'transcript') and id_m and parent_m:
                # 1 ensembl mRNA 1 201 . + . ID=transcript;Parent=gene;...
                tx_id = id_m.group(1).decode('ascii', 'ignore')
                gene_id = parent_m.group(1).decode('ascii', 'ignore')
                tx_gene[tx_id] = gene_id
                gene_txs[gene_id].append(tx_id)

            elif feature_type == b'CDS' and parent_m:
                # 1 ensembl CDS 1 201 . + 0 ID=cds;Parent=transcript;...
                tx_id = parent_m.group(1).decode('ascii', 'ignore')

                tx_cds[tx_id].append([
                    tx_id,
                    str(chro.decode('ascii', 'ignore')),
                    int(start),
                    int(end),
                    strand.decode('ascii', 'ignore'),
                    phase.decode('ascii', 'ignore')
                ])

    simp_gff = pd.merge(
        left = pd.Series(
            data=list(set(tx_gene[i] for i in tx_cds.keys())),
            name='gene_id'),
        right = pd.DataFrame(data=_df),
        on='gene_id',
        how='inner',
    ).sort_values(['chr', 'start']).reset_index(drop=True)
    simp_gff['order'] = simp_gff.groupby('chr').cumcount() + 1
    genelist = simp_gff['gene_id'].to_list()

    table = Table(title='Results Summary', )
    table.add_column('Entries Type', style='cyan', no_wrap=True)
    table.add_column('Quantity', style='green', justify="right")
    table.add_row('Protein Coding Gene', f'{len(genelist)}')
    table.add_row('Transcriptable Gene', f'{len(gene_txs.keys())}')

    table.add_row('Protein Coding Transcript', f'{len(tx_cds.keys())}')
    table.add_row('All Transcript', f'{len(tx_gene.keys())}')
    table.add_row('CDS', f'{sum(len(sub) for sub in tx_cds.values())}')
    console.print(table)

    return simp_gff, genelist, dict(gene_txs), dict(tx_gene), dict(tx_cds)

def gff3fixer(gff3_file_path: str, mode: str):
    pass
