# gui/video_manager.py

import os
import urllib.parse

import streamlit as st
import streamlit.components.v1 as components


from rcdl.core.config import Config
from rcdl.core.models import Status, Media
from rcdl.core.db import DB
from rcdl.utils import format_seconds


previous_statuses = {}


def video_html(path):
    safe_path = urllib.parse.quote(path, safe="")
    # Use the same IP as the one in the browser URL

    return f"""
    <video controls preload="metadata" style="width:100%; max-height:320px;">
        <source
            src="http://{Config.HOST}:8123/video?path={safe_path}"
            type="video/mp4"
        >
    </video>
    """


def set_status(media: Media, status: Status):
    key = media.post_id + media.url
    previous_statuses[key] = media.status
    media.status = status

    with DB() as db:
        db.update_media(media)
    print(f"Set {media.post_id} to {status.value}")

    for m in st.session_state.medias:
        if m.post_id == media.post_id and m.url == media.url:
            m.status = status
            break


def video_manager():
    if "reload_medias" not in st.session_state:
        st.session_state.reload_medias = True
    if "media_index" not in st.session_state:
        st.session_state.media_index = 0

    st.title("Video Manager")
    Config.set_host()

    # Filter & Sorting UI
    with st.expander("Filters & Sorting", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.selectbox(
                "Sort By",
                options=["file_size", "service", "duration", "file_path"],
                index=0,
                key="sort_by",
            )
        with col2:
            st.radio(
                "Order",
                options=[True, False],
                format_func=lambda x: "Ascending" if x else "Descending",
                horizontal=True,
                key="ascending",
            )
        with col3:
            st.text_input(
                "Creator ID(user)",
                placeholder="Leave empty for all",
                key="creator_filter",
            )
        st.multiselect(
            "Status",
            options=list(Status),
            default=[Status.DOWNLOADED, Status.OPTIMIZED],
            key="status_filter",
        )

        if st.button("Apply"):
            st.session_state.reload_medias = True

    # load db
    if st.session_state.reload_medias or "medias" not in st.session_state:
        with DB() as db:
            medias = db.query_medias_by_status_sorted(
                st.session_state.status_filter,
                sort_by=st.session_state.sort_by,
                ascending=st.session_state.ascending,
            )

            # check if in a fuse group

            # creator filter
            if st.session_state.creator_filter:
                filtered = []
                for m in medias:
                    post = db.query_post_by_id(m.post_id)
                    if (
                        post
                        and post.user == st.session_state.creator_filter
                        and db.query_fuses_by_id(m.post_id) is None
                    ):
                        filtered.append(m)
                medias = filtered

            st.session_state.medias = medias
            st.session_state.media_index = 0
        st.session_state.reload_medias = False

    medias = st.session_state.medias
    if not medias:
        st.info("No media found")
        return

    # session state
    if "media_index" not in st.session_state:
        st.session_state.media_index = 0

    idx = st.session_state.media_index
    media = medias[idx]

    # media info
    st.subheader(f"Media {idx + 1} / {len(medias)}")

    with DB() as db:
        post = db.query_post_by_id(media.post_id)
        if post is None:
            st.info("No matching post found")
            return

    col_video, col_info = st.columns([1, 2])
    with col_info:
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Post ID:**", media.post_id)
            st.write("**Service:**", media.service)
            st.write("**User:**", post.user)
            st.write("**Duration:**", format_seconds(media.duration))
            st.write("**Sequence:**", media.sequence)
            st.write("**Size:**", round(media.file_size / (1024 * 1024), 1), "MB")
            st.write("**Status:**", media.status)
            key = media.post_id + media.url
            if key in previous_statuses:
                st.write("**PREV STATUS:**", previous_statuses[key])
            st.write("**Path:**", media.file_path)
            st.write("**Created at**:", media.created_at[0:16])

        with col2:
            # controls
            c1, c2, c3 = st.columns([1, 1, 2])
            with c1:
                if st.button("⏮ Prev", disabled=idx == 0):
                    st.session_state.media_index -= 1
                    st.rerun()
                if st.button("⏭ Next", disabled=idx >= len(medias) - 1):
                    st.session_state.media_index += 1
                    st.rerun()
            with c2:
                if st.button("Remove"):
                    set_status(media, Status.TO_BE_DELETED)
                    st.rerun()
                if st.button("Revert Status"):
                    key = media.post_id + media.url
                    if key in previous_statuses:
                        set_status(media, previous_statuses[key])
                    else:
                        print("Not in previous status")
                    st.rerun()
            with c3:
                chosen_status = st.selectbox(
                    "Set Status",
                    options=list(Status),
                    index=list(Status).index(media.status)
                    if media.status in list(Status)
                    else 0,
                )
                if st.button("Apply Status"):
                    set_status(media, chosen_status)
                    st.rerun()

    # video player
    with col_video:
        full_path = os.path.join(Config.creator_folder(post.user), media.file_path)

        if os.path.exists(full_path):
            with st.container(key=f"container_{media.post_id}_{idx}"):
                components.html(video_html(full_path), height=320)
        else:
            st.error(f"Video not found: {full_path}")
