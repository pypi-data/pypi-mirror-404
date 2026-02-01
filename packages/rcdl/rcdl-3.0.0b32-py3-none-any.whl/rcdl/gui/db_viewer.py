# gui/db_viewer.py

import streamlit as st
import sqlite3

import pandas as pd

from rcdl.core.config import Config

TABLES = ["medias", "posts", "fuses"]


def get_table_columns(table_name):
    conn = sqlite3.connect(Config.DB_PATH)
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cur.fetchall()]
    conn.close()
    return columns


def get_table_data(table_name, sort_by=None, ascending=True):
    conn = sqlite3.connect(Config.DB_PATH)
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    if sort_by and sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=ascending)
    return df


def run_db_viewer():
    st.set_page_config(page_title="DB Viewer", layout="wide")
    st.title("Database Viewer")

    table_name = st.selectbox("Select Table", TABLES)

    # Load data
    df = get_table_data(table_name, sort_by=None, ascending=True)

    st.write(f"Showing `{table_name}` table ({len(df)} rows)")
    st.dataframe(df, width="stretch")
