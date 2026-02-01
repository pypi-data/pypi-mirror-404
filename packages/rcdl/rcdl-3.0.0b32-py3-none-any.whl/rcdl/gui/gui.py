# gui/gui.py

import streamlit as st

from rcdl.gui.db_viewer import run_db_viewer
from rcdl.gui.video_manager import video_manager

st.markdown(
    """
    <style>
    /* Remove top padding */
    .block-container {
        padding-top: 1rem !important;
    }

    /* Optional: remove Streamlit header */
    header[data-testid="stHeader"] {
        display: none;
    }

    /* Optional: remove footer */
    footer {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def run_gui():
    """
    Launches the Streamlit GUI.
    This function can be called from a CLI command.
    """
    # Streamlit code
    st.set_page_config(page_title="RCDL", layout="wide")

    # Sidebar navigation
    page = st.sidebar.radio("Go to", ["Home", "Manage Videos", "View DB"])

    if page == "Home":
        st.header("Home Page")
        st.write("Develloped by - ritonun -")

    elif page == "Manage Videos":
        video_manager()

    elif page == "View DB":
        run_db_viewer()


if __name__ == "__main__":
    run_gui()
