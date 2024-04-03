import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from mplsoccer import PyPizza, FontManager, grid
from datetime import datetime

fm_rubik = FontManager(
    "https://raw.githubusercontent.com/google/fonts/main/ofl/"
    "rubikmonoone/RubikMonoOne-Regular.ttf"
)


class Pizzachart:
    def __init__(
        self, categories, min_range, max_range, group_1, slice_colors, text_colors
    ):
        self.pizza = PyPizza(
            params=categories,  # list of parameters
            min_range=min_range,  # min range values
            max_range=max_range,  # max range values
            # background_color="#EBEBE9",     # background color
            straight_line_color="#EBEBE9",  # color for straight lines
            last_circle_color="white",
            last_circle_lw=2.5,
            other_circle_lw=0.2,
            other_circle_color="white",
            straight_line_lw=1,
            other_circle_ls="-.",
        )
        self.group_1 = group_1
        self.slice_colors = slice_colors
        self.text_colors = text_colors
        self.ax.set_facecolor((0, 0, 0, 0))

    def draw(self, save_figure: bool = False, show_figure: bool = True):
        """Draw Radarchart

        Args:
            save_figure (bool, optional): _description_. Defaults to False.
            show_figure (bool, optional): _description_. Defaults to True.
        """
        fig, ax = self.pizza.make_pizza(
            self.group_1_int,  # list of values
            figsize=(8, 8.5),  # adjust figsize according to your need
            # color_blank_space="same",        # use same color to fill blank space
            slice_colors=self.slice_colors,  # color for individual slices
            value_colors=self.text_colors,  # color for the value-text
            value_bck_colors=self.slice_colors,  # color for the blank spaces
            blank_alpha=0.4,  # alpha for blank-space colors
            kwargs_slices=dict(
                edgecolor="#F2F2F2", zorder=2, linewidth=1
            ),  # values to be used when plotting slices
            kwargs_params=dict(
                color="white", fontsize=9, va="center", wrap=True
            ),  # values to be used when adding parameter
            kwargs_values=dict(
                color="#000000",
                fontsize=12,
                zorder=3,
                bbox=dict(
                    edgecolor="#000000",
                    facecolor="cornflowerblue",
                    boxstyle="round,pad=0.5",
                    lw=1,
                ),
            ),  # values to be used when adding parameter-values
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


if __name__ == "__main__":
    pizza = Pizzachart()
    pizza.draw()
