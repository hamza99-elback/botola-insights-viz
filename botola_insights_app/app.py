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
from charts.shot_goal_location import ShotGoalLocation
from charts.stackedbarchart import StackedBarChart
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

# TODO: add Season Filter in all the queries
# TODO: Isolate all queries results in a separate file
try:
    # Make connection with Azure Database
    CONN = get_conn()
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
                ,[teamIdInterne]
                ,[teamName]
                ,[teamNameCode]
                ,[teamShortName]
            FROM [dim].[AxeTeam]"""
    teams = get_query_result(query_get_teams, cursor)
    # get Team names
    team_names = [team[2] for team in teams]
    return team_names


def get_seasons_list(cursor)->tuple:
    """Get all seasons list from the database"""
    query_get_seasons = """SELECT [seasonYear]
    FROM [dim].[AxeTournament]
    WHERE [seasonName] LIKE '%Botola%'"""
    seasons = get_query_result(query_get_seasons, cursor)
    seasons_names = tuple([season[0] for season in seasons])
    return seasons_names


def get_all_players_list(cursor):
    query_get_players = f"""SELECT [teamName]
                ,[playerName]
                ,[position]
            FROM [dim].[AxePlayer] p JOIN [dim].[AxeTeam] t 
            ON p.teamId = t.teamIdInterne"""
    players = get_query_result(query_get_players, cursor)
    # get Team names
    player_names = [
        {"player_name": player[1], "position": player[2],"team_name": player[0]} for player in players
    ]
    return player_names


def get_players_list(team_name: str, position: str = None):
    if position:
        player_list = [
            player["player_name"]
            for player in PLAYERS_LIST
            if player["team_name"] == team_name and player["position"] == position
        ]
        print("player_list: ", player_list)
    else:
        player_list = [
            player["player_name"]
            for player in PLAYERS_LIST
            if player["team_name"] == team_name
        ]
    return player_list

def get_players_by_match(match: str, position:str, cursor):
    query_get_players = f"""SELECT DISTINCT([p].[playerName])
                        FROM [dim].[AxeLineUps] [l]
                        JOIN [dim].[AxePlayer] p ON [l].[PlayerId]=[p].[PlayerId]
                        JOIN [dim].[AxeMatche] m ON [m].[matcheId]=[l].[matcheId]
                        WHERE [l].[substitute]=0
                        AND [p].[position]='{position}'
            AND CONCAT([m].[homeName], ' - ', [m].[awayName]) = '{str(match.replace("'", "''"))}'"""
    cursor = get_cursor(CONN)
    players = get_query_result(query_get_players, cursor)
    # get Team names
    player_names = [
        player[0] for player in players
    ]
    return player_names

def get_teams_by_season(season: str):
    pass
def get_all_matches_list(cursor):
    query_get_matches = f"""
                SELECT [matcheId],
            [round],
            [t].[seasonYear],
            [homeName],
            [awayName],
            CONCAT([homeName], ' - ', [awayName]) as matchName
        FROM [dim].[AxeMatche] m JOIN [dim].[AxeTournament] t 
        ON [m].[tounamentIdInterne]=[t].[tournamentId]"""
    matches = get_query_result(query_get_matches, cursor)
    matches_names = [
        {
            "home_team": match[3],
            "away_team": match[4],
            "round": match[1],
            "season": match[2],
            "match_name": match[5],
        }
        for match in matches
    ]
    return matches_names


def get_matches_list(team: str, season: str)->list:
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
        and match["season"] == season
    ]
    return matches_list


def get_shootmap_data(match: str, player: str, cursor):
    if player:
        query_get_shootmap_data = f"""SELECT [p].[PlayerId]
      ,[s].[matcheId]
      ,CONCAT([m].[homeName], ' - ', [m].[awayName]) as matchName
      ,[m].[homeName]
      ,[p].[PlayerName]
      ,[m].[awayName]
      ,[isHome]
      ,[xgot]
      ,[time]
      ,[goalType]
      ,[xg]
      ,[shotType]
      ,[reversedPeriodTime]
      ,[goalMouthLocation]
      ,[bodyPart]
      ,[BlockCoordinatesZ]
      ,[BlockCoordinatesY]
      ,[BlockCoordinatesX]
      ,[PlayerCoordinatesZ]
      ,[PlayerCoordinatesY]
      ,[PlayerCoordinatesX]
      ,[GoalMouthCoordinatesZ]
      ,[GoalMouthCoordinatesX]
      ,[GoalMouthCoordinatesY]
        FROM [dim].[FactShotMap] s JOIN [dim].[AxeMatche] m ON [s].[matcheId] = [m].[matcheId]
        JOIN [dim].[AxePlayer] p ON [s].[PlayerId] = [p].[PlayerId]
        WHERE CONCAT([m].[homeName], ' - ', [m].[awayName]) = '{str(match.replace("'", "''"))}'
        AND [p].[PlayerName] LIKE '%{player}%'"""
    else:
        query_get_shootmap_data = f"""
            SELECT [PlayerId]
        ,[s].[matcheId]
        ,CONCAT([m].[homeName], ' - ', [m].[awayName]) as matchName
        ,[isHome]
        ,[xgot]
        ,[time]
        ,[goalType]
        ,[xg]
        ,[shotType]
        ,[goalMouthLocation]
        ,[bodyPart]
        ,[StartY]
        ,[StartX]
        ,[PlayerCoordinatesZ]
        ,[PlayerCoordinatesY]
        ,[PlayerCoordinatesX]
        ,[GoalMouthCoordinatesZ]
        ,[GoalMouthCoordinatesX]
        ,[GoalMouthCoordinatesY]
    FROM [dim].[FactShotMap] s JOIN [dim].[AxeMatche] m
    ON [s].[matcheId] = [m].[matcheId]
    WHERE CONCAT([m].[homeName], ' - ', [m].[awayName]) = '{str(match.replace("'", "''"))}'"""
    shootmap_data = get_query_result(query_get_shootmap_data, cursor)
    return shootmap_data

def get_stackbarchart_data(match: str, cursor):
    """Get Stacked Bar Chart Data

    Args:
        match (str): _description_
        cursor (_type_): _description_
    """
    # "Ball possession",
    #         "Expected goals",
    #         "Total shots",
    #         "Shots on target",
    #         "Shots off target",
    #         "Blocked shots",
    query_stackedbar = f"""SELECT [t].[teamName]
                , CASE WHEN [m].[homeName] = [t].[teamName] THEN 'YES' ELSE 'NO' END AS [isHome]
                ,[Ball_possession]
                ,[Expected_goals]
                ,[Total_shots]
                ,[Shots_on_target]
                ,[Shots_off_target]
                ,[Blocked_shots]
                FROM [dim].[FactMatcheStats] ms
                JOIN [dim].[AxeMatche] m ON [m].[matcheId]=[ms].[matcheId]
                JOIN [dim].[AxeTeam] t ON [t].[teamId]=[ms].[teamId]
                WHERE CONCAT([m].[homeName], ' - ', [m].[awayName]) = '{str(match.replace("'", "''"))}'"""
    stackedbar_data = get_query_result(query_stackedbar, cursor)
    return stackedbar_data


def get_opponent_shootmap_data(match: str, player: str, cursor):
    if player:
        query_get_shootmap_data = f"""SELECT [p].[playerName] as GoalKeeperName
       ,[p2].[playerName]
       ,[m].[matcheId]
       ,CONCAT([m].[homeName], ' - ', [m].[awayName]) as matchName
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
      ,[GoalMouthCoordinatesY]
      ,[addedTime]
      ,[GoalMouthCoordinatesZ]
      ,[GoalMouthCoordinatesX]
      ,[BlockX]
      ,[isHome]
  FROM [dim].[AxeLineUps] l 
  JOIN [dim].[AxeMatche] m ON [l].[matcheId]=[m].[matcheId]
  JOIN [dim].[FactShotMap] s ON [s].[matcheId]=[m].[matcheId]
  JOIN [dim].[AxePlayer] p2 on [p2].[PlayerId]=[s].[PlayerId]
  JOIN [dim].[AxePlayer] p on [p].[PlayerId]=[l].[PlayerId]
  WHERE [p].[position] = 'G'
  AND [p].[teamId]=[p2].[teamId]
  AND [l].[substitute]=0
  AND CONCAT([m].[homeName], ' - ', [m].[awayName]) = '{str(match.replace("'", "''"))}'
  AND [p].[playerName]!='{player}'"""
    else:
        query_get_shootmap_data = f"""
            SELECT [PlayerId]
        ,[s].[matcheId]
        ,CONCAT([m].[homeName], ' - ', [m].[awayName]) as matchName
        ,[isHome]
        ,[xgot]
        ,[time]
        ,[goalType]
        ,[xg]
        ,[shotType]
        ,[goalMouthLocation]
        ,[bodyPart]
        ,[StartY]
        ,[StartX]
        ,[PlayerCoordinatesZ]
        ,[PlayerCoordinatesY]
        ,[PlayerCoordinatesX]
        ,[GoalMouthCoordinatesZ]
        ,[GoalMouthCoordinatesX]
        ,[GoalMouthCoordinatesY]
    FROM [dim].[FactShotMap] s JOIN [dim].[AxeMatche] m
    ON [s].[matcheId] = [m].[matcheId]
    WHERE CONCAT([m].[homeName], ' - ', [m].[awayName]) = '{str(match.replace("'", "''"))}'"""
    shootmap_data = get_query_result(query_get_shootmap_data, cursor)
    return shootmap_data


def get_shootmap_data_goalkeeper(match: str, player: str, cursor):
    if player:
        query_get_shootmap_data = f"""SELECT [p].[playerName] as GoalKeeperName
                        ,[m].[matcheId]
                        ,CONCAT([m].[homeName], ' - ', [m].[awayName]) as matchName
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
                        ,[GoalMouthCoordinatesY]
                        ,[addedTime]
                        ,[GoalMouthCoordinatesZ]
                        ,[GoalMouthCoordinatesX]
                        ,[BlockX]
                        ,[isHome]
                    FROM [dim].[AxeLineUps] l 
                    JOIN [dim].[AxeMatche] m ON [l].[matcheId]=[m].[matcheId]
                    JOIN [dim].[FactShotMap] s ON [s].[matcheId]=[m].[matcheId]
                    JOIN [dim].[AxePlayer] p on [p].[PlayerId]=[l].[PlayerId]
                    WHERE [p].[position] = 'G' 
                    WHERE CONCAT([m].[homeName], ' - ', [m].[awayName]) = '{str(match.replace("'", "''"))}'
                    AND [p].[PlayerName] LIKE '%{player}%'"""
    else:
        query_get_shootmap_data = f"""
            SELECT [p].[playerName] as GoalKeeperName
                        ,[m].[matcheId]
                        ,CONCAT([m].[homeName], ' - ', [m].[awayName]) as matchName
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
                        ,[GoalMouthCoordinatesY]
                        ,[addedTime]
                        ,[GoalMouthCoordinatesZ]
                        ,[GoalMouthCoordinatesX]
                        ,[BlockX]
                        ,[isHome]
                    FROM [dim].[AxeLineUps] l 
                    JOIN [dim].[AxeMatche] m ON [l].[matcheId]=[m].[matcheId]
                    JOIN [dim].[FactShotMap] s ON [s].[matcheId]=[m].[matcheId]
                    JOIN [dim].[AxePlayer] p on [p].[PlayerId]=[l].[PlayerId]
                    WHERE [p].[position] = 'G' 
                    WHERE CONCAT([m].[homeName], ' - ', [m].[awayName]) = '{str(match.replace("'", "''"))}'"""
    shootmap_data = get_query_result(query_get_shootmap_data, cursor)
    return shootmap_data


# def get_teams_by_season(season: str):

#     return team_names


# Get Teams list
cursor = get_cursor(CONN)
print("cursor: ", cursor)
TEAMS_LIST = get_all_teams_list(cursor)
PLAYERS_LIST = get_all_players_list(cursor)
SEASONS_LIST = get_seasons_list(cursor)
MATCHES_LIST = get_all_matches_list(cursor)


def shootmap_visualisations():
    """Function to display the shootmap visualisations in the Streamlit app"""
    col1, col2, col3, col4 = st.columns(4)
    cursor = get_cursor(CONN)
    season_names = SEASONS_LIST
    with col1:
        season = st.selectbox("Shoose a Season", season_names, key="season")
    team_names = TEAMS_LIST
    with col2:
        team_shootmap = st.selectbox("Shoose a Team", team_names, key="team_shootmap")
    matches_names = get_matches_list(team=team_shootmap, season=season)
    with col3:
        match = st.selectbox("Shoose a Match", matches_names, key="match")
    with col4:
        home_c = st.color_picker("Home Color", "#00f900")
        away_c = st.color_picker("Away Color", "#F90004")

    cursor = get_cursor(CONN)
    shootmap_data = get_shootmap_data(match=match, player=None, cursor=cursor)
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
    save_fig(fig=fig, file_name="Shootmap.png", key="shootmap")


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

    get_player_stats_query = f"""SELECT goals-(penaltiesTaken*penaltyConversion)/100 as [Non penalty Goal]
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
    get_max_stats_query = """SELECT MAX((goals-(penaltiesTaken*penaltyConversion)/100)) AS [Non penalty Goal]
      ,MAX([totalTackle]) AS [totalTackle]
      ,MAX([errorLeadToAShot]) AS [errorLeadToAShot]
      ,MAX([possessionLostCtrl]) AS [possessionLostCtrl]
      ,MAX([outfielderBlock]) AS [outfielderBlock]
      ,MAX([totalClearance]) AS [totalClearance]
      ,MAX([expectedAssists]) AS [expectedAssists]
      ,MAX([expectedGoals]) AS [expectedGoals]
      ,MAX([rating]) AS [rating]
      ,MAX([minutesPlayed]) AS [minutesPlayed]
      ,MAX([totalOffside]) AS [totalOffside]
      ,MAX([totalfouls]) AS [totalfouls]
      ,MAX([wasFouled]) AS [wasFouled]
      ,MAX([ownGoals]) AS [ownGoals]
      ,MAX([goals]) AS [goals]
      ,MAX([onTargetScoringAttempt]) AS [onTargetScoringAttempt]
      ,MAX([shotOffTarget]) AS [shotOffTarget]
      ,MAX([bigChanceCreated]) AS [bigChanceCreated]
      ,MAX([wonContest]) AS [wonContest]
      ,MAX([totalContest]) AS [totalContest]
      ,MAX([dispossessed]) AS [dispossessed]
      ,MAX([challengeLost]) AS [challengeLost]
      ,MAX([duelWon]) AS [duelWon]
      ,MAX([duelLost]) AS [duelLost]
      ,MAX([aerialWon]) AS [aerialWon]
      ,MAX([aerialLost]) AS [aerialLost]
      ,MAX([touches]) AS [touches]
      ,MAX([accurateCross]) AS [accurateCross]
      ,MAX([totalCross]) AS [totalCross]
      ,MAX([goalAssist]) AS [goalAssist]
      ,MAX([penaltyWon]) AS [penaltyWon]
      ,MAX([accurateKeeperSweeper]) AS [accurateKeeperSweeper]
      ,MAX([totalKeeperSweeper]) AS [totalKeeperSweeper]
      ,MAX([savedShotsFromInsideTheBox]) AS [savedShotsFromInsideTheBox]
      ,MAX([goodHighClaim]) AS [goodHighClaim]
      ,MAX([aerialDuelsWonPercentage]) AS [aerialDuelsWonPercentage]
      ,MAX([aerialDuelsWon]) AS [aerialDuelsWon]
      ,MAX([totalDuelsWonPercentage]) AS [totalDuelsWonPercentage]
      ,MAX([ballRecovery]) AS [ballRecovery]
      ,MAX([interceptions]) AS [interceptions]
      ,MAX([accurateCrossesPercentage]) AS [accurateCrossesPercentage]
      ,MAX([accurateFinalThirdPasses]) AS [accurateFinalThirdPasses]
      ,MAX([accurateLongBalls]) AS [accurateLongBalls]
      ,MAX([accurateLongBallsPercentage]) AS [accurateLongBallsPercentage]
      ,MAX([accuratePasses]) AS [accuratePasses]
      ,MAX([accuratePassesPercentage]) AS [accuratePassesPercentage]
      ,MAX([appearances]) AS [appearances]
      ,MAX([inaccuratePasses]) AS [inaccuratePasses]
      ,MAX([totalPasses]) AS [totalPasses]
      ,MAX([keyPasses]) AS [keyPasses]
      ,MAX([successfulDribbles]) AS [successfulDribbles]
      ,MAX([successfulDribblesPercentage]) AS [successfulDribblesPercentage]
      ,MAX([yellowCards]) AS [yellowCards]
      ,MAX([redCards]) AS [yellowCards]
      ,MAX([directRedCards]) AS [directRedCards]
      ,MAX([totalShots]) AS [totalShots]
      ,MAX([shotsOnTarget]) AS [shotsOnTarget]
      ,MAX([shotsOffTarget]) AS [shotsOffTarget]
      ,MAX([blockedShots]) AS [blockedShots]
      ,MAX([goalConversionPercentage]) AS [goalConversionPercentage]
      ,MAX([penaltiesTaken]) AS [penaltiesTaken]
      ,MAX([shotFromSetPiece]) AS [shotFromSetPiece]
      ,MAX([clearances]) AS [clearances]
      ,MAX([dribbledPast]) AS [dribbledPast]
      ,MAX([offsides]) AS [offsides]
      ,MAX([passToAssist]) AS [passToAssist]
      ,MAX([saves]) AS [saves]
      ,MAX([cleanSheet]) AS [cleanSheet]
      ,MAX([crossesNotClaimed]) AS [crossesNotClaimed]
      ,MAX([matchesStarted]) AS [matchesStarted]
      ,MAX([penaltyConversion]) AS [penaltyConversion]
      ,MAX([attemptPenaltyMiss]) AS [attemptPenaltyMiss]
      ,MAX([goalsConceded]) AS [goalsConceded]
      ,MAX([scoringFrequency]) AS [scoringFrequency]
      ,MAX([goalKicks]) AS [goalKicks]
  FROM [dim].[FactPlayerStatistics] s 
  JOIN [dim].[AxePlayer] p ON [p].[PlayerId]=[s].[playerId] 
  JOIN [dim].[AxeTeam] t ON [t].[teamIdInterne]=[p].[teamId]"""
    # player stats
    cursor = get_cursor(CONN)
    pizzachart_data = get_query_result(get_player_stats_query, cursor)
    columns_pizza = [col[0] for col in cursor.description]
    data = [
        {col: val for col, val in zip(columns_pizza, row)} for row in pizzachart_data
    ]
    df_pizzachart = pd.DataFrame(data, columns=columns_pizza).reset_index(drop=True)
    # maximum stats
    cursor = get_cursor(CONN)
    max_pizzachart_data = get_query_result(get_max_stats_query, cursor)
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
    print("max_range: ", df_max_pizzachart)
    print("group_1: ", df_pizzachart)
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
    save_fig(fig=fig, file_name="Pizzachart.png", key="pizzachart")


def heatmap_visualisations():
    col1, col2 = st.columns(2)
    cursor = get_cursor(CONN)
    team_list = TEAMS_LIST
    with col1:
        team = st.selectbox("Shoose a Team", team_list, key="team")
    players_list = get_players_list(team)
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
    save_fig(fig=fig, file_name="Heatmap.png", key="heatmap")


def goal_location_visualisations():
    
    team, match = None, None
    # Players shots location
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        seasons_list = SEASONS_LIST
        season = st.selectbox("Shoose a season", seasons_list, key="season_53")

    with col2:
        teams_list = TEAMS_LIST
        team = st.selectbox("Shoose a Team", teams_list, key="team_53")

    with col3:
        players_list = get_players_list(team)
        player = st.selectbox(
            "Shoose a Player", ["None"] + players_list, key="player_53"
        )

    with col4:
        matches_list = get_matches_list(team=team, season=season)
        match = st.selectbox("Shoose a match", matches_list, key="match_53")

    with col5:
        color = st.color_picker("Color", "#00f900")
    columns_to_keep = [
        "GoalMouthCoordinatesY",
        "GoalMouthCoordinatesZ",
        "shotType",
        "xg",
    ]
    player_value = player if player != "None" else None
    shootmap_data = get_shootmap_data(match=match, player=player_value, cursor=cursor)
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
    print(df_goal_location)
    if df_goal_location.empty:
        no_data_message(message="No data available for this match")
        return (team, match) if(team is not None) and (match is not None) else ("Default", "Default")

    shot_goal_location = ShotGoalLocation(
        data=df_goal_location.to_records(), color=color
    )
    fig, ax = shot_goal_location.draw()
    st.pyplot(fig)
    save_fig(fig=fig, file_name="ShotGoalLocation.png", key="goal_location")
    return (team, match) if(team is not None) and (match is not None) else ("Default", "Default")


def goal_keeper_vizualisations(match, team):
    col1, col2= st.columns(2)

    with col1:
        players_list = get_players_by_match(match=match, position="G", cursor=cursor)
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
    shootmap_data = get_opponent_shootmap_data(match=match, player=player_value, cursor=cursor)
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
    df_goal_location = df_goal_location.loc[df_goal_location["shotType"].isin(['save', 'goal'])]
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
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        col_team1 = st.color_picker("Color", "#00f900", key="col_team1")
        col_team2 = st.color_picker("Color", "#000990", key="col_team2")
        
    with col2:
        season = st.selectbox("Shoose Season", SEASONS_LIST, key="season_sbr")

    with col3:
        team = st.selectbox("Shoose a Team", TEAMS_LIST, key="team_sbr")

    with col4:
        match = st.selectbox(
            "Shoose a Match",
            get_matches_list(season=season, team=team),
            key="match_sbr",
        )

    stacked_data = get_stackbarchart_data(match=match, cursor=cursor)
    columns = [col[0] for col in cursor.description]
    data = [{col: val for col, val in zip(columns, row)} for row in stacked_data]
    df_stacked = pd.DataFrame(data, columns=columns)
    if df_stacked.empty:
        no_data_message(message="No data available for this match")
        return
    home_data = list(df_stacked.loc[df_stacked["isHome"]=="YES"].to_records()[0])[3:]
    away_data = list(df_stacked.loc[df_stacked["isHome"]=="NO"].to_records()[0])[3:]
    home_data = [float(home_data[_]) if _==1 else int(home_data[_]) for _ in range(len(home_data))]
    away_data = [float(home_data[_]) if _==1 else int(away_data[_]) for _ in range(len(away_data))]
    
    

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


def main():
    left_co, cent_co, last_co = st.columns(3)
    script_dir = os.path.dirname(__file__)
    image_path = os.path.join(script_dir, "assets/images/logo_botola_insights_red.png")
    with cent_co:
        image = Image.open(image_path)
        st.image(image, width=150)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "Heatmap",
            "Shootmap",
            "Pizzachart",
            "Radarchart",
            "Stackedbar",
            "Goal Location",
        ]
    )
    with tab1:
        st.header("Heatmap Visualization")
        heatmap_visualisations()

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
        stacked_barchart_vizualisations()

    with tab6:
        st.header("Goal Location")
        (team, match) = goal_location_visualisations()
        goal_keeper_vizualisations(team=team, match=match)


if __name__ == "__main__":
    main()
