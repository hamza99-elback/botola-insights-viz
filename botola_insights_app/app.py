import sys
import os
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
from mplsoccer import Pitch
import io
from data.azure_data_extraction import get_conn, get_cursor, get_query_result
from charts.shootmap import ShootMap
from charts.pizzachart import Pizzachart
from charts.heatmap import Heatmap
import pandas as pd
from data_processing.shootmap_processor import ShootmapProcessor
import random
from mplsoccer import (
    VerticalPitch,
    Pitch,
)
import logging
import datetime
from PIL import Image

# Make connection with Azure Database
CONN = get_conn()

try:
    now = datetime.datetime.now()
    now_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f'./../logs/app_{now_str}.log'
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=filename, filemode='w')
except Exception as e:
    print("error in configuring logging")
    
random.seed(42)


# Add parent directory to Python path
def save_fig(fig, file_name):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight", transparent=True)
    buf.seek(0)
    st.download_button("Download", buf, file_name=file_name, mime="image/png")


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


def get_teams_list(cursor):
    query_get_teams = """SELECT [teamId]
                ,[teamIdInterne]
                ,[teamName]
                ,[teamNameCode]
                ,[teamShortName]
            FROM [dim].[AxeTeam]"""
    teams = get_query_result(query_get_teams, cursor)
    # get Team names
    team_names = tuple([team[2] for team in teams])
    return team_names


def get_players_list(team_name: str, cursor):
    query_get_players = f"""SELECT [teamName]
                ,[playerName]
            FROM [dim].[AxePlayer] p JOIN [dim].[AxeTeam] t 
            ON p.teamId = t.teamIdInterne 
            WHERE t.teamName = '{str(team_name)}'"""
    players = get_query_result(query_get_players, cursor)
    # get Team names
    player_names = tuple([player[1] for player in players])
    return player_names


def shootmap_visualisations():
    """Function to display the shootmap visualisations in the Streamlit app"""
    col1, col2, col3, col4 = st.columns(4)
    cursor = get_cursor(CONN)
    query_get_seasons = """SELECT [seasonYear]
    FROM [dim].[AxeTournament]
    WHERE [seasonName] LIKE '%Botola%'"""
    seasons = get_query_result(query_get_seasons, cursor)
    season_names = tuple([season[0] for season in seasons])
    with col1:
        season = st.selectbox("Shoose a Season", season_names, key="season")

    query_get_teams = """SELECT [teamId]
            ,[teamIdInterne]
            ,[teamName]
            ,[teamNameCode]
            ,[teamShortName]
        FROM [dim].[AxeTeam]"""
    teams = get_query_result(query_get_teams, cursor)
    team_names = tuple([team[2] for team in teams])
    with col2:
        team_shootmap = st.selectbox("Shoose a Team", team_names, key="team_shootmap")
    cursor = get_cursor(CONN)
    query_get_matches = f"""
                SELECT [matcheId],
            [round],
            [t].[seasonYear],
            [homeName],
            [awayName],
            CONCAT([homeName], ' - ', [awayName]) as matchName
        FROM [dim].[AxeMatche] m JOIN [dim].[AxeTournament] t 
        ON [m].[tounamentIdInterne]=[t].[tournamentId]
        WHERE [t].[seasonYear]='{str(season)}'
        AND ([homeName]='{str(team_shootmap)}' OR [awayName]='{str(team_shootmap)}')"""
    matches = get_query_result(query_get_matches, cursor)
    matches_names = tuple([match[-1] for match in matches])
    with col3:
        match = st.selectbox("Shoose a Match", matches_names, key="match")
    with col4:
        home_c = st.color_picker("Home Color", "#00f900")
        away_c = st.color_picker("Away Color", "#F90004")

    cursor = get_cursor(CONN)
    query_get_shootmap_data = f"""
            SELECT [PlayerId]
        ,[s].[matcheId]
        ,CONCAT([m].[homeName], ' - ', [m].[awayName]) as matchName
        ,[isHome]
        ,[EndY]
        ,[EndX]
        ,[xgot]
        ,[goalType]
        ,[xg]
        ,[timeSeconds]
        ,[time]
        ,[shotType]
        ,[reversedPeriodTime]
        ,[DrawId]
        ,[goalMouthLocation]
        ,[bodyPart]
        ,[DatumAddedTime]
        ,[BlockCoordinatesZ]
        ,[BlockCoordinatesY]
        ,[BlockCoordinatesX]
        ,[StartY]
        ,[StartX]
        ,[PlayerCoordinatesZ]
        ,[PlayerCoordinatesY]
        ,[PlayerCoordinatesX]
        ,[BlockY]
        ,[addedTime]
        ,[GoalMouthCoordinatesZ]
        ,[GoalMouthCoordinatesX]
        ,[GoalMouthCoordinatesY]
        ,[BlockX]
    FROM [dim].[FactShotMap] s JOIN [dim].[AxeMatche] m
    ON [s].[matcheId] = [m].[matcheId]
    WHERE CONCAT([m].[homeName], ' - ', [m].[awayName]) = '{str(match.replace("'", "''"))}'"""

    shootmap_data = get_query_result(query_get_shootmap_data, cursor)
    columns = [col[0] for col in cursor.description]
    data = [{col: val for col, val in zip(columns, row)} for row in shootmap_data]
    df_shootmap = pd.DataFrame(data, columns=columns)
    if df_shootmap.empty:
        no_data_message(message="No data available for this match")
        return

    # Here we can prepare the data for the shootmap
    shootmap_processor = ShootmapProcessor(data=df_shootmap)
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
    save_fig(fig=fig, file_name="Shootmap.png")


def pizzachart_visualisations():
    """Function to display the pizzachart visualisations in the Streamlit app"""
    col1, col2, col3 = st.columns(3)
    get_kpis_query = """SELECT TOP(1) goals-(penaltiesTaken*penaltyConversion)/100 as [Non penalty Goal]
      ,[totalTackle]
      ,[errorLeadToAShot]
      ,[possessionLostCtrl]
      ,[outfielderBlock]
      ,[totalClearance]
      ,[expectedAssists]
      ,[expectedGoals]
      ,[rating]
      ,[minutesPlayed]
      ,[totalOffside]
      ,[totalfouls]
      ,[wasFouled]
      ,[ownGoals]
      ,[goals]
      ,[onTargetScoringAttempt]
      ,[shotOffTarget]
      ,[bigChanceCreated]
      ,[wonContest]
      ,[totalContest]
      ,[dispossessed]
      ,[challengeLost]
      ,[duelWon]
      ,[duelLost]
      ,[aerialWon]
      ,[aerialLost]
      ,[touches]
      ,[accurateCross]
      ,[totalCross]
      ,[goalAssist]
      ,[penaltyWon]
      ,[accurateKeeperSweeper]
      ,[totalKeeperSweeper]
      ,[savedShotsFromInsideTheBox]
      ,[goodHighClaim]
      ,[aerialDuelsWonPercentage]
      ,[aerialDuelsWon]
      ,[totalDuelsWonPercentage]
      ,[ballRecovery]
      ,[interceptions]
      ,[accurateCrossesPercentage]
      ,[accurateFinalThirdPasses]
      ,[accurateLongBalls]
      ,[accurateLongBallsPercentage]
      ,[accuratePasses]
      ,[accuratePassesPercentage]
      ,[appearances]
      ,[inaccuratePasses]
      ,[totalPasses]
      ,[keyPasses]
      ,[successfulDribbles]
      ,[successfulDribblesPercentage]
      ,[yellowCards]
      ,[redCards]
      ,[directRedCards]
      ,[totalShots]
      ,[shotsOnTarget]
      ,[shotsOffTarget]
      ,[blockedShots]
      ,[goalConversionPercentage]
      ,[penaltiesTaken]
      ,[shotFromSetPiece]
      ,[clearances]
      ,[dribbledPast]
      ,[offsides]
      ,[passToAssist]
      ,[saves]
      ,[cleanSheet]
      ,[crossesNotClaimed]
      ,[matchesStarted]
      ,[penaltyConversion]
      ,[attemptPenaltyMiss]
      ,[goalsConceded]
      ,[scoringFrequency]
      ,[goalKicks]
  FROM [dim].[FactPlayerStatistics]"""
    cursor = get_cursor(CONN)
    kpis_data = get_query_result(get_kpis_query, cursor)
    columns = [col[0] for col in cursor.description]
    team_names = get_teams_list(cursor)
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

    player_names = get_players_list(team_pizza, cursor)
    with col2:
        player_pizza = player_selectbox(player_names, uuid=st.session_state.uuid_player)

    with col3:
        kpis_list = kpis_multiselect(columns, uuid=st.session_state.uuid_kpis)

    get_player_stats_query = f"""SELECT goals-(penaltiesTaken*penaltyConversion)/100 as [Non penalty Goal]
      ,[playerStatisticsId]
      ,[s].[playerId]
      ,[p].[playerName]
      ,[t].[teamName]
      ,[tournamentId]
      ,[totalTackle]
      ,[errorLeadToAShot]
      ,[possessionLostCtrl]
      ,[outfielderBlock]
      ,[totalClearance]
      ,[expectedAssists]
      ,[expectedGoals]
      ,[rating]
      ,[minutesPlayed]
      ,[totalOffside]
      ,[totalfouls]
      ,[wasFouled]
      ,[ownGoals]
      ,[goals]
      ,[onTargetScoringAttempt]
      ,[shotOffTarget]
      ,[bigChanceCreated]
      ,[wonContest]
      ,[totalContest]
      ,[dispossessed]
      ,[challengeLost]
      ,[duelWon]
      ,[duelLost]
      ,[aerialWon]
      ,[aerialLost]
      ,[touches]
      ,[accurateCross]
      ,[totalCross]
      ,[goalAssist]
      ,[penaltyWon]
      ,[accurateKeeperSweeper]
      ,[totalKeeperSweeper]
      ,[savedShotsFromInsideTheBox]
      ,[goodHighClaim]
      ,[aerialDuelsWonPercentage]
      ,[aerialDuelsWon]
      ,[totalDuelsWonPercentage]
      ,[ballRecovery]
      ,[interceptions]
      ,[accurateCrossesPercentage]
      ,[accurateFinalThirdPasses]
      ,[accurateLongBalls]
      ,[accurateLongBallsPercentage]
      ,[accuratePasses]
      ,[accuratePassesPercentage]
      ,[appearances]
      ,[inaccuratePasses]
      ,[totalPasses]
      ,[keyPasses]
      ,[successfulDribbles]
      ,[successfulDribblesPercentage]
      ,[yellowCards]
      ,[redCards]
      ,[directRedCards]
      ,[totalShots]
      ,[shotsOnTarget]
      ,[shotsOffTarget]
      ,[blockedShots]
      ,[goalConversionPercentage]
      ,[penaltiesTaken]
      ,[shotFromSetPiece]
      ,[clearances]
      ,[dribbledPast]
      ,[offsides]
      ,[passToAssist]
      ,[saves]
      ,[cleanSheet]
      ,[crossesNotClaimed]
      ,[matchesStarted]
      ,[penaltyConversion]
      ,[attemptPenaltyMiss]
      ,[goalsConceded]
      ,[scoringFrequency]
      ,[goalKicks]
  FROM [dim].[FactPlayerStatistics] s 
  JOIN [dim].[AxePlayer] p ON [p].[PlayerId]=[s].[playerId] 
  JOIN [dim].[AxeTeam] t ON [t].[teamIdInterne]=[p].[teamId]
  WHERE [p].[playerName]='{str(player_pizza)}'"""
    cursor = get_cursor(CONN)
    pizzachart_data = get_query_result(get_player_stats_query, cursor)
    columns_pizza = [col[0] for col in cursor.description]
    data = [
        {col: val for col, val in zip(columns_pizza, row)} for row in pizzachart_data
    ]
    print("data: ", data)
    df_pizzachart = pd.DataFrame(data, columns=columns_pizza).reset_index(drop=True)
    if df_pizzachart.empty:
        no_data_message(message="No data available for this player")
        return
    df_pizzachart = df_pizzachart[kpis_list]
    categories = list(df_pizzachart.columns)
    group_1 = list(df_pizzachart.values[0])
    min_range = [0] * len(group_1)
    new_list = [x / 4 for x in df_pizzachart.max().tolist()]
    max_range = [x + y for x, y in zip(df_pizzachart.max().tolist(), new_list)]
    nb_cat = len(categories)
    list_colors = ["#FE4844", "#30E5D0", "#9726E0"]
    slice_colors = list_colors * (nb_cat // 3) + list_colors[: nb_cat % 3]
    slice_colors.sort()
    text_colors = ["#000000"] * (nb_cat)
    print(len(slice_colors), len(text_colors), len(categories))
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
    save_fig(fig=fig, file_name="Pizzachart.png")


def heatmap_visualisations():
    col1, col2 = st.columns(2)
    cursor = get_cursor(CONN)
    team_list = get_teams_list(cursor)
    with col1:
        team = st.selectbox("Shoose a Team", team_list, key="team")
    players_list = get_players_list(team, cursor)
    with col2:
        player = st.selectbox("Shoose a Player", players_list, key="player")
    get_heatmap_data_query = f"""SELECT [heatMapId]
      ,[y]
      ,[x]
      ,[matcheId]
      ,[p].[playerName]
        FROM [dim].[FactHeatMap] h
        JOIN [dim].[AxePlayer] p ON [h].[playerId]=[p].[PlayerId]
        WHERE [p].[playerName]='{player}'"""
    cursor = get_cursor(CONN)
    heatmap_data = get_query_result(get_heatmap_data_query, cursor)
    columns = [col[0] for col in cursor.description]
    data = [{col: val for col, val in zip(columns, row)} for row in heatmap_data]
    df_heatmap = pd.DataFrame(data, columns=columns)
    if df_heatmap.empty:
        no_data_message(message="No data available for this player")
        return
    pitch = Heatmap(data=df_heatmap, pitch=VerticalPitch)
    fig, ax = pitch.draw()
    st.pyplot(fig)
    save_fig(fig=fig, file_name="Heatmap.png")


def main():
    left_co, cent_co, last_co = st.columns(3)
    script_dir = os.path.dirname(__file__)
    image_path = os.path.join(script_dir, 'assets/images/logo_botola_insights_red.png')
    with cent_co:
        image = Image.open(image_path)
        st.image(image, width=150)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Heatmap", "Shootmap", "Pizzachart", "Radarchart", "Stackedbar"]
    )
    with tab1:
        st.header("Heatmap Visualization")
        heatmap_visualisations()

        # # Create a mplsoccer pitch instance
        # pitch = Pitch()
        # fig, ax = pitch.draw(figsize=(8, 4))
        # # Display the pitch
        # st.pyplot(fig)
        # # Save figure to a BytesIO object
        # save_fig(fig=fig, file_name="Heatmap.png")

    with tab2:
        st.header("Shootmap Visualization")
        shootmap_visualisations()

    with tab3:
        st.header("Pizzachart Visualization")
        pizzachart_visualisations()

    with tab4:
        st.header("Radarchart Visualization")

    with tab5:
        st.header("Stackedbar")


if __name__ == "__main__":
    main()
