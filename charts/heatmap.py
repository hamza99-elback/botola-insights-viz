from matplotlib.colors import LinearSegmentedColormap
from tools.json_tool import JsonTool
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

fm_rubik = FontManager('https://raw.githubusercontent.com/google/fonts/main/ofl/'
                       'rubikmonoone/RubikMonoOne-Regular.ttf')

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
        figsize=(12, 10),
        pitch_color='#F7F7F7'
    ):
        self.pitch = pitch(
            pad_bottom=pad_bottom,
            half=half,
            goal_type=goal_type,
            goal_alpha=goal_alpha,
            # pitch_type=pitch_type,
        )
        self.pitch_color = pitch_color
        self.fig, self.ax = self.pitch.draw(figsize=figsize)
        self.data = pd.DataFrame(data["heatmap"])
        
    def draw(self, save_figure:bool=False, show_figure:bool=True):
        pearl_earring_cmap_100 = LinearSegmentedColormap.from_list("Pearl Earring - 100 colors", ['#F7F7F7', '#C384FF','#00FFD4', '#FBFF00', '#FE5202'], N=80)
        pitch = VerticalPitch(line_color='#7E7E7E', line_zorder=2, pitch_color=self.pitch_color, pad_bottom=0, pad_left=0, pad_right=0, pad_top=0)
        kdeplot = pitch.kdeplot(self.data.x, self.data.y, ax=self.ax, cmap=pearl_earring_cmap_100, fill=True, levels=100, zorder=-1)
        if show_figure:
            plt.show()
        if save_figure:
            current_datetime = datetime.now()
            formatted_datetime = current_datetime.strftime("%d-%m-%y_%H-%M-%S")
            plt.savefig(f'./images/heatmap/heatmap_{str(formatted_datetime)}.png', dpi=300, bbox_inches='tight', transparent=True)
            
if __name__=="__main__":
    json_tool = JsonTool(path="./data/heatmap_data.json")
    data = json_tool.get_data()
    pitch = Heatmap(data=data, pitch=VerticalPitch)
    pitch.draw(save_figure=True)
    print(data)