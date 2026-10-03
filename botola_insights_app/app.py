import os
import sys
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import datetime
import io
import json
import logging
import random

import pandas as pd
import streamlit as st
from mplsoccer import Pitch, VerticalPitch
from PIL import Image

from charts.heatmap import Heatmap
from charts.pizzachart import Pizzachart
from charts.radarchart import Radarchart
from charts.shootmap import ShootMap
from charts.shot_goal_location import ShotGoalLocation
from charts.stackedbarchart import StackedBarChart
from data_processing.shootmap_processor import ShootmapProcessor

# TODO: add Season Filter in all the queries
# TODO: Isolate all queries results in a separate file
try:
    # Make connection with Azure Database
    CONN = ""
except Exception as e:
    print("Error in establishing connection with Azure Database:", str(e))


try:
    now = datetime.datetime.now()
    now_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"./../logs/app_{now_str}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filename=filename,
        filemode="w",
    )
except Exception as e:
    print("error in configuring logging")

random.seed(42)


# Add parent directory to Python path
def save_fig(fig, file_name, key: str):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight", transparent=True)
    buf.seek(0)
    st.download_button("Download", buf, file_name=file_name, mime="image/png", key=key)


def no_data_message(message: str):
    st.markdown(
        f"<h3 style='text-align: center; color: gray;margin-top: 10px'>{message}</h3>",
        unsafe_allow_html=True,
    )


def team_selectbox(team_list, uuid):
    return st.selectbox("Shoose a Team", team_list, key=f"team_{uuid}")


def player_selectbox(player_list, uuid):
    return st.selectbox("Shoose a Player", player_list, key=f"player_{uuid}")


def kpis_multiselect(kpis_list, uuid):
    return st.multiselect("Select KPIs", kpis_list, key=f"kpis_{uuid}")


def get_all_teams_list(cursor):
    # TODO: get teams by season: ADD SEASON FILTER
    query_get_teams = """SELECT [teamId]
                ,[apiTeamId]
                ,[teamName]
                ,[teamSlug]
                ,[teamShortName]
            FROM [dim].[AxeTeam]"""
    teams = get_query_result(query_get_teams, cursor)
    # get Team names
    team_names = [team[2] for team in teams]
    return team_names


def get_seasons_list(cursor) -> tuple:
    """Get all seasons list from the database"""
    query_get_seasons = """SELECT [seasonYear]
    FROM [dim].[AxeTournamentSeason]
    WHERE [seasonName] LIKE '%Botola%'"""
    seasons = ""
    seasons_names = tuple([season[0] for season in seasons])
    return seasons_names


def get_seasons_list_by_competition(cursor, competition) -> tuple:
    """Get all seasons list from the database"""
    query_get_seasons = f"""SELECT DISTINCT seasonYear
            FROM [dim].[AxeTournamentSeason]
            where name='{competition}'"""
    seasons = ""
    seasons_names = tuple([season[0] for season in seasons])
    return seasons_names


def get_all_players_list(cursor):
    query_get_players = f"""
                SELECT DISTINCT [teamName]
                ,[playerName]
                ,p.[position]
            FROM [dim].[FactPlayerMatcheStats] ps JOIN [dim].[AxeTeam] t  ON ps.TeamId = t.TeamId
			JOIN [dim].[AxePlayer] p ON ps.PlayerId=p.playerId;"""
    players = ""
    # get Team names
    player_names = [
        {"player_name": player[1], "position": player[2], "team_name": player[0]}
        for player in players
    ]
    return player_names


def get_players_list(team_name: str, position: str = None):
    if position:
        player_list = [
            player["player_name"]
            for player in PLAYERS_LIST
            if player["team_name"] == team_name and player["position"] == position
        ]
    else:
        player_list = [
            player["player_name"]
            for player in PLAYERS_LIST
            if player["team_name"] == team_name
        ]
    return player_list


def get_teams_by_season(season: str):
    pass


def get_matches_list(team: str, season: str) -> list:
    """Get Matches list by team and season

    Args:
        team (str): _description_
        season (str): _description_

    Returns:
        list: _description_
    """
    matches_list = [
        match["match_name"]
        for match in MATCHES_LIST
        if team in (match["home_team"], match["away_team"])
        # and match["season"] == season
    ]
    return matches_list


# Get Teams list
cursor = ""
TEAMS_LIST = ""
PLAYERS_LIST = ""
SEASONS_LIST = ""
MATCHES_LIST = ""
COMPETITIONS_LIST = ""


def shootmap_visualisations():
    """Function to display the shootmap visualisations in the Streamlit app"""
    col1, col2 = st.columns(2)
    data = []
    season_names = SEASONS_LIST
    with col1:
        home_c = st.color_picker("Home Color", "#00f900")
    with col2:
        away_c = st.color_picker("Away Color", "#F90004")

    uploaded_file = st.file_uploader("Choose a file", key="shootmap_fileuploader")
    json_text = st.text_area(
        "Paste the shootmap here (json format)", key="shootmap_textarea"
    )
    if uploaded_file is not None:

        # Can be used wherever a "file-like" object is accepted:
        data = json.loads(uploaded_file.read())
    elif json_text:
        data = json.loads(json_text)
    else:
        data = ""
    df_shootmap = (
        pd.DataFrame(data=data["shotmap"]) if "shotmap" in data else pd.DataFrame()
    )
    print("df_shootmap columns: ", df_shootmap.head())
    if df_shootmap.empty:
        no_data_message(message="No data available for this match")
        return

    # Here we can prepare the data for the shootmap
    shootmap_processor = ShootmapProcessor(data=data["shotmap"])
    logging.info("Processing data")
    df_team1, df_team2 = shootmap_processor.process_data()
    pitch = ShootMap(
        df_team1=df_team1,
        df_team2=df_team2,
        pitch=Pitch,
        team1_c=home_c,
        team2_c=away_c,
    )
    fig, ax = pitch.draw_v2(save_figure=False, show_figure=False)
    st.pyplot(fig)
    save_fig(fig=fig, file_name="Shootmap.png", key="shootmap")


def pizzachart_visualisations():
    """Function to display the pizzachart visualisations in the Streamlit app"""
    col1, col2, col3 = st.columns(3)

    columns = [col[0] for col in cursor.description]
    team_names = get_all_teams_list(cursor)
    if "uuid_team" not in st.session_state:
        st.session_state.uuid_team = str(
            uuid.uuid4()
        )  # replace this with your uuid generation logic
    if "uuid_player" not in st.session_state:
        st.session_state.uuid_player = str(
            uuid.uuid4()
        )  # replace this with your uuid generation logic
    if "uuid_kpis" not in st.session_state:
        st.session_state.uuid_kpis = str(
            uuid.uuid4()
        )  # replace this with your uuid generation logic

    with col1:
        team_pizza = team_selectbox(team_names, uuid=st.session_state.uuid_team)

    player_names = get_players_list(team_pizza)
    with col2:
        player_pizza = player_selectbox(player_names, uuid=st.session_state.uuid_player)

    with col3:
        kpis_list = kpis_multiselect(columns, uuid=st.session_state.uuid_kpis)

    # player stats
    pizzachart_data = ""
    columns_pizza = [col[0] for col in cursor.description]
    data = [
        {col: val for col, val in zip(columns_pizza, row)} for row in pizzachart_data
    ]
    df_pizzachart = pd.DataFrame(data, columns=columns_pizza).reset_index(drop=True)
    # maximum stats
    max_pizzachart_data = ""
    max_columns_pizza = [col[0] for col in cursor.description]
    max_data = [
        {col: val for col, val in zip(columns_pizza, row)}
        for row in max_pizzachart_data
    ]
    df_max_pizzachart = pd.DataFrame(max_data, columns=max_columns_pizza).reset_index(
        drop=True
    )
    if df_pizzachart.empty:
        no_data_message(message="No data available for this player")
        return
    df_pizzachart = df_pizzachart[kpis_list]
    df_max_pizzachart = df_max_pizzachart[kpis_list]
    categories = list(df_pizzachart.columns)
    group_1 = list(df_pizzachart.values[0])
    min_range = [0] * len(group_1)
    new_list = [x / 4 for x in df_max_pizzachart.max().tolist()]
    max_range = list(df_max_pizzachart.values[0])
    nb_cat = len(categories)
    list_colors = ["#FE4844", "#30E5D0", "#9726E0"]
    slice_colors = list_colors * (nb_cat // 3) + list_colors[: nb_cat % 3]
    slice_colors.sort()
    text_colors = ["#000000"] * (nb_cat)
    if len(categories) < 1:
        no_data_message(message="No data available for this player")
    pizza = Pizzachart(
        categories=categories,
        min_range=min_range,
        max_range=max_range,
        group_1=group_1,
        slice_colors=slice_colors,
        text_colors=text_colors,
    )
    fig, ax = pizza.draw()
    st.pyplot(fig)
    save_fig(fig=fig, file_name="Pizzachart.png", key="pizzachart")


def heatmap_visualisations():
    data = []
    team_list = TEAMS_LIST
    st.subheader("Choose Heatmap Color Palette")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        color1 = st.color_picker(
            "Low Intensity", value="#FFFFFF", help="Color for low values"
        )
    with col2:
        color2 = st.color_picker(
            "Medium Intensity", value="#D33131", help="Color for medium values"
        )
    with col3:
        color3 = st.color_picker(
            "High Intensity", value="#5F0202", help="Color for high values"
        )
    with col4:
        line_color = st.color_picker(
            "Line Color", value="#424242", help="Color for pitch lines"
        )
    uploaded_file = st.file_uploader("Choose a file", key="heatmap_fileuploader")
    json_text = st.text_area(
        "Paste the heatmap here (json format)", key="heatmap_textarea"
    )
    if uploaded_file is not None:

        # Can be used wherever a "file-like" object is accepted:
        data = json.loads(uploaded_file.read())
        # st.button("Use this data", on_click=lambda: st.session_state.update(heatmap_data=dataframe))
    elif json_text:
        data = json.loads(json_text)
    else:
        data = ""
    df_heatmap = (
        pd.DataFrame(data["points"])
        if "points" in data
        else pd.DataFrame(data["heatmap"]) if "heatmap" in data else pd.DataFrame()
    )
    if df_heatmap.empty:
        no_data_message(message="No data available for this player")
        return
    pitch = Heatmap(data=df_heatmap, pitch=VerticalPitch)
    fig, ax = pitch.draw(color_palette=[color1, color2, color3], line_color=line_color)
    st.pyplot(fig)
    save_fig(fig=fig, file_name="Heatmap.png", key="heatmap")


def goal_location_visualisations():
    # TODO: keep just players that are on the shootmap data
    team, match = None, None
    st.subheader("Choose main color")
    # Players shots location
    col1, col2 = st.columns(2)

    with col1:
        home_list = ["Home", "Away"]
        home_value = st.selectbox("Shoose a season", home_list, key="home_value")

    with col2:
        color = st.color_picker("Color", "#00f900")

    uploaded_file = st.file_uploader("Choose a file", key="goallocation_fileuploader")
    json_text = st.text_area(
        "Paste the heatmap here (json format)", key="goallocation_textarea"
    )
    if uploaded_file is not None:
        data = json.loads(uploaded_file.read())
        # st.button("Use this data", on_click=lambda: st.session_state.update(heatmap_data=dataframe))
    elif json_text:
        data = json.loads(json_text)
    else:
        data = ""

    if len(data) == 0:
        no_data_message(message="No data available for this match")
        return

    # Here we can prepare the data for the shootmap
    shootmap_processor = ShootmapProcessor(data=data["shotmap"])
    logging.info("Processing data")
    df_team1, df_team2 = shootmap_processor.process_data()

    columns_to_keep = [
        "GoalMouthCoordinatesY",
        "GoalMouthCoordinatesZ",
        "shotType",
        "xg",
    ]
    if home_value == "Home":
        df_goal_location = df_team1
    else:
        df_goal_location = df_team2
    
    df_goal_location = df_goal_location[df_goal_location["shotType"].isin(["save", "goal"])]
    df_goal_location = df_goal_location[columns_to_keep]
    if df_goal_location.empty:
        no_data_message(message="No data available for this team")
        return

    df_goal_location["GoalMouthCoordinatesY"] = df_goal_location[
        "GoalMouthCoordinatesY"
    ].astype(float)
    df_goal_location["GoalMouthCoordinatesZ"] = df_goal_location[
        "GoalMouthCoordinatesZ"
    ].astype(float)
    df_goal_location["xg"] = df_goal_location["xg"].astype(float)
    df_goal_location["shotType"] = df_goal_location["shotType"].astype(str)

    shot_goal_location = ShotGoalLocation(
        data=df_goal_location.to_records(), color=color, edge_color=color
    )
    fig, ax = shot_goal_location.draw()
    st.pyplot(fig)
    save_fig(fig=fig, file_name="ShotGoalLocation.png", key="goal_location")


def goal_keeper_vizualisations(match, team):
    col1, col2 = st.columns(2)

    with col1:
        players_list = [""]
        print("players_list: ", players_list, match)
        player = st.selectbox(
            "Shoose a Goalkeeper", ["None"] + players_list, key="player_gk"
        )

    with col2:
        color = st.color_picker("Color", "#00f900", key="color_gk")

    columns_to_keep = [
        "GoalMouthCoordinatesY",
        "GoalMouthCoordinatesZ",
        "shotType",
        "xg",
    ]
    player_value = player if player != "None" else None
    shootmap_data = ""
    columns = [col[0] for col in cursor.description]
    data = [{col: val for col, val in zip(columns, row)} for row in shootmap_data]
    df_goal_location = pd.DataFrame(data, columns=columns_to_keep)
    df_goal_location["GoalMouthCoordinatesY"] = df_goal_location[
        "GoalMouthCoordinatesY"
    ].astype(float)
    df_goal_location["GoalMouthCoordinatesZ"] = df_goal_location[
        "GoalMouthCoordinatesZ"
    ].astype(float)
    df_goal_location["xg"] = df_goal_location["xg"].astype(float)
    df_goal_location["shotType"] = df_goal_location["shotType"].astype(str)
    df_goal_location = df_goal_location.loc[
        df_goal_location["shotType"].isin(["save", "goal"])
    ]
    if df_goal_location.empty:
        no_data_message(message="No data available for this match")
        return
    shot_goal_location = ShotGoalLocation(
        data=df_goal_location.to_records(), color=color, player_type="goal_keeper"
    )
    fig, ax = shot_goal_location.draw()
    st.pyplot(fig)
    save_fig(fig=fig, file_name="GoalKeeperShots.png", key="goal_keeper")


def stacked_barchart_vizualisations():
    col1, col2 = st.columns(2)


    with col1:
        col_team1 = st.color_picker("Color", "#00f900", key="col_team1")
        # home values
        home1 = st.text_input("result for home team", key="home1")
        home2 = st.text_input("possession", key="home2")
        home3 = st.text_input("total shots", key="home3")
        home4 = st.text_input("shots on target", key="home4")
        home5 = st.text_input("shots off target", key="home5")
        home6 = st.text_input("blocked shots", key="home6")

    with col2:
        col_team2 = st.color_picker("Color", "#000990", key="col_team2")
        # away values
        away1 = st.text_input("result for away team", key="away1")
        away2 = st.text_input("possession", key="away2")
        away3 = st.text_input("total shots", key="away3")
        away4 = st.text_input("shots on target", key="away4")
        away5 = st.text_input("shots off target", key="away5")
        away6 = st.text_input("blocked shots", key="away6")
    
    home = [home6, home5, home4, home3, home2, home1]
    away = [away6, away5, away4, away3, away2, away1]
    
    if any(val is None or val == "" for val in home) or any(val is None or val == "" for val in away):
        no_data_message(message="No data available for this match")
        return
    
    home_data = [float(val) for val in home]
    away_data = [float(val) for val in away]


    data = {
        "home": home_data,
        "away": away_data,
        "itemName": [
            "Ball possession",
            "Expected goals",
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
        data=data,
        total_values=total_values,
        proportions=proportions,
        home_c=col_team1,
        away_c=col_team2,
    )
    fig, ax = stackedbarchart.draw(show_figure=False, save_figure=False)
    st.pyplot(fig)
    save_fig(fig=fig, file_name="StackedBarChart.png", key="stackedbar")


def example_radarchart_data():
    example_data = {
        "Player": ["Player A", "Player B"],
        "Goals": [10, 8],
        "Assists": [5, 7],
        "Passes": [85, 78],
        "Tackles": [45, 52],
        "Interceptions": [25, 30],
    }
    example_df = pd.DataFrame(example_data)

    # Convert to CSV
    csv_buffer = io.StringIO()
    example_df.to_csv(csv_buffer, sep=";", index=False)
    csv_string = csv_buffer.getvalue()

    return csv_string


def radarchart_visualisations():
    st.info(
        "Ensure the input file is a CSV, and the first column should be the player name and it's not considered",
        icon="ℹ️",
    )
    csv_string = example_radarchart_data()

    # Download button for example file
    st.download_button(
        label="Download Example CSV",
        data=csv_string,
        file_name="radar_chart_example.csv",
        mime="text/csv",
        key="example_radarchart",
    )
    # Players shots location
    col1, col2 = st.columns(2)

    with col1:
        group1_color = st.color_picker("Color", "#00f900", key="group1_color")

    with col2:
        group2_color = st.color_picker("Color", "#f90000", key="group2_color")

    uploaded_file = st.file_uploader("Choose a file", key="radarchart_fileuploader")
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file, sep=";")
        # st.button("Use this data", on_click=lambda: st.session_state.update(heatmap_data=dataframe))
    else:
        data = pd.DataFrame()

    if data.empty:
        no_data_message(message="No data available for this comparison")
        return

    # Convert all columns except the first one (player names) to float
    for col in data.columns[1:]:
        data[col] = data[col].astype(str).str.replace(',', '.').str.replace('%', '').str.strip()
        data[col] = data[col].astype(float)

    print("data columns: ", data.columns)
    params = list(data.columns)[1:]
    print("params: ", params)
    group_1 = data.iloc[0, 1:].tolist()
    group_2 = data.iloc[1, 1:].tolist()
    low = [0] * len(params)
    high = [max(group_1[i], group_2[i]) for i in range(len(group_1))]

    print("low: ", low)
    print("high: ", high)

    radar = Radarchart(
        params=params,
        group_1=group_1,
        group_2=group_2,
        low=low,
        high=high,
        group1_c=group1_color,
        group2_c=group2_color,
    )
    fig, ax = radar.draw_v2()
    st.pyplot(fig)
    save_fig(fig=fig, file_name="radarchart.png", key="radarchart")


def main():
    left_co, cent_co, last_co = st.columns(3)
    script_dir = os.path.dirname(__file__)
    image_path = os.path.join(script_dir, "assets/images/logo_botola_insights_red.png")
    with cent_co:
        image = Image.open(image_path)
        st.image(image, width=150)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Heatmap",
            "Shootmap",
            "Radarchart",
            "Stacked barchart",
            "Goal Location",
        ]
    )
    with tab1:
        st.header("Heatmap Visualization")
        heatmap_visualisations()

    with tab2:
        # TODO: add shootmap for specific player, by uploading multiple files and adding player name by filter
        st.header("Shootmap Visualization")
        shootmap_visualisations()

    # with tab3:
    #     st.header("Pizzachart Visualization")
    #     pizzachart_visualisations()

    with tab3:
        st.header("Radarchart Visualization")
        radarchart_visualisations()

    with tab4:
        st.header("Stackedbar")
        stacked_barchart_vizualisations()

    with tab5:
        # TODO: separate between player and goalkeeper
        # TODO: add filter by match
        # TODO: possibility to upload multiple files
        st.header("Goal Location")
        goal_location_visualisations()
        # goal_keeper_vizualisations(team=team, match=match)


if __name__ == "__main__":
    main()
