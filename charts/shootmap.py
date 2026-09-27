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

# fm_rubik = FontManager('https://raw.githubusercontent.com/google/fonts/main/ofl/'
#                        'rubikmonoone/RubikMonoOne-Regular.ttf')
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
                    # fontproperties=fm_rubik.prop, 
                    color=self.pitch.line_color,
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
                                s=250 ,
                                c=marker_color, 
                                edgecolors=edge_colors,
                                marker=marker,
                                zorder=(2 if row['shotType'] == 'goal' else 1),
                                ax=self.ax)
                self.pitch.lines(row.DrawStartY, row.DrawStartX,
                    row.DrawEndY, row.DrawEndX, comet=True,
                    label='shot', 
                    color=(self.team1_c if row['shotType'] == 'goal' else self.team1_c), 
                    ax=self.ax,
                    lw=0.2,
                    zorder=(2 if row['shotType'] == 'goal' else 1)
                    )
            
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


if __name__ == "__main__":
    
    # Start generating shotmap for match
    json_tool = JsonTool(path="./data/far_jsk.json")
    data = json_tool.get_data()
    df_shootmap = pd.DataFrame(data['shotmap'])
    # df_shootmap = pd.read_excel("./data/wac_codm.xlsx")
    # df_shootmap=df_shootmap.dropna(subset=['xg'])
    shootmap_processor = ShootmapProcessor(data=data['shotmap'])

    # shootmap_processor = ShootmapProcessor(data=df_shootmap)
    df_team1, df_team2 = shootmap_processor.process_data()
    df_team1["xg"] = 1
    df_team2["xg"] = 1

    df_team1.rename(columns={
                "draw.start.x": "DrawStartX",
                "draw.start.y": "DrawStartY",
                "draw.end.x": "DrawEndX",
                "draw.end.y": "DrawEndY",
                "goalType": "GoalType"
                    }, inplace=True)
    df_team2.rename(columns={
                "draw.start.x": "DrawStartX",
                "draw.start.y": "DrawStartY",
                "draw.end.x": "DrawEndX",
                "draw.end.y": "DrawEndY",
                "goalType": "GoalType"
                    }, inplace=True)
    df_team2["PlayerCoordinatesX"] =  100 - df_team2["PlayerCoordinatesX"]
    # df_team2["PlayerCoordinatesY"] = 100 - df_team2["PlayerCoordinatesY"]

    df_team2["DrawStartX"] = 100 - df_team2["DrawStartX"]
    df_team2["DrawEndX"] = 100 - df_team2["DrawEndX"]
    # df_team1.rename(columns={
    #             "draw.start.x": "DrawStartX",
    #             "draw.start.y": "DrawStartY",
    #             "draw.end.x": "DrawEndX",
    #             "draw.end.y": "DrawEndY",
    #             "goalType": "GoalType"
    #                 }, inplace=True)
    # df_team1["PlayerCoordinatesX"] =  100 - df_team1["PlayerCoordinatesX"]
    df_team1["PlayerCoordinatesY"] = 100 - df_team1["PlayerCoordinatesY"]
    df_team1["DrawStartX"] = 100 - df_team1["DrawStartX"]
    df_team1["DrawEndX"] = 100 - df_team1["DrawEndX"]
    # df_team1 = df_team1[df_team1["shotType"] == "save"]
    pitch = ShootMap(
        df_team1=df_team1,
        df_team2=None,
        pitch=Pitch,
        team1_c="#FF1717",
        team2_c="#F9FD00",
    )
    fig, ax = pitch.draw_v3(save_figure=True, show_figure=True)
    # End generating shotmap for match

    # startccustom shotmap
    # json_tool = JsonTool(path="./data/mar_niger.json")
    # data1 = json_tool.get_data()
    # df_shootmap1 = pd.DataFrame(data1['shotmap'])
    # json_tool = JsonTool(path="./data/mar_tanz.json")
    # data2 = json_tool.get_data()
    # df_shootmap2 = pd.DataFrame(data2['shotmap'])
    # shootmap_processor1 = ShootmapProcessor(data=data1['shotmap'])
    # shootmap_processor2 = ShootmapProcessor(data=data2['shotmap'])
    # df_team11, df_team21 = shootmap_processor1.process_data()
    # df_team12, df_team22 = shootmap_processor2.process_data()
    # df_team21["PlayerCoordinatesX"] = 100 - df_team21["PlayerCoordinatesX"]
    # df_team21["PlayerCoordinatesY"] = 100 - df_team21["PlayerCoordinatesY"]
    # df_merged = pd.concat([df_team21, df_team12], ignore_index=True)
    # df_merged["xg"] = 0.5
    # # df_merged.rename(columns={
    # #             "XG": "xg",
    # #             "ShotType": "shotType",
    # #                 }, inplace=True)
    # pitch = ShootMap(
    #     df_team1=df_merged,
    #     df_team2=None,
    #     pitch=Pitch,
    #     team1_c="#EE272B",
    #     team2_c="#81ACDB",
    # )
    # fig, ax = pitch.draw_v2(save_figure=True, show_figure=True)
    # end custom shotmap

    # # start genereting custom shotmap
    # df_shootmap = pd.read_excel("./data/goal_location/young_vs_far.xlsx")
    # # TODO: rename columns XG, ShotType ...
    # df_shootmap.rename(columns={
    #             "XG": "xg",
    #             "ShotType": "shotType",
    #                 }, inplace=True)
    # df_shootmap=df_shootmap.dropna(subset=['xg'])
    # # df_shootmap["PlayerCoordinatesX"] = 100 - df_shootmap["PlayerCoordinatesX"]
    # df_shootmap["PlayerCoordinatesY"] = 100 - df_shootmap["PlayerCoordinatesY"]
    # df_shootmap["DrawStartX"] = 100 - df_shootmap["DrawStartX"]
    # df_shootmap["DrawEndX"] = 100 - df_shootmap["DrawEndX"]


    # pitch = ShootMap(
    # df_team1=df_shootmap,
    # df_team2=None,
    # pitch=Pitch,
    # team1_c="#27C7F2",
    # team2_c="#81ACDB",
    # )
    # fig, ax = pitch.draw_v3(save_figure=True, show_figure=True)
    # # End genereting custom shotmap


