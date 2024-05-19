import matplotlib.pyplot as plt
import matplotlib.patches as patch
import matplotlib.cm as cm
import numpy as np


class ShotGoalLocation:
    def __init__(
        self,
        color: str = "#62FF81",
        data: list[dict] = [
            {"GoalMouthCoordinatesY": 41.5, "GoalMouthCoordinatesZ": 50.2, "shotType": "miss", "xg": 0.1915},
            {"GoalMouthCoordinatesY": 46.9, "GoalMouthCoordinatesZ": 23.2, "shotType": "save", "xg": 0.03237},
            {"GoalMouthCoordinatesY": 58.2, "GoalMouthCoordinatesZ": 40.5, "shotType": "miss", "xg": 0.09457},
            {"GoalMouthCoordinatesY": 46.4, "GoalMouthCoordinatesZ": 8.8, "shotType": "goal", "xg": 0.2122},
            {"GoalMouthCoordinatesY": 47.6, "GoalMouthCoordinatesZ": 33.3, "shotType": "goal", "xg": 0.82},
            {"GoalMouthCoordinatesY": 49, "GoalMouthCoordinatesZ": 19.2, "shotType": "save", "xg": 0.1178},
        ],
    ):
        self.data = data
        self.color= color
        self.edge_color= color
        # self.label_c = {"goal": "#62FF81", "miss": "#FF4C4C", "save":"#FFE946", "block":"#4684FF"}

    def draw(self):
        """Draw the shot goal location chart

        Returns:
            _type_: _description_
        """
        mode = "normal"

        # Goal height
        goal_height_opta = 39.85
        goal_height_yards = 2.66667
        goal_height_factor = goal_height_yards / goal_height_opta

        # Goal width
        goal_width_yards = 8
        goal_width_opta = 9.6
        goal_width_factor = goal_width_yards / goal_width_opta

        # Goalkeeper midriff position
        gk_y_pos_yards = 0
        gk_y_pos_opta = 50
        gk_z_pos_yards = 2.06667 / 2
        gk_z_pos_opta = gk_z_pos_yards * (1 / goal_height_factor)

        # Set up figure
        fig = plt.figure(constrained_layout=False, figsize=(14, 10))
        # fig.set_facecolor("#313332")
        gs = fig.add_gridspec(
            1,
            1,
            left=0.03,
            right=0.97,
            top=0.845,
            bottom=0.07,
            wspace=0.2,
            hspace=0.08,
            height_ratios=[1],
        )

        # Define colourmap
        marker_cmap = cm.get_cmap("RdYlGn")
        marker_cmap = marker_cmap(np.linspace(0, 1, 256))

        # Define list of goal axes
        goal = [0] * 1
        goal[0] = fig.add_subplot(gs[0, 0])

        # Set width and height to include per goal
        # width_lower_lim = 43.5
        width_lower_lim = 40
        width_upper_lim = 60
        height_upper_lim = 60
        height_lower_lim = -45
        # width_upper_lim = 56.5
        # height_upper_lim = 55

        # Format goals
        for goal_ax in goal:

            # Colour and axes
            goal_ax.set_facecolor("#313332")
            for axis in ["bottom", "left", "right", "top"]:
                goal_ax.spines[axis].set_color("w")

            goal_ax.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
            goal_ax.tick_params(axis="y", which="both", left=False, labelleft=False)

            # Draw goal-line and goal posts
            goal_ax.plot([width_lower_lim, width_upper_lim], [0, 0], lw=1, color="w")
            goal_ax.plot([45.2, 45.2], [0, 39.85], lw=2.5, color="w")
            goal_ax.plot([54.8, 54.8], [0, 39.85], lw=2.5, color="w")
            goal_ax.plot([45.2, 54.8], [39.85, 39.85], lw=2.5, color="w")

            # Draw 6-yard box horizontal line
            goal_ax.plot([40, 60], [-10.175, -10.175], lw=1.5, color="w")

            # Draw penalty spot
            ellipse = patch.Ellipse(
                xy=(50, -40), width=0.5, height=0.5, edgecolor="w", fc="w", lw=2
            )
            goal_ax.add_artist(ellipse)

            # Draw and label GK position
            goal_ax.scatter(
                gk_y_pos_opta,
                gk_z_pos_opta,
                color="w",
                s=10,
                lw=0.5,
                edgecolor="#313332",
                zorder=1,
            )
            goal_ax.text(
                gk_y_pos_opta,
                gk_z_pos_opta + 2,
                "GK",
                ha="center",
                fontsize=7,
                color="w",
                zorder=1,
            )

            # Set axis limits
            goal_ax.set_xlim(width_upper_lim, width_lower_lim)
            goal_ax.set_ylim(height_lower_lim, height_upper_lim)

            # Set aspect ratio
            goal_ax.set_aspect(10.7 / (3 * 39.85))

        # Loop through top players
        idx = 0
        pen = self.data

        for p in pen:
            # goal[idx].plot([50,pen['goalMouthY']], [-40, pen['goalMouthZ']], 'w', ls = 'dashed', zorder=3, lw = 0.5)
            scale = 300*p["xg"]
            label="Goal" if p["shotType"]=="goal" else "No Goal"
            color = self.color if p["shotType"]=="goal" else "none"
            edge_color = "none" if p["shotType"]=="goal" else self.edge_color
            goal[idx].scatter(p['GoalMouthCoordinatesY'], p['GoalMouthCoordinatesZ'], c=color, s=scale, label=label, edgecolors=edge_color, linewidths=0.9)

        # Add twitter logo
        ax = fig.add_axes([0.92, 0.025, 0.04, 0.04])
        ax.axis("off")
        plt.show()
        # badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
        # ax.imshow(badge)
        # fig.savefig(f"player_penalty_takers/{title_str.replace(' ','_')}-{year_str}-top-penalty-takers", dpi=300)
        return fig, ax


# if __name__ == "__main__":
#     data = [
#             {"goalMouthY": 41.5, "goalMouthZ": 50.2, "shotType": "miss", "xg": 0.1915},
#             {"goalMouthY": 46.9, "goalMouthZ": 23.2, "shotType": "save", "xg": 0.03237},
#             {"goalMouthY": 58.2, "goalMouthZ": 40.5, "shotType": "miss", "xg": 0.09457},
#             {"goalMouthY": 46.4, "goalMouthZ": 8.8, "shotType": "goal", "xg": 0.2122},
#             {"goalMouthY": 47.6, "goalMouthZ": 33.3, "shotType": "goal", "xg": 0.82},
#             {"goalMouthY": 49, "goalMouthZ": 19.2, "shotType": "save", "xg": 0.1178},
#         ]
#     shot_goal_location = ShotGoalLocation(data=data)
#     shot_goal_location.draw()
