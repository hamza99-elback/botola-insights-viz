# from tools.json_tool import JsonTool
# from charts.shootmap import ShootMap
# from charts.heatmap import Heatmap
# from charts.stackedbarchart import StackedBarChart
# from data_processing.shootmap_processor import ShootmapProcessor
# from mplsoccer import (
#     VerticalPitch,
#     Pitch,
#     create_transparent_cmap,
#     FontManager,
#     arrowhead_marker,
#     Sbopen,
# )
# import logging
# import argparse
# import datetime


# now = datetime.datetime.now()
# now_str = now.strftime("%Y-%m-%d_%H-%M-%S")
# filename = f'logs/app_{now_str}.log'
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename=filename, filemode='w')

# def main():
#     parser = argparse.ArgumentParser(description="Plot Charts")
#     parser.add_argument("-ch", "--chart", type=str, help="Chart Type")
#     parser.add_argument("-f", "--filter", type=str, help="Data Filter", default=None)
    
#     args = parser.parse_args()

#     if args.chart=="heatmap":
#         logging.info("Heatmap")
#         if args.filter:
#             # TODO: here we can extract data based on the filter we pass to the args
#             print("Filter:", args.filter) 
#         json_tool = JsonTool(path="./data/heatmap_data.json")
#         data = json_tool.get_data()
#         pitch = Heatmap(data=data, pitch=VerticalPitch)
#         pitch.draw(save_figure=False)
#     elif args.chart=="shootmap":
#         logging.info("Shootmap")
#         if args.filter:
#             # TODO: here we can extract data based on the filter we pass to the args
#             print("Filter:", args.filter) 
#         json_tool = JsonTool(path="./data/shootmap_data.json")
#         data = json_tool.get_data()
#         shootmap_processor = ShootmapProcessor(data=data)
#         df_team1, df_team2 = shootmap_processor.process_data()
#         pitch = ShootMap(df_team1=df_team1, df_team2=df_team2, pitch=Pitch)
#         pitch.draw_v2(save_figure=False)
#     elif args.chart=="pizzachart":
#         logging.info("Pizza Chart")
#         pass
#     elif args.chart=="radarchart":
#         logging.info("Radar Chart")
#         pass
#     elif args.chart=="stackedbarchart":
#         logging.info("Stacked Bar Chart")
#         data = {
#         "home": [1.42, 50, 16, 7, 7, 2],
#         "away": [1.86, 50, 17, 6, 5, 5],
#         "itemName": [
#             "Expected goals",
#             "Ball possession",
#             "Total shots",
#             "Shots on target",
#             "Shots off target",
#             "Blocked shots",
#         ],
#     }

#         # Calculate proportions for the last column
#         home_values = data["home"]
#         away_values = data["away"]
#         total_values = [home + away for home, away in zip(home_values, away_values)]
#         proportions = [(home, away) for home, away in zip(home_values, away_values)]
#         stackedbarchart = StackedBarChart(
#             data=data, total_values=total_values, proportions=proportions
#         )
#         stackedbarchart.draw(show_figure=True, save_figure=False)
#     else:
#         logging.info(f"No chart with the name {args.chart}")
    
def generator():
    for i in range(10):
        yield i


def file_generator(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            yield line.strip()


def main():
    gen = generator()
    for value in gen:
        print(value)

def process_line(line):
    # Process the line (e.g., print it, store it, etc.)
    print(line)

    file_gen = file_generator('data/sample.txt')
    for line in file_gen:
        process_line(line)


if __name__=="__main__":
    # main()
    import pandas as pd
    import json
    with open("data/hadraf_passes.json", "r") as f:
        data = json.load(f)
    
    df_passes = pd.json_normalize(data["passes"])
    df_passes.rename(columns={
        "playerCoordinates.x": "playerCoordinatesStartX",
        "playerCoordinates.y": "playerCoordinatesStartY",
        "passEndCoordinates.x": "playerCoordinatesEndX",
        "passEndCoordinates.y": "playerCoordinatesEndY",
    }, inplace=True)
    df_passes.to_excel("./data/hadraf_passes.xlsx", index=False)
    # df_24_25 = pd.read_excel("./data/botola_comparison.xlsx", sheet_name="24_25", usecols=["Club", "PtsPoints"])
    # df_23_24 = pd.read_excel("./data/botola_comparison.xlsx", sheet_name="23_24", usecols=["Club", "PtsPoints"])
    # df_24_25.dropna(inplace=True)
    # df_23_24.dropna(inplace=True)

    # df = df_24_25.merge(df_23_24, how="left", on="Club")
    # df["Difference"] = df["PtsPoints_x"] - df["PtsPoints_y"]
    # df["DifferencePerc"] = (df["PtsPoints_x"]/df["PtsPoints_y"])*100-100
    # df = df.sort_values("Difference", ascending=False)
    # df = df.reset_index(drop=True)
    # df["Rank"] = df.index + 1
    # df.to_excel("./data/result_botola_comparison.xlsx", sheet_name="Ranking", index=False)

    # data\hadraf_passes.json
    
