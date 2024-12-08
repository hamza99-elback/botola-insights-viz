import matplotlib.pyplot as plt
import matplotlib.patches as patch
import matplotlib.cm as cm
import numpy as np
import pandas as pd
from datetime import datetime



class ShotGoalLocation:
    def __init__(
        self,
        data: list[dict],
        player_type: str = "player",
        color: str = "#62FF81",
    ):
        self.data = data
        self.color= color
        self.edge_color= color
        self.player_type = player_type

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
            if self.player_type=="player":
                scale = 1000*p["xg"]
                label="Goal" if p["shotType"]=="goal" else "No Goal"
                color = self.color if p["shotType"]=="goal" else "none"
                edge_color = "none" if p["shotType"]=="goal" else self.edge_color
            elif self.player_type=="goal_keeper":
                scale = 1000*p["xg"]
                label="Save" if p["shotType"]=="save" else "Goal"
                color = self.color if p["shotType"]=="save" else "none"
                edge_color = "none" if p["shotType"]=="save" else self.edge_color
            goal[idx].scatter(p['GoalMouthCoordinatesY'], p['GoalMouthCoordinatesZ'], c=color, s=scale, label=label, edgecolors=edge_color, linewidths=0.9)

        # Add twitter logo
        ax = fig.add_axes([0.92, 0.025, 0.04, 0.04])
        ax.axis("off")
        # plt.show()
        # badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
        # ax.imshow(badge)
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%d-%m-%y_%H-%M-%S")
        plt.savefig(f'./images/goal_location/shots_{str(formatted_datetime)}.png', dpi=300, bbox_inches='tight', transparent=True)
        return fig, ax


if __name__ == "__main__":
    data = pd.read_excel("./data/wac_mas_shootmap.xlsx")
    columns_to_keep = [
        "GoalMouthCoordinatesY",
        "GoalMouthCoordinatesZ",
        "shotType",
        "xg",
    ]
    df_goal_location = data[columns_to_keep]
    df_goal_location["GoalMouthCoordinatesY"] = df_goal_location[
        "GoalMouthCoordinatesY"
    ].astype(float)
    df_goal_location["GoalMouthCoordinatesZ"] = df_goal_location[
        "GoalMouthCoordinatesZ"
    ].astype(float)
    df_goal_location["xg"] = df_goal_location["xg"].astype(float)
    df_goal_location["shotType"] = df_goal_location["shotType"].astype(str)
    df_goal_location = df_goal_location.loc[df_goal_location["shotType"].isin(['save', 'goal'])]
    shot_goal_location = ShotGoalLocation(
        data=df_goal_location.to_records(), color='yellow',  player_type="goal_keeper"
    )
    fig, ax = shot_goal_location.draw()
    print(data)
