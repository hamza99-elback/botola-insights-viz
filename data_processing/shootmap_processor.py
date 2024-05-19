import pandas as pd
import logging

class ShootmapProcessor:
    def __init__(self, data, reverse: bool = False, isHome: bool = None):
        self.data = data
        self.reverse = reverse
        self.isHome = isHome
        self.columns_to_keep = [
            "PlayerId",
            "matcheId",
            "matchName",
            "isHome",
            "xgot",
            "goalType",
            "xg",
            "time",
            "shotType",
            "reversedPeriodTime",
            "DrawId",
            "goalMouthLocation",
            "bodyPart",
            "DatumAddedTime",
            "BlockCoordinatesZ",
            "BlockCoordinatesY",
            "BlockCoordinatesX",
            "PlayerCoordinatesZ",
            "PlayerCoordinatesY",
            "PlayerCoordinatesX",
            "addedTime",
            "GoalMouthCoordinatesZ",
            "GoalMouthCoordinatesX",
            "GoalMouthCoordinatesY",
        ]

    def process_data(self):
        # Convert the dictionary to a DataFrame
        # df = pd.json_normalize(self.data["shotmap"])
        # Display the DataFrame
        df = self.data
        if self.isHome:
            df = df[df["isHome"] == self.isHome]
        df.loc[df["time"] <= 45, "Half"] = "First"
        df.loc[df["time"] > 45, "Half"] = "Second"
        axis_width = 100
        axis_height = 100
        df_team1 = df[df["isHome"] == True]
        df_team2 = df[df["isHome"] == False]
        logging.info(f"before edit: {df_team2['PlayerCoordinatesX']}")
        df_team2["PlayerCoordinatesX"] = axis_width - df_team2["PlayerCoordinatesX"]
        df_team2["PlayerCoordinatesY"] = axis_height - df_team2["PlayerCoordinatesY"]
        logging.info(f"after edit: {df_team2['PlayerCoordinatesX']}")
        return (df_team1, df_team2)
