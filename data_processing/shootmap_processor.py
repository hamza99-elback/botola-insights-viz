import pandas as pd
import logging

axis_width = 100
axis_height = 100
class ShootmapProcessor:
    def __init__(self, data, reverse: bool = False, isHome: bool = None):
        self.data = data
        self.reverse = reverse
        self.isHome = isHome
        self.columns_to_keep = [
            "isHome",
            "xgot",
            "goalType",
            "xg",
            "time",
            "shotType",
            "goalMouthLocation",
            "bodyPart",
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
        if isinstance(self.data, list):
            df = pd.json_normalize(self.data)
            # df.rename(columns={
            #     "playerCoordinates.x": "PlayerCoordinatesX",
            #     "playerCoordinates.y": "PlayerCoordinatesY",
            #     "playerCoordinates.z": "PlayerCoordinatesZ",
            #     "goalMouthCoordinates.x": "GoalMouthCoordinatesX",
            #     "goalMouthCoordinates.y": "GoalMouthCoordinatesY",
            #     "goalMouthCoordinates.z": "GoalMouthCoordinatesZ",
            #         }, inplace=True)
        else:
            df = self.data
        
        df["isHome"] = df["isHome"].replace({'True': True, 'False': False}) # Convert isHome to boolean
            
        if self.isHome:
            df = df[df["isHome"] == self.isHome]
        df.loc[df["time"] <= 45, "Half"] = "First"
        df.loc[df["time"] > 45, "Half"] = "Second"

        df.rename(columns={
                "draw.start.x": "DrawStartX",
                "draw.start.y": "DrawStartY",
                "draw.end.x": "DrawEndX",
                "draw.end.y": "DrawEndY",
                "goalType": "GoalType",
                "playerCoordinates.x": "PlayerCoordinatesX",
                "playerCoordinates.y": "PlayerCoordinatesY",
                "playerCoordinates.z": "PlayerCoordinatesZ",
                "goalMouthCoordinates.x": "GoalMouthCoordinatesX",
                "goalMouthCoordinates.y": "GoalMouthCoordinatesY",
                "goalMouthCoordinates.z": "GoalMouthCoordinatesZ",
                    }, inplace=True)
        df["xg"] = 1
        print("df columns: ", df.columns)
        df_team1 = df[df["isHome"] == True]
        df_team2 = df[df["isHome"] == False]
        logging.info(f"before edit: {df_team2['PlayerCoordinatesX']}")
        df_team2["PlayerCoordinatesX"] = axis_width - df_team2["PlayerCoordinatesX"]
        df_team1["PlayerCoordinatesY"] = axis_height - df_team1["PlayerCoordinatesY"]
        logging.info(f"after edit: {df_team2['PlayerCoordinatesX']}")
        return (df_team1, df_team2)


    def process_data_mono(self):
        self.data.rename(columns={
            "playerCoordinates.x": "PlayerCoordinatesX",
            "playerCoordinates.y": "PlayerCoordinatesY",
            "playerCoordinates.z": "PlayerCoordinatesZ",
            "goalMouthCoordinates.x": "GoalMouthCoordinatesX",
            "goalMouthCoordinates.y": "GoalMouthCoordinatesY",
            "goalMouthCoordinates.z": "GoalMouthCoordinatesZ",
            "draw.start.x": "DrawStartX",
            "draw.start.y": "DrawStartY",
            "draw.end.x": "DrawEndX",
            "draw.end.y": "DrawEndY",
            "goalType": "GoalType"
                }, inplace=True)
        self.data["xg"] = 0.8
        self.data["isHome"] = self.data["isHome"].replace({'True': True, 'False': False})
        # self.data.loc[self.data["isHome"] == False,"PlayerCoordinatesX"] = axis_width - self.data["PlayerCoordinatesX"]
        # self.data.loc[self.data["isHome"] == False,"PlayerCoordinatesY"] = axis_height - self.data["PlayerCoordinatesY"]
        # self.data.loc[self.data["isHome"] == False,"DrawStartX"] = axis_height - self.data["DrawStartX"]
        # self.data.loc[self.data["isHome"] == False,"DrawEndX"] = axis_height - self.data["DrawEndX"]
        return self.data