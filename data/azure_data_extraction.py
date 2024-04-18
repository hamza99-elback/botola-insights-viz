import os
import pyodbc, struct

from typing import Union
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Now you can access the variables using os.getenv
connection_string = os.getenv("CONNECTION_STRING_READ_ONLY")

connection_string = connection_string



def get_conn():
    conn = pyodbc.connect(connection_string)
    return conn

def get_cursor(conn):
    cursor = conn.cursor()
    return cursor

def get_query_result(query: str, conn: pyodbc.Connection, cursor: pyodbc.Cursor) -> Union[list, None]:
    cursor.execute(query)
    result = cursor.fetchall()
    return result

if __name__=="__main__":
    conn = get_conn()
    cursor = get_cursor(conn)
    query = """SELECT [teamId]
            ,[teamIdInterne]
            ,[teamName]
            ,[teamNameCode]
            ,[teamShortName]
        FROM [dim].[AxeTeam]"""
    result = get_query_result(query, conn, cursor)
    # get Team names
    team_names = [team[2] for team in result]
    print(conn)