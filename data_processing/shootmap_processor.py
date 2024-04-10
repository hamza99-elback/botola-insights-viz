import pandas as pd


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
            "EndY",
            "EndX",
            "xgot",
            "goalType",
            "xg",
            "timeSeconds",
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
            "StartY",
            "StartX",
            "PlayerCoordinatesZ",
            "PlayerCoordinatesY",
            "PlayerCoordinatesX",
            "BlockY",
            "addedTime",
            "GoalMouthCoordinatesZ",
            "GoalMouthCoordinatesX",
            "GoalMouthCoordinatesY",
            "BlockX",
        ]

    def process_data(self):
        # Convert the dictionary to a DataFrame
        # df = pd.json_normalize(self.data["shotmap"])
        # TODO: analyze the goalMouthCoordinates information
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
        df_team2["PlayerCoordinatesX"] = axis_width - df_team2["PlayerCoordinatesX"]
        df_team2["PlayerCoordinatesY"] = axis_height - df_team2["PlayerCoordinatesY"]

        if self.reverse:
            # Reverse the direction of points on the left side to the right side
            left_points = df[
                df["Half"].isin(["First"])
            ]  # Select points on the left side
            left_points["playerCoordinates.x"] = (
                axis_width - left_points["playerCoordinates.x"]
            )  # Reverse x coordinate
            left_points["playerCoordinates.y"] = (
                axis_height - left_points["playerCoordinates.y"]
            )  # Reverse y coordinate
            # Update the dataframe with the new coordinates
            df.update(left_points)
        return (df_team1, df_team2)
