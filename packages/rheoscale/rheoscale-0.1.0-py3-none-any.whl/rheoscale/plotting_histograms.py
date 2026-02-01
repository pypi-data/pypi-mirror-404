import pandas as pd
import numpy as np

from .data_structures import HistogramData
import matplotlib
import sys
if "debugpy" in sys.modules:
    matplotlib.use("Agg")

import matplotlib.pyplot as plt

def plot_all_positions(positions: list, hist_list: list, dead_extremum, WT_value,dead_value,save_path, neutral_bin_size, prefix='', all_pos=False, is_even_bins=False):
    master_hist_data = hist_list[0]
    for i in range(len(positions)):
        name = prefix+'_pos_'+str(positions[i])
        if all_pos:
             make_tuning_plot_one_pos(hist_list[i], dead_extremum, WT_value,dead_value, neutral_bin_size, save_path, tle=name, is_even_bins=is_even_bins)
        if i!=0:
             master_hist_data+= hist_list[i]
    all_title = prefix+'_all_positions'
    make_tuning_plot_one_pos(master_hist_data, dead_extremum, WT_value,dead_value, neutral_bin_size, save_path, all_title, is_all=True, is_even_bins=is_even_bins)

    
def make_tuning_plot_one_pos(hist_data: HistogramData , dead_extremum, WT_value, dead_value, neutral_bin_size,path,     
    tle: str = "Histogram",
    is_all: bool = False,
    is_even_bins: bool = False,
    xlabel: str = "Value",
    ylabel: str = "Count",
    log_y: bool = True,
    label_precision: int = 2):
        
        counts = hist_data.counts
        bin_edges = hist_data.bin_edges

        # ---- sanity check ----
        if len(bin_edges) != len(counts) + 1:
            raise ValueError("bin_edges must be one element longer than counts")
        if is_even_bins:
             if dead_extremum == 'Min':
                  bin_edges[0] = dead_value
             else:
                  bin_edges[-1] = dead_value
        
        # bin_widths = np.diff(bin_edges)
        # bin_centers = bin_edges[:-1] + bin_widths / 2

        bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
        bin_widths = np.diff(bin_edges)

        
        fmt = f"{{:.{label_precision}f}}"
        bin_labels = [
            f"{fmt.format(left)}–{fmt.format(right)}"
            for left, right in zip(bin_edges[:-1], bin_edges[1:])
        ]

        # ---- create figure & axes ----
        fig, ax = plt.subplots()

        # ---- plot ----
        ax.bar(
            bin_centers,
            counts,
            width=bin_widths*0.85,
            align="center",
            color='black'
        )
        
        

        WT_index =  np.digitize(WT_value, bin_edges) - 1
        WT_bin_center = bin_centers[WT_index]

        ax.axvline(dead_value, color='red')
        ax.axvspan(WT_value-(neutral_bin_size/2), WT_value+(neutral_bin_size/2), alpha=.55, color='green')

        # ---- axes formatting ----
        if not is_all:
            ax.set_ylim(0.001, 21)
            ax.set_yticks([i for i in range(5,21, 5)])
        else:
            
            ax.set_yscale('log')
            ax.set_ylim(1)
        ax.set_xticks(bin_centers)
        ax.set_xticklabels(bin_labels, rotation=45, ha="right")

        ax.set_xlabel(xlabel)
        ax.set_title(tle)

        if log_y:
            pass
            #ax.set_yscale("log")

        fig.tight_layout()
        plt.savefig(rf'{path}\{tle}.png')
        print(fr'#####saved to {path}\{tle}.png')
        plt.close()

        