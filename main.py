from tools.json_tool import JsonTool
from charts.shootmap import ShootMap
from charts.heatmap import Heatmap
from charts.stackedbarchart import StackedBarChart
from data_processing.shootmap_processor import ShootmapProcessor
from mplsoccer import (
    VerticalPitch,
    Pitch,
    create_transparent_cmap,
    FontManager,
    arrowhead_marker,
    Sbopen,
)
import logging
import argparse
import datetime


now = datetime.datetime.now()
now_str = now.strftime("%Y-%m-%d_%H-%M-%S")
filename = f'logs/app_{now_str}.log'
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename=filename, filemode='w')

def main():
    parser = argparse.ArgumentParser(description="Plot Charts")
    parser.add_argument("-ch", "--chart", type=str, help="Chart Type")
    parser.add_argument("-f", "--filter", type=str, help="Data Filter", default=None)
    
    args = parser.parse_args()

    if args.chart=="heatmap":
        logging.info("Heatmap")
        if args.filter:
            # TODO: here we can extract data based on the filter we pass to the args
            print("Filter:", args.filter) 
        json_tool = JsonTool(path="./data/heatmap_data.json")
        data = json_tool.get_data()
        pitch = Heatmap(data=data, pitch=VerticalPitch)
        pitch.draw(save_figure=False)
    elif args.chart=="shootmap":
        logging.info("Shootmap")
        if args.filter:
            # TODO: here we can extract data based on the filter we pass to the args
            print("Filter:", args.filter) 
        json_tool = JsonTool(path="./data/shootmap_data.json")
        data = json_tool.get_data()
        shootmap_processor = ShootmapProcessor(data=data)
        df_team1, df_team2 = shootmap_processor.process_data()
        pitch = ShootMap(df_team1=df_team1, df_team2=df_team2, pitch=Pitch)
        pitch.draw_v2(save_figure=False)
    elif args.chart=="pizzachart":
        logging.info("Pizza Chart")
        pass
    elif args.chart=="radarchart":
        logging.info("Radar Chart")
        pass
    elif args.chart=="stackedbarchart":
        logging.info("Stacked Bar Chart")
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
        stackedbarchart.draw(show_figure=True, save_figure=False)
    else:
        logging.info(f"No chart with the name {args.chart}")
    


if __name__=="__main__":
    main()