from mplsoccer import (
    Radar,
    FontManager,
)
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

fm_rubik = FontManager(
    "https://raw.githubusercontent.com/google/fonts/main/ofl/"
    "rubikmonoone/RubikMonoOne-Regular.ttf"
)


class Radarchart:
    def __init__(
        self,
        group_1,
        group_2,
        params,
        low,
        high,
        lower_is_better,
        group1_c="#0A5B3A",
        group2_c="#FF4B44",
    ):
        self.radar = Radar(
            params,
            min_range=low,
            max_range=high,
            lower_is_better=lower_is_better,
            # whether to round any of the labels to integers instead of decimal places
            round_int=[True] * len(params),
            num_rings=2,  # the number of concentric circles (excluding center circle)
            ring_width=1,
            center_circle_radius=1,
        )
        self.fig, self.ax = self.radar.setup_axis()
        self.ax.set_facecolor((0, 0, 0, 0))  # (R, G, B, Alpha)
        self.group_1 = group_1
        self.group_2 = group_2
        self.group1_c = group1_c
        self.group2_c = group2_c

    def draw(self, save_figure: bool = False, show_figure: bool = True):
        """Draw Radarchart

        Args:
            save_figure (bool, optional): _description_. Defaults to False.
            show_figure (bool, optional): _description_. Defaults to True.
        """
        # Draw inner rings with white lines and transparent category background
        rings_inner = self.radar.draw_circles(
            ax=self.ax, facecolor="none", edgecolor="white", alpha=1
        )
        # Draw outer rings with white lines and transparent category background
        rings_outer = self.radar.draw_circles(
            ax=self.ax, facecolor="none", edgecolor="white", alpha=1
        )

        radar1, vertices1 = self.radar.draw_radar_solid(
            self.group_1,
            ax=self.ax,
            kwargs={"facecolor": "none", "alpha": 1, "lw": 1.5, "edgecolor": "#0A5B3A"},
        )
        radar2, vertices2 = self.radar.draw_radar_solid(
            self.group_2,
            ax=self.ax,
            kwargs={"facecolor": "none", "alpha": 1, "lw": 1.5, "edgecolor": "#FF4B44"},
        )

        self.ax.scatter(
            vertices1[:, 0],
            vertices1[:, 1],
            c="#0A5B3A",
            edgecolors="#0A5B3A",
            s=100,
            zorder=1,
        )
        self.ax.scatter(
            vertices2[:, 0],
            vertices2[:, 1],
            c="#FF4B44",
            edgecolors="#FF4B44",
            s=100,
            zorder=1,
        )

        # range_labels = radar.draw_range_labels(ax=ax, fontsize=20)
        param_labels = self.radar.draw_param_labels(
            ax=self.ax, fontsize=30, color="white"
        )

        # Add data labels for each point in group_1 with padding and background
        for i, (x, y) in enumerate(vertices1):
            label = f"{int(self.group_1[i])}"
            self.ax.annotate(
                label,
                (x, y),
                textcoords="offset points",
                xytext=(0, 20),  # Adjust the vertical padding here
                ha="center",
                va="center",
                fontsize=20,
                color="white",
                fontweight="bold",
                bbox=dict(
                    boxstyle="round,pad=0.5",
                    edgecolor="none",
                    facecolor=self.group1_c,
                    alpha=1,
                ),
            )

        # Add data labels for each point in group_2 with padding and background
        for i, (x, y) in enumerate(vertices2):
            label = f"{int(self.group_2[i])}"
            self.ax.annotate(
                label,
                (x, y),
                textcoords="offset points",
                xytext=(40, 30),  # Adjust the vertical padding here
                ha="center",
                va="center",
                fontsize=20,
                color="white",
                fontweight="bold",
                bbox=dict(
                    boxstyle="round,pad=0.5",
                    edgecolor="none",
                    facecolor=self.group2_c,
                    alpha=1,
                ),
            )

        if save_figure:
            current_datetime = datetime.now()
            formatted_datetime = current_datetime.strftime("%d-%m-%y_%H-%M-%S")
            plt.savefig(
                f"./images/radar/radar_{str(formatted_datetime)}.png",
                dpi=300,
                bbox_inches="tight",
                transparent=True,
            )
        if show_figure:
            plt.show()
            
if __name__=="__main__":
    radar = Radarchart()
    radar.draw_radarchart()
