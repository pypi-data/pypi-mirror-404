#  Copyright (C) 2025-2026, HYLi360.
#  Free software distributed under the terms of the GNU GPL-3.0 license,
#  and comes with ABSOLUTELY NO WARRANTY.
#  See at <https://www.gnu.org/licenses/gpl-3.0.en.html>

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import Colormap
from matplotlib.path import Path

import pandas as pd

from typing import Optional, Literal

class MacroCollPlot:
    def __init__(
            self,
            genome_structure_top: pd.DataFrame,
            genome_structure_bottom: pd.DataFrame,
            species_name_top: str,
            species_name_bottom: str,
            anchor: zip,
            h: tuple[float, float] = (0.6, 0.4),
            x: tuple[float, float] = (0.2, 0.9),
            spacing=0.1,
            collbox_style: Literal['polygon', 'bezier'] = 'bezier',
            chr_namels_top: Optional[list] = None,
            chr_namels_bottom: Optional[list] = None,
            savefile: Optional[str] = None,
    ):
        self.genome_structure_top = genome_structure_top
        self.genome_structure_bot = genome_structure_bottom
        self.species_name_top = species_name_top
        self.species_name_bot = species_name_bottom
        self.anchor = anchor
        self.h = h
        self.x = x
        self.spacing = spacing
        self.collbox_style = collbox_style
        self.chr_namels_top = chr_namels_top
        self.chr_namels_bot = chr_namels_bottom
        self.savefile = savefile

    def draw(self):
        self._chro_init()
        self._collbox_init()

        palette = plt.get_cmap('tab10')

        canvas = plt.gca()

        # Chromosomes
        for start, length, chrname in self.chrposls_top:
            canvas.add_patch(patches.Rectangle(
                xy=(start, self.h[0]-0.003),
                width=length,
                height=0.006,
                fill=True,
                fc=palette(0),
                ec='none',))
            canvas.add_patch(patches.Rectangle(
                xy=(start, self.h[0]-0.01),
                width=length,height=0.02,
                fill=False,
                ec=(0.2,0.2,0.2,0.2)))
            canvas.text(
                x=start + length / 2,
                y=self.h[0] + 0.025,
                s=chrname,
                ha='center',
                va='center',
                backgroundcolor='white')

        for start, length, chrname in self.chrposls_bot:
            canvas.add_patch(patches.Rectangle(xy=(start, self.h[1] - 0.003),width=length,height=0.006,fill=True, fc=palette(1),ec='none',))
            canvas.add_patch(patches.Rectangle(xy=(start, self.h[1] - 0.01), width=length,height=0.02, fill=False,ec=(0.2,0.2,0.2,0.2)))
            canvas.text(x=start + length / 2, y=self.h[1] - 0.025, s=chrname, ha='center', va='center', backgroundcolor='white')

        # Add collboxes
        if self.collbox_style == 'bezier':
            for collbox in self.collbox:
                collbox_patch = _get_bezier_ribbon(collbox[0], collbox[1], collbox[2], collbox[3], self.h[0], self.h[1], 'grey')
                canvas.add_patch(collbox_patch)
        if self.collbox_style == 'polygon':
            for collbox in self.collbox:
                collbox_patch = _get_polygon_ribbon(collbox[0], collbox[1], collbox[2], collbox[3], self.h[0], self.h[1], 'grey')
                canvas.add_patch(collbox_patch)

        # Add species name
        canvas.text(x=0.12, y=self.h[0], s=self.species_name_top, size=15, ha='center', va='center', fontstyle='italic')
        canvas.text(x=0.12, y=self.h[1], s=self.species_name_bot, size=15, ha='center', va='center', fontstyle='italic')

        # Close the axis
        plt.axis('off')

        plt.show()

    def _chro_init(self):
        """Preprocessing steps prior of plotting."""
        # set chromesome list.
        chrls1 = self.genome_structure_top['chr'].drop_duplicates().tolist()
        if self.chr_namels_top is not None:
            self.chr_namels_top = [chro for chro in self.chr_namels_top if chro in chrls1]
        else:
            self.chr_namels_top = chrls1

        chrls2 = self.genome_structure_bot['chr'].drop_duplicates().tolist()
        if self.chr_namels_bot is not None:
            self.chr_namels_bot = [chro for chro in self.chr_namels_bot if chro in chrls2]
        else:
            self.chr_namels_bot = chrls2

        genes_num1 = len(self.genome_structure_top[self.genome_structure_top['chr'].isin(self.chr_namels_top)])
        genes_num2 = len(self.genome_structure_bot[self.genome_structure_bot['chr'].isin(self.chr_namels_bot)])

        sf1 = (self.x[1] - self.x[0])/(genes_num1 * (1 + self.spacing))
        sf2 = (self.x[1] - self.x[0])/(genes_num2 * (1 + self.spacing))

        if (len(self.chr_namels_top) - 1) != 0:
            space_len1 = self.spacing * genes_num1 / (len(self.chr_namels_top) - 1)
        else:
            space_len1 = 0

        if (len(self.chr_namels_top) - 1) != 0:
            space_len2 = self.spacing * genes_num2 / (len(self.chr_namels_bot) - 1)
        else:
            space_len2 = 0

        start1, length1, space_end1 = [], [], [self.x[0]]
        start2, length2, space_end2 = [], [], [self.x[0]]

        for chro in self.chr_namels_top:
            start1.append(space_end1[-1])
            length1.append(len(self.genome_structure_top[self.genome_structure_top['chr'] == chro]) * sf1)
            space_end1.append(start1[-1] + length1[-1] + space_len1 * sf1)

        for chro in self.chr_namels_bot:
            start2.append(space_end2[-1])
            length2.append(len(self.genome_structure_bot[self.genome_structure_bot['chr'] == chro]) * sf2)
            space_end2.append(start2[-1] + length2[-1] + space_len2 * sf2)

        self.sf_top, self.sf_bot = sf1, sf2
        self.chrposls_top, self.chrposls_bot = tuple(zip(start1, length1, self.chr_namels_top)), tuple(zip(start2, length2, self.chr_namels_bot))
        self.startd_top, self.startd_bot = dict(zip(self.chr_namels_top, start1)), dict(zip(self.chr_namels_bot, start2))

    def _collbox_init(self):
        res = []
        for chr1, chr2, loc1start, loc1end, loc2start, loc2end in self.anchor:
            if (str(chr1) in self.startd_top) and (str(chr2) in self.startd_bot):
                res.append([
                    self.startd_top[str(chr1)] + loc1start * self.sf_top,
                    self.startd_top[str(chr1)] + loc1end * self.sf_top,
                    self.startd_bot[str(chr2)] + loc2start * self.sf_bot,
                    self.startd_bot[str(chr2)] + loc2end * self.sf_bot,
                ])
        self.collbox = res


class MicroCollPlot:
    def __init__(
            self,
            draw_method: Literal['gene_name', 'gene_index', 'base_range'],
            gff1: pd.DataFrame,
            gff2: pd.DataFrame,
            anchor: pd.DataFrame,
            species_name_top: str,
            species_name_bottom: str,
            list_param1: list,
            list_param2: list,
            y: tuple[float, float] = (0.6, 0.4),
            x: tuple[float, float] = (0.2, 0.9),
            reverse: tuple[bool, bool] = (False, False),
            collbox_style: Literal['polygon', 'bezier'] = 'polygon',
            palette: Colormap = plt.get_cmap('tab10'),
            savefile: Optional[str] = None,
    ):
        self.canvas = None
        self.palette = plt.get_cmap('tab10')
        gff1 = (gff1.loc[:,['gene_id', 'start', 'end', 'strand']]
                .rename(columns={'gene_id': 'gene_top', 'start': 'x_top_start', 'end': 'x_top_end', 'strand': 'strand_top'}))
        gff2 = (gff2.loc[:,['gene_id', 'start', 'end', 'strand']]
                .rename(columns={'gene_id': 'gene_bot', 'start': 'x_bot_start', 'end': 'x_bot_end', 'strand': 'strand_bot'}))
        anchor = (anchor.loc[:,['gene1', 'chr1', 'gene2', 'chr2']]
                  .rename(columns={'gene1': 'gene_top', 'chr1': 'chr_top', 'gene2': 'gene_bot', 'chr2': 'chr_bot'}))

        anchor = pd.merge(left=anchor, right=gff1, on='gene_top', how='inner')
        anchor = pd.merge(left=anchor, right=gff2, on='gene_bot', how='inner')
        # anchor: gene_top, chr_top, gene_bot, chr_bot, x_top_start, x_top_end, strand_top, x_bot_start, x_bot_end, strand_bot
        self.anchor = anchor

        self.draw_method = draw_method
        self.list_param1 = list_param1
        self.list_param2 = list_param2

        self.species_name_top = species_name_top
        self.species_name_bot = species_name_bottom

        self.ytop, self.ybot = y
        self.xleft, self.xright = x
        self.reverse_top = reverse[0]
        self.reverse_bot = reverse[1]
        self.collbox_style = collbox_style
        self.palette = palette
        self.savefile = savefile

    def show(self):
        self._range_init()
        self._arrows_collboxes_init()

        self.canvas = plt.gca()

        # Add DNA strand
        self.canvas.add_patch(patches.Rectangle(xy=(self.xleft, self.ytop - 0.002), width=self.xright - self.xleft, height=0.004, fc='grey', ec='none'))
        self.canvas.add_patch(patches.Rectangle(xy=(self.xleft, self.ybot - 0.002), width=self.xright - self.xleft, height=0.004, fc='grey', ec='none'))

        # Add gene arrows
        for genearrow in self.genearrows:
            self.canvas.add_patch(genearrow)

        # Add collboxes
        for collbox in self.collboxes:
            self.canvas.add_patch(collbox)

        # Add texts
        # Species name
        self.canvas.text(
            x=0.09, y=self.ytop, s=self.species_name_top, size=15,
            ha='center', va='bottom', fontstyle='italic')
        self.canvas.text(
            x=0.09, y=self.ybot, s=self.species_name_bot, size=15,
            ha='center', va='bottom', fontstyle='italic')

        # Sequence info
        range1 = f'{self.x_top_startbase/1000000:03f}~{self.x_top_endbase/1000000:03f}Mbp'
        range2 = f'{self.x_bot_startbase/1000000:03f}~{self.x_bot_endbase/1000000:03f}Mbp'
        self.canvas.text(x=0.09, y=self.ytop, s=range1, size=15, ha='center', va='top')
        self.canvas.text(x=0.09, y=self.ybot, s=range2, size=15, ha='center', va='top')

        # Close the axis
        plt.axis('off')

        plt.show()

    def _range_init(self):
        # Define top and botton ranges and scale factors
        # Method 1: genome name list
        if self.draw_method == 'gene_name':
            # Get gene table with those genes
            self.anchor = self.anchor[self.anchor['gene_top'].isin(self.list_param1)]
            self.anchor = self.anchor[self.anchor['gene_bot'].isin(self.list_param2)]

        # Method 2: genome index list
        if self.draw_method == 'gene_index':
            # Get gene table in that range
            self.anchor = self.anchor[self.list_param1]
            self.anchor = self.anchor[self.list_param2]

        # Method 3: base range
        if self.draw_method == 'base_range':
            # Get gene table in that range
            # list param structure: [chr_id, base_start, base_end]
            self.anchor = self.anchor[self.anchor['chr_top'] == self.list_param1[0]]
            self.anchor = self.anchor[self.anchor['chr_bot'] == self.list_param2[0]]

            self.x_top_startbase, self.x_top_endbase = self.list_param1[1:]
            self.x_bot_start, self.x_bot_endbase = self.list_param2[1:]

        else:
            # Set base range
            x1, x2 = self.anchor['x_top_start'].min(), self.anchor['x_top_end'].max()
            x3, x4 = self.anchor['x_bot_start'].min(), self.anchor['x_bot_end'].max()

            # Add some offset (3%)
            self.x_top_startbase = int(x1 - (x2 - x1 + 1) * 0.03)
            self.x_top_endbase   = int(x2 + (x2 - x1 + 1) * 0.03)
            self.x_bot_startbase = int(x3 - (x4 - x3 + 1) * 0.03)
            self.x_bot_endbase   = int(x4 + (x4 - x3 + 1) * 0.03)

        if self.reverse_top:
            self.x_top_startbase, self.x_top_endbase = self.x_top_endbase, self.x_top_startbase
        if self.reverse_bot:
            self.x_bot_startbase, self.x_bot_endbase = self.x_bot_endbase, self.x_bot_startbase

        # Set scale factors
        self.sf_top = (self.xright - self.xleft) / (abs(self.x_top_endbase - self.x_top_startbase) + 1)
        self.sf_bot = (self.xright - self.xleft) / (abs(self.x_bot_endbase - self.x_bot_startbase) + 1)

        # todo: Multiple chromosome support?

    def _arrows_collboxes_init(self):
        # Prepare gene arrows and collboxes
        self.genearrows, self.collboxes = [], []
        # gene_top, chr_top, gene_bot, chr_bot, x_top_start, x_top_end, strand_top, x_bot_start, x_bot_end, strand_bot
        for idx, info in self.anchor.iterrows():
            gene_top, chr_top, gene_bot, chr_bot, x_top_start, x_top_end, strand_top, x_bot_start, x_bot_end, strand_bot = info
            x_top_start, x_top_end = (x_top_start, x_top_end) if strand_top == '+' else (x_top_end, x_top_start)
            x_bot_start, x_bot_end = (x_bot_start, x_bot_end) if strand_bot == '+' else (x_bot_end, x_bot_start)

            if self.reverse_top:
                x1 = self.xright - (x_top_start - self.x_top_endbase) * self.sf_top
                x2 = self.xright - (x_top_end - self.x_top_endbase) * self.sf_top
            else:
                x1 = self.xleft + (x_top_start - self.x_top_startbase) * self.sf_top
                x2 = self.xleft + (x_top_end - self.x_top_startbase) * self.sf_top

            if self.reverse_bot:
                x3 = self.xright - (x_bot_start - self.x_bot_endbase) * self.sf_bot
                x4 = self.xright - (x_bot_end - self.x_bot_endbase) * self.sf_bot
            else:
                x3 = self.xleft + (x_bot_start - self.x_bot_startbase) * self.sf_bot
                x4 = self.xleft + (x_bot_end - self.x_bot_startbase) * self.sf_bot

            # For top
            self.genearrows.append(patches.FancyArrowPatch(
                posA=(x1, self.ytop), posB=(x2, self.ytop), color=self.palette(0), mutation_scale=100,))

            # For bottom
            self.genearrows.append(patches.FancyArrowPatch(
                posA=(x3, self.ybot), posB=(x4, self.ybot), color=self.palette(1), mutation_scale=100,))
            
            # For collbox
            if self.collbox_style == 'polygon':
                self.collboxes.append(_get_polygon_ribbon(
                    x1, x2, x4, x3, self.ytop, self.ybot, 'grey'))

            if self.collbox_style == 'bezier':
                self.collboxes.append(_get_bezier_ribbon(
                    x1, x2, x4, x3, self.ytop, self.ybot, 'grey'))

def _get_polygon_ribbon(
        x_top_start,
        x_top_end,
        x_bot_start,
        x_bot_end,
        ytop, ybot,
        color_code
):
    return patches.Polygon([[x_top_start, ytop - 0.003],
                            [x_top_end, ytop - 0.003],
                            [x_bot_start, ybot + 0.003],
                            [x_bot_end, ybot + 0.003],],
                           fc=color_code, ec='none', lw=0, alpha=0.5)

def _get_bezier_ribbon(
        x_top_start,
        x_top_end,
        x_bot_start,
        x_bot_end,
        ytop, ybot,
        color_code
):
    mid_y = (ytop + ybot) / 2

    codes = [
        Path.MOVETO,
        Path.LINETO,

        Path.CURVE4,  # verts[2]
        Path.CURVE4,  # verts[3]
        Path.CURVE4,  # verts[4]

        Path.LINETO,

        Path.CURVE4,  # verts[6]
        Path.CURVE4,  # verts[7]
        Path.CURVE4,  # verts[8]

        Path.CLOSEPOLY,
    ]

    verts = [
        (x_top_start, ytop - 0.003),  # MOVETO
        (x_top_end, ytop - 0.003),    # LINETO

        (x_top_end, mid_y),           # CURVE4
        (x_bot_end, mid_y),           # CURVE4
        (x_bot_end, ybot + 0.003),    # CURVE4

        (x_bot_start, ybot + 0.003),  # LINETO

        (x_bot_start, mid_y),         # CURVE4
        (x_top_start, mid_y),         # CURVE4
        (x_top_start, ytop - 0.003),  # CURVE4

        (x_top_start, ytop - 0.003),  # CLOSEPOLY
    ]

    path = Path(verts, codes)
    patch = patches.PathPatch(path, fc=color_code, ec='none', lw=0, alpha=0.5)
    return patch
