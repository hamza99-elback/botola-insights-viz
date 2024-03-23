from tools.json_tool import JsonTool
from charts.shootmap import ShootMap
from charts.heatmap import Heatmap
from data_processing.shootmap_processor import ShootmapProcessor
from mplsoccer import (
    VerticalPitch,
    Pitch,
    create_transparent_cmap,
    FontManager,
    arrowhead_marker,
    Sbopen,
)




if __name__=="__main__":
    # json_tool = JsonTool(path="./data/shootmap_data.json")
    # data = json_tool.get_data()
    # shootmap_processor = ShootmapProcessor(data=data)
    # df_team1, df_team2 = shootmap_processor.process_data()
    # pitch = ShootMap(df_team1=df_team1, df_team2=df_team2, pitch=Pitch, team1_c="", team2_c="")
    # pitch.draw_shootmap_v2(save_figure=True)
    # print(data)
    json_tool = JsonTool(path="./data/heatmap_data.json")
    data = json_tool.get_data()
    pitch = Heatmap(data=data, pitch=VerticalPitch)
    pitch.draw_heatmap(save_figure=True)
    print(data)