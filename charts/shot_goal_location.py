import matplotlib.pyplot as plt
import matplotlib.patches as patch
import matplotlib.cm as cm
import numpy as np
import pandas as pd
from datetime import datetime
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
from tools.json_tool import JsonTool
from data_processing.shootmap_processor import ShootmapProcessor


class ShotGoalLocation:
    def __init__(
        self,
        data: list[dict],
        player_type: str = "player",
        color: str = "#62FF81",
        edge_color: str = "#005586",
    ):
        self.data = data
        self.color= color
        self.edge_color= edge_color
        self.player_type = player_type

    def draw(self, save_figure=False, show_figure=True):
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
            goal_ax.set_facecolor("none")
            for axis in ["bottom", "left", "right", "top"]:
                goal_ax.spines[axis].set_color("black")

            goal_ax.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
            goal_ax.tick_params(axis="y", which="both", left=False, labelleft=False)

            # Draw goal-line and goal posts
            goal_ax.plot([width_lower_lim, width_upper_lim], [0, 0], lw=1, color="black")
            goal_ax.plot([45.2, 45.2], [0, 39.85], lw=2.5, color="black")
            goal_ax.plot([54.8, 54.8], [0, 39.85], lw=2.5, color="black")
            goal_ax.plot([45.2, 54.8], [39.85, 39.85], lw=2.5, color="black")

            # Draw 6-yard box horizontal line
            goal_ax.plot([40, 60], [-10.175, -10.175], lw=1.5, color="black")

            # Draw penalty spot
            ellipse = patch.Ellipse(
                xy=(50, -40), width=0.5, height=0.5, edgecolor="black", fc="black", lw=2
            )
            goal_ax.add_artist(ellipse)

            # Draw and label GK position
            goal_ax.scatter(
                gk_y_pos_opta,
                gk_z_pos_opta,
                color="black",
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
                color="black",
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
                color = self.color if p["shotType"]in ("post", "goal") else "none"
                marker = "o" if p["shotType"] in ("save", "goal") else "X"
                edge_color = self.edge_color if p["shotType"]=="goal" else self.color
            goal[idx].scatter(p['GoalMouthCoordinatesY'], p['GoalMouthCoordinatesZ'], c=color, s=scale, label=label, edgecolors=edge_color, linewidths=0.9, marker=marker)

        # Add twitter logo
        ax = fig.add_axes([0.92, 0.025, 0.04, 0.04])
        ax.axis("off")
        plt.show()
        # badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
        # ax.imshow(badge)
        if save_figure:
            current_datetime = datetime.now()
            formatted_datetime = current_datetime.strftime("%d-%m-%y_%H-%M-%S")
            plt.savefig(f'./images/goal_location/shots_{str(formatted_datetime)}.png', dpi=300, bbox_inches='tight', transparent=True)
        return fig, ax


if __name__ == "__main__":
    # data = pd.read_excel("./data/goal_location/bono_goal.xlsx")
    files_list = ["./data/goal_location/sen_egypt.json", "./data/goal_location/sen_civ.json"]
    for file in files_list:
        json_tool = JsonTool(path=file)
        input = json_tool.get_data()
        shootmap_processor = ShootmapProcessor(data=input['shotmap'])
        df_team1, df_team2 = shootmap_processor.process_data()
        if file == files_list[0]:
            data = df_team2[(df_team2["isHome"] == False) & (df_team2["situation"] == "shootout")]
        else:
            data = pd.concat([data, df_team2[(df_team2["isHome"] == False) & (df_team2["situation"] == "shootout")]], ignore_index=True)
    
    # data = pd.DataFrame(data['shotmap'])
    # data.rename(columns={"XG": "xg", 
    #                      "ShotType": "shotType", 
    #                      "goalMouthCoordinatesY": "GoalMouthCoordinatesY",
    #                      "goalMouthCoordinatesZ": "GoalMouthCoordinatesZ"}, inplace=True)
    data["xg"] = 0.5
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
    df_goal_location = df_goal_location.loc[df_goal_location["shotType"].isin(['save', 'goal', 'post'])]

     # Start generating shot goal location chart
    df_goal_location["GoalMouthCoordinatesY"] = df_goal_location["GoalMouthCoordinatesY"] - 0.3
    shot_goal_location = ShotGoalLocation(
        data=df_goal_location.to_records(), color="#00993B", edge_color="#013F19",  player_type="goal_keeper"
    )
    fig, ax = shot_goal_location.draw(save_figure=True)
    print(data)
