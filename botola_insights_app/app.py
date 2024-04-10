import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
from mplsoccer import Pitch
import io
from data.azure_data_extraction import get_conn, get_cursor, get_query_result
from charts.shootmap import ShootMap
import pandas as pd
from data_processing.shootmap_processor import ShootmapProcessor


# Add parent directory to Python path
def save_fig(fig, file_name):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight", transparent=True)
    buf.seek(0)
    st.download_button(
            "Download", buf, file_name=file_name, mime="image/png"
        )


def shootmap_visualisations():
    """Function to display the shootmap visualisations in the Streamlit app"""
    col1, col2, col3, col4 = st.columns(4)
    conn = get_conn()
    cursor = get_cursor(conn)
    query_get_seasons = """SELECT [seasonYear]
    FROM [dim].[AxeTournament]
    WHERE [seasonName] LIKE '%Botola%'"""
    seasons = get_query_result(query_get_seasons, conn, cursor)
    season_names = tuple([season[0] for season in seasons])
    with col1:
        season = st.selectbox("Shoose a Season", season_names, key="season")
        st.write("You selected:", season)

    query_get_teams = """SELECT [teamId]
            ,[teamIdInterne]
            ,[teamName]
            ,[teamNameCode]
            ,[teamShortName]
        FROM [dim].[AxeTeam]"""
    teams = get_query_result(query_get_teams, conn, cursor)
    team_names = tuple([team[2] for team in teams])
    with col2:
        team_shootmap = st.selectbox(
            "Shoose a Team", team_names, key="team_shootmap"
        )
        st.write("You selected:", team_shootmap)
    cursor = get_cursor(conn)
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
    matches = get_query_result(query_get_matches, conn, cursor)
    matches_names = tuple([match[-1] for match in matches])
    with col3:
        match = st.selectbox("Shoose a Match", matches_names, key="match")
        st.write("You selected:", match)
    with col4:
        home_c = st.color_picker('Home Color', '#00f900')
        away_c = st.color_picker('Away Color', '#F90004')
        
    cursor = get_cursor(conn)
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
    WHERE CONCAT([m].[homeName], ' - ', [m].[awayName]) = '{str(match)}'"""
    
    shootmap_data = get_query_result(query_get_shootmap_data, conn, cursor)
    columns = [col[0] for col in cursor.description]
    data = [{col: val for col, val in zip(columns, row)} for row in shootmap_data]
    df_shootmap = pd.DataFrame(data, columns=columns)
    if df_shootmap.empty:
        st.markdown("<h3 style='text-align: center; color: gray;margin-top: 10px'>No data available for this match</h3>", unsafe_allow_html=True)
        return
    # Here we can prepare the data for the shootmap
    shootmap_processor = ShootmapProcessor(data=df_shootmap)
    df_team1, df_team2 = shootmap_processor.process_data()
    pitch = ShootMap(df_team1=df_team1, df_team2=df_team2, pitch=Pitch, team1_c=home_c, team2_c=away_c)
    fig, ax = pitch.draw_v2(save_figure=False, show_figure=False)
    st.pyplot(fig)
    save_fig(fig=fig, file_name="Shootmap.png")

def main():
    left_co, cent_co,last_co = st.columns(3)
    with cent_co:
        st.image('./assets/images/logo_botola_insights_red.png',width=150)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Heatmap", "Shootmap", "Pizzachart", "Radarchart", "Stackedbar"]
    )
    with tab1:
        st.header("Heatmap Visualization")
        col1, col2 = st.columns(2)
        conn = get_conn()
        cursor = get_cursor(conn)
        query_get_teams = """SELECT [teamId]
                ,[teamIdInterne]
                ,[teamName]
                ,[teamNameCode]
                ,[teamShortName]
            FROM [dim].[AxeTeam]"""
        teams = get_query_result(query_get_teams, conn, cursor)
        # get Team names
        team_names = tuple([team[2] for team in teams])

        with col1:
            team = st.selectbox("Shoose a Team", team_names, key="team")
            st.write("You selected:", team)
        query_get_players = f"""SELECT [teamName]
                    ,[playerName]
                FROM [dim].[AxePlayer] p JOIN [dim].[AxeTeam] t 
                ON p.teamId = t.teamIdInterne 
                WHERE t.teamName = '{str(team)}'"""
        players = get_query_result(query_get_players, conn, cursor)
        # get Team names
        player_names = tuple([player[1] for player in players])

        with col2:
            player = st.selectbox("Shoose a player", player_names, key="player")
            st.write("You selected:", player)

        # Create a mplsoccer pitch instance
        pitch = Pitch()
        fig, ax = pitch.draw(figsize=(8, 4))
        # Display the pitch
        st.pyplot(fig)
        # Save figure to a BytesIO object
        save_fig(fig=fig, file_name="Heatmap.png")
        

    with tab2:
        st.header("Shootmap Visualization")
        shootmap_visualisations()

    with tab3:
        st.header("Pizzachart Visualization")

    with tab4:
        st.header("Radarchart Visualization")

    with tab5:
        st.header("Stackedbar")


if __name__ == "__main__":
    main()
