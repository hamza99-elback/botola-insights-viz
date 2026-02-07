import os
import pyodbc, struct

from typing import Union
from dotenv import load_dotenv
import logging

# Load .env file
load_dotenv()


def get_conn():
    """Make a connection to the database using the connection string from the .env file

    Returns:
        _type_: _description_
    """
    conn=None   
    try:
        connection_string = os.getenv("CONNECTION_STRING_READ_ONLY_DRIVER_18")
        conn = pyodbc.connect(connection_string)
    except Exception as e:
        logging.error(f"Error while connecting to the database, try using string connection for ODBC 18: {e}")
        try:
            connection_string = os.getenv("CONNECTION_STRING_READ_ONLY_DRIVER_17")
            conn = pyodbc.connect(connection_string)
        except Exception as e:
            connection_string = os.getenv("LOCAL_CONNECTION_STRING")
            conn = pyodbc.connect(connection_string)
    # else:
    #     logging.error(f"Error while connecting to the database")
    return conn

def get_cursor(conn):
    """Get a cursor from the connection

    Args:
        conn (_type_): _description_

    Returns:
        _type_: _description_
    """
    try:
        cursor = conn.cursor()
        return cursor
    except Exception as e:
        logging.error(f"Error while getting cursor: {e}")
        return None

def get_query_result(query: str, cursor: pyodbc.Cursor) -> Union[list, None]:
    """Get the result of a query

    Args:
        query (str): _description_
        cursor (pyodbc.Cursor): _description_

    Returns:
        Union[list, None]: _description_
    """
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Exception as e:
        logging.error(f"Error while executing query: {e}")
        return None

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