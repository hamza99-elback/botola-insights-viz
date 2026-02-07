from mplsoccer import (
    VerticalPitch,
    Pitch,
    create_transparent_cmap,
    FontManager,
    arrowhead_marker,
    Sbopen,
)
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime


import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
from tools.json_tool import JsonTool
from data_processing.shootmap_processor import ShootmapProcessor

fm_rubik = FontManager('https://raw.githubusercontent.com/google/fonts/main/ofl/'
                       'rubikmonoone/RubikMonoOne-Regular.ttf')
class ShootMap:
    def __init__(
        self,
        pitch,
        team1_c: str="#FE4844",
        team2_c: str="#66F042",
        team1_edge_c: str="#383838",
        team2_edge_c: str="#383838",
        data: pd.DataFrame=None,
        df_team1 : pd.DataFrame=None,
        df_team2 : pd.DataFrame=None,
        pad_bottom=0.5,
        half=False,
        goal_type='line',
        goal_alpha=0.8,
        pitch_type="wyscout",
        figsize=(12, 10),
    ):
        self.pitch = pitch(
            pad_bottom=pad_bottom,
            half=half,
            goal_type=goal_type,
            goal_alpha=goal_alpha,
            pitch_type=pitch_type,
        )
        self.fig, self.ax = self.pitch.draw(figsize=figsize)
        self.data = data
        self.df_team1 = df_team1
        self.df_team2 = df_team2
        self.team1_c = team1_c
        self.team2_c = team2_c
        self.team1_edge_c = team1_edge_c
        self.team2_edge_c = team2_edge_c
        
        
        
    
    def draw(self, save_figure=False, show_figure=True):
        for i, row in self.data.iterrows():
            self.pitch.annotate(str(row['time']) + " - " + row["player.name"], (row['playerCoordinates.x'] + 2, row['playerCoordinates.y'] + 2), color="#000000",
                        fontsize=12, ax=self.ax)
        sc = self.pitch.scatter(self.data["playerCoordinates.x"], self.data["playerCoordinates.y"],
                        # size varies between 100 and 1000 (points squared)
                        s=(self.data["xg"] * 1000) + 100,
                        c='#b94b75',  # color for scatter in hex format
                        edgecolors='#383838',  # give the markers a charcoal border
                        # for other markers types see: https://matplotlib.org/api/markers_api.html
                        marker='h',
                        ax=self.ax)
        txt = self.ax.text(x=40, y=80, s='Raja shots\nversus MAT',
                    size=30,
                    # here i am using a downloaded font from google fonts instead of passing a fontdict
                    fontproperties=fm_rubik.prop, color=self.pitch.line_color,
                    va='center', ha='center')
        if save_figure:
            plt.savefig('./shots.png', dpi=300, bbox_inches='tight', transparent=True)
        if show_figure:
            plt.show()

    def draw_v2(self, save_figure=False, show_figure=True):
        if self.df_team1 is not None and not self.df_team1.empty:
            for i, row in self.df_team1.iterrows():
                marker_color = self.team1_c if row['shotType'] == 'goal' else (0, 0, 0, 0)
                edge_colors = self.team1_edge_c if row['shotType'] == 'goal' else self.team1_c

                self.pitch.scatter(row["PlayerCoordinatesX"], row["PlayerCoordinatesY"],
                                s=(1000 * row["xg"]) , #row["xg"]
                                c=marker_color, 
                                edgecolors=edge_colors,
                                ax=self.ax)
        if self.df_team2 is not None and not self.df_team2.empty:
            for i, row in self.df_team2.iterrows():
                marker_color = self.team2_c if row['shotType'] == 'goal' else (0, 0, 0, 0)
                edge_colors = self.team2_edge_c if row['shotType'] == 'goal' else self.team2_c

                self.pitch.scatter(row["PlayerCoordinatesX"], row["PlayerCoordinatesY"],
                                    s=(1000 * row["xg"]) ,#row["xg"]
                                    c=marker_color,
                                    edgecolors=edge_colors,
                                    ax=self.ax)
        if save_figure:
            current_datetime = datetime.now()
            formatted_datetime = current_datetime.strftime("%d-%m-%y_%H-%M-%S")
            plt.savefig(f'./images/shootmap/shots_{str(formatted_datetime)}.png', dpi=300, bbox_inches='tight', transparent=True)
        if show_figure:
            plt.show()
        return self.fig, self.ax
    
    def draw_v3(self, save_figure=False, show_figure=True):
        if self.df_team1 is not None and not self.df_team1.empty:
            
            for i, row in self.df_team1.iterrows():
                marker_color = (
                                    self.team1_c if row['shotType'] == 'goal' and row['GoalType'] != 'penalty'
                                    else self.team1_c if row['shotType'] == 'goal' and row['GoalType'] == 'penalty'
                                    else (0, 0, 0, 0)
                                )
                edge_colors = (
                                    self.team1_edge_c if row['shotType'] == 'goal' and row['GoalType'] != 'penalty'
                                    else self.team1_edge_c if row['shotType'] == 'goal' and row['GoalType'] == 'penalty'
                                    else self.team1_c
                                )
                marker = (
                           'o' if row['shotType'] == 'goal' and row['GoalType'] != 'penalty'
                                    else 'o' if row['shotType'] == 'goal' and row['GoalType'] == 'penalty'
                                    else 'o'
                                )

                self.pitch.scatter(row["PlayerCoordinatesX"], row["PlayerCoordinatesY"],
                                s=300*(row["xg"]) ,
                                c=marker_color, 
                                edgecolors=edge_colors,
                                marker=marker,
                                zorder=(2 if row['shotType'] == 'goal' else 1),
                                ax=self.ax)
                # self.pitch.lines(row.DrawStartY, row.DrawStartX,
                #     row.DrawEndY, row.DrawEndX, comet=True,
                #     label='shot', 
                #     color=(self.team1_c if row['shotType'] == 'goal' else self.team1_c), 
                #     ax=self.ax,
                #     lw=0.2,
                #     zorder=(2 if row['shotType'] == 'goal' else 1)
                #     )
            
            # line = self.pitch.lines(self.df_team1.DrawStartY, self.df_team1.DrawStartX,
            #         self.df_team1.DrawEndY, self.df_team1.DrawEndX, comet=True,
            #         label='shot', color='#dce8e0', ax=self.ax, lw=1)
        if self.df_team2 is not None and not self.df_team2.empty:
            for i, row in self.df_team2.iterrows():
                marker_color = self.team2_c if row['shotType'] == 'goal' else (0, 0, 0, 0)
                edge_colors = self.team2_edge_c if row['shotType'] == 'goal' else self.team2_c

                self.pitch.scatter(row["PlayerCoordinatesX"], row["PlayerCoordinatesY"],
                                    s=(row["xg"] * 700) ,
                                    c=marker_color,
                                    edgecolors=edge_colors,
                                    ax=self.ax)
        
        if save_figure:
            current_datetime = datetime.now()
            formatted_datetime = current_datetime.strftime("%d-%m-%y_%H-%M-%S")
            plt.savefig(f'./images/shootmap/shots_{str(formatted_datetime)}.png', dpi=300, bbox_inches='tight', transparent=True)
        if show_figure:
            plt.show()
        return self.fig, self.ax


    def process_fotmob_data(self, data):
        """Process FotMob JSON data format directly without using ShootmapProcessor"""
        df = pd.json_normalize(data['shotmap'])
        
        # Map FotMob data to expected format
        df_processed = pd.DataFrame()
        
        # Map coordinates (FotMob uses percentage coordinates)
        df_processed["PlayerCoordinatesX"] = df["x"]
        df_processed["PlayerCoordinatesY"] = df["y"]
        df_processed["onGoalShotX"] = df["onGoalShot.x"]
        df_processed["onGoalShotY"] = df["onGoalShot.y"]
        df_processed["PlayerCoordinatesX"] = df_processed["PlayerCoordinatesX"] - 6
        df_processed["PlayerCoordinatesY"] = df_processed["PlayerCoordinatesY"] + 16

        
        # Map shot outcome to shotType
        def map_event_type(event_type):
            if event_type == "Goal":
                return "goal"
            elif event_type in ["AttemptSaved", "Miss", "AttemptBlocked"]:
                return "save"  # Non-goal attempts
            else:
                return "save"
        
        df_processed["shotType"] = df["eventType"].apply(map_event_type)
        
        # Use expectedGoals as xg
        df_processed["xg"] = df["expectedGoals"]
        
        # Create team indicator based on teamId (assuming all shots are from same team)
        df_processed["isHome"] = True  # Since this is a player shootmap, treat as home team
        
        # Map other fields
        df_processed["time"] = df["min"]
        df_processed["GoalType"] = df.get("situation", "RegularPlay")
        df_processed["playerName"] = df["playerName"]
        
        # Create draw coordinates for shot lines (from shot position to goal)
        df_processed["DrawStartX"] = df_processed["PlayerCoordinatesX"] 
        df_processed["DrawStartY"] = df_processed["PlayerCoordinatesY"]
        df_processed["DrawEndX"] = df_processed["DrawStartX"]*df_processed["onGoalShotX"]
        df_processed["DrawEndY"] = df_processed["DrawStartY"]*df_processed["onGoalShotY"]


        
        return df_processed

if __name__ == "__main__":
    
    # Start generating shotmap for match using FotMob data format
    json_tool = JsonTool(path="./data/fotmob_data/diaz_afcon_shotmap.json")
    data = json_tool.get_data()
    
    # Create ShootMap instance to use the processing method
    shootmap_instance = ShootMap(pitch=Pitch)
    df_processed = shootmap_instance.process_fotmob_data(data)
    
    # Since this is player data, we'll treat it as team1 and flip coordinates for display
    df_team1 = df_processed.copy()
    
    # Flip Y coordinates for correct display orientation
    df_team1["PlayerCoordinatesY"] = 100 - df_team1["PlayerCoordinatesY"]
    df_team1["DrawStartY"] = 100 - df_team1["DrawStartY"] 
    df_team1["DrawEndY"] = 100 - df_team1["DrawEndY"]
    
    # Create the shootmap visualization
    pitch = ShootMap(
        df_team1=df_team1,
        df_team2=None,
        pitch=Pitch,
        team1_c="#D80505",
        team2_c="#F9FD00",
    )
    fig, ax = pitch.draw_v3(save_figure=True, show_figure=True)
    