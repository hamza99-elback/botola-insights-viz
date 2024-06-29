import matplotlib.pyplot as plt
from matplotlib import patheffects
from matplotlib.font_manager import FontProperties
from datetime import datetime
import os


class StackedBarChart:
    def __init__(
        self,
        total_values,
        proportions,
        data,
        figsize=(6, 4),
        home_c="#FE4844",
        away_c="#66F042",
    ):
        self.data = data
        self.home_values = self.data["home"]
        self.away_values = self.data["away"]
        self.item_name = self.data["itemName"]
        self.total_values = total_values
        self.proportions = proportions
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.y_pos = 0
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.abspath(os.path.dirname(ROOT_DIR)+"/fonts/Roboto-Medium.ttf")
        self.roboto = FontProperties(fname=font_path)
        self.home_c = home_c
        self.away_c = away_c

    def draw(self, save_figure: bool = False, show_figure: bool = True):
        """Draw Radarchart

        Args:
            save_figure (bool, optional): _description_. Defaults to False.
            show_figure (bool, optional): _description_. Defaults to True.
        """
        # Loop through each item
        for i, (proportion, item_name) in enumerate(
            zip(self.proportions, self.item_name)
        ):
            home_val, away_val = proportion
            total_val = home_val + away_val

            # Create rectangle with proportional color
            self.ax.add_patch(
                plt.Rectangle(
                    (0, self.y_pos),
                    home_val / total_val,
                    0.6,
                    color=self.home_c,
                    alpha=0.8,
                )
            )
            self.ax.add_patch(
                plt.Rectangle(
                    (home_val / total_val, self.y_pos),
                    away_val / total_val,
                    0.6,
                    color=self.away_c,
                    alpha=1,
                )
            )

            # Calculate x-coordinate for placing item name
            x_text = (home_val / total_val + away_val / total_val) / 2

            # Add item name inside the rectangle with bold font
            text = self.ax.text(
                x_text,
                self.y_pos + 0.25,
                item_name,
                ha="center",
                va="center",
                color="white",
                fontsize=14,
                fontweight="bold",
                fontproperties=self.roboto,
            )
            # Add shadow effect
            text.set_path_effects(
                [patheffects.withStroke(linewidth=3, foreground="#121212")]
            )
            label_1 = self.ax.text(
                0.06,
                self.y_pos + 0.25,
                f"{home_val}",
                ha="left",
                va="center",
                color="white",
                fontsize=14,
                fontweight="bold",
                fontproperties=self.roboto,
            )
            label_1.set_path_effects(
                [patheffects.withStroke(linewidth=3, foreground="#121212")]
            )
            label_2 = self.ax.text(
                1 - 0.06,
                self.y_pos + 0.25,
                f"{away_val}",
                ha="right",
                va="center",
                color="white",
                fontsize=14,
                fontweight="bold",
                fontproperties=self.roboto,
            )
            label_2.set_path_effects(
                [patheffects.withStroke(linewidth=3, foreground="#121212")]
            )
            # Increase y position for the next rectangle with some space
            self.y_pos += 1

        # Set y limit and hide y axis
        self.ax.set_ylim(
            -0.5, self.y_pos
        )  # Adjust the y limit to fit all rectangles with space
        self.ax.yaxis.set_visible(False)
        self.ax.xaxis.set_visible(False)
        # Hide spines (borders)
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["bottom"].set_visible(False)
        self.ax.spines["left"].set_visible(False)

        plt.subplots_adjust(left=0.15, right=0.9, top=1, bottom=0.1)
        if save_figure:
            current_datetime = datetime.now()
            formatted_datetime = current_datetime.strftime("%d-%m-%y_%H-%M-%S")
            plt.savefig(
                f"./images/barchart/stackedbarchart_{str(formatted_datetime)}.png",
                dpi=300,
                bbox_inches="tight",
                transparent=True,
            )
        if show_figure:
            plt.show()
        return self.fig, self.ax


if __name__ == "__main__":
    data = {
        "home": [1.42, 50, 16, 7, 7, 2],
        "away": [1.86, 50, 17, 6, 5, 5],
        "itemName": [
            "Expected goals",
            "Ball possession",
            "Total shots",
            "Shots on target",
            "Shots off target",
            "Blocked shots",
        ],
    }

    # Calculate proportions for the last column
    home_values = data["home"]
    away_values = data["away"]
    total_values = [home + away for home, away in zip(home_values, away_values)]
    proportions = [(home, away) for home, away in zip(home_values, away_values)]
    stackedbarchart = StackedBarChart(
        data=data, total_values=total_values, proportions=proportions
    )
    stackedbarchart.draw(show_figure=True, save_figure=True)
