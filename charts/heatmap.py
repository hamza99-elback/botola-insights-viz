import os
import sys

from matplotlib.colors import LinearSegmentedColormap

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from mplsoccer import FontManager, Pitch, VerticalPitch, create_transparent_cmap
from scipy.ndimage import gaussian_filter

from tools.json_tool import JsonTool

# fm_rubik = FontManager(
#     "https://raw.githubusercontent.com/google/fonts/main/ofl/"
#     "rubikmonoone/RubikMonoOne-Regular.ttf"
# )


class Heatmap:
    def __init__(
        self,
        pitch,
        data,
        pad_bottom=0.5,
        half=False,
        goal_type="box",
        goal_alpha=0.8,
        pitch_type="opta",
        figsize=(8, 10),
        pitch_color="#FFFFFF",
    ):
        self.pitch = pitch(
            pad_bottom=pad_bottom,
            half=half,
            goal_type=goal_type,
            goal_alpha=goal_alpha,
            # pitch_type='custom',
            # pitch_length=120,
            # pitch_width=80
        )
        self.figsize = figsize
        self.pitch_color = pitch_color
        # self.fig, self.ax = self.pitch.draw(figsize=figsize)
        self.data = data
        if "count" not in self.data.columns:
            self.data["count"] = 1

    def draw_v2(self, save_figure: bool = False, show_figure: bool = False):
        pearl_earring_cmap_100 = LinearSegmentedColormap.from_list(
            "Pearl Earring - 100 colors",
            ["#F7F7F7", "#C384FF", "#00FFD4", "#FBFF00", "#FE5202"],
            N=80,
        )  # ['#F7F7F7', '#C384FF','#00FFD4', '#FBFF00', '#FE5202']
        pitch = VerticalPitch(
            line_color="#7E7E7E",
            line_zorder=2,
            pitch_color=self.pitch_color,
            pad_bottom=0,
            pad_left=10,
            pad_right=10,
            pad_top=0,
        )
        self.fig, self.ax = pitch.draw(figsize=self.figsize)

        kdeplot = pitch.kdeplot(
            self.data.x,
            self.data.y,
            ax=self.ax,
            cmap=pearl_earring_cmap_100,
            fill=True,
            levels=100,
            zorder=-1,
            thresh=0.01,
            weights=self.data["count"],
            multiple="stack",
        )
        if show_figure:
            plt.show()
        if save_figure:
            current_datetime = datetime.now()
            formatted_datetime = current_datetime.strftime("%d-%m-%y_%H-%M-%S")
            plt.savefig(
                f"./images/heatmap/heatmap_{str(formatted_datetime)}.png",
                dpi=300,
                bbox_inches="tight",
                transparent=True,
            )
        return self.fig, self.ax

    def draw(
        self,
        save_figure: bool = False,
        show_figure: bool = False,
        color_palette=["#FFFFFF00", "#D33131", "#5F0202"],
        line_color="#424242",
    ):
        # pearl_earring_cmap_100 = LinearSegmentedColormap.from_list("Pearl Earring - 100 colors", ['#FFFFFF',"#7082E7", "#1B234E"], N=100) # ['#F7F7F7', '#C384FF','#00FFD4', '#FBFF00', '#FE5202'], ['none','#C384FF','#00FFD4', '#FBFF00', '#FE5202']
        # pearl_earring_cmap_100 = LinearSegmentedColormap.from_list("Pearl Earring - 100 colors", ['#FFFFFF',"#70E7CD", "#1B4E2C"], N=100)
        pearl_earring_cmap_100 = LinearSegmentedColormap.from_list(
            "Pearl Earring - 100 colors", color_palette, N=100
        )

        pitch = VerticalPitch(
            line_color=line_color,
            line_zorder=2,
            pitch_color=self.pitch_color,
            pad_bottom=0,
            pad_left=0,
            pad_right=0,
            pad_top=0,
            pitch_type="opta",
            pitch_length=100,
            pitch_width=100,
        )
        self.fig, self.ax = pitch.draw(figsize=self.figsize)
        bin_statistic = pitch.bin_statistic(
            self.data.x,
            self.data.y,
            statistic="count",
            bins=(100, 100),
            values=self.data["count"],
        )
        bin_statistic["statistic"] = gaussian_filter(bin_statistic["statistic"], 4)
        pcm = pitch.heatmap(
            bin_statistic,
            ax=self.ax,
            cmap=pearl_earring_cmap_100,
            edgecolors="none",
            zorder=-1,
            alpha=1,
        )
        if show_figure:
            plt.show()
        if save_figure:
            current_datetime = datetime.now()
            formatted_datetime = current_datetime.strftime("%d-%m-%y_%H-%M-%S")
            self.fig.savefig(
                f"./images/heatmap/heatmap_{str(formatted_datetime)}.png",
                dpi=300,
                bbox_inches="tight",
                transparent=True,
            )
        return self.fig, self.ax


if __name__ == "__main__":
    json_tool = JsonTool(path="./data/heatmap_boulacsout.json")
    data = json_tool.get_data()
    df_heatmap = (
        pd.DataFrame(data["points"])
        if hasattr(data, "points")
        else pd.DataFrame(data["heatmap"])
    )
    pitch = Heatmap(data=df_heatmap, pitch=VerticalPitch)
    pitch.draw(show_figure=True, save_figure=True)
    print(data)
