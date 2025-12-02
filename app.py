import streamlit as st
from ui.pages import dashboard, topic, settings
from ui.components.sidebar import render_sidebar
from database.connection import get_connection

# Page config
st.set_page_config(
    page_title="LawFlow",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if 'current_module_id' not in st.session_state:
    st.session_state.current_module_id = None
if 'current_topic_id' not in st.session_state:
    st.session_state.current_topic_id = None
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'dashboard'

# Initialize database connection
# We use the context manager to get a connection, but for the app lifecycle
# we might want to pass a connection object or re-open it per request.
# Streamlit reruns the script on every interaction.
# For simplicity in Sprint 1, we'll open a connection at the start of the script
# and pass it down. In a real production app, we might use st.cache_resource for the connection pool.

# Using the context manager directly in the render functions is safer for SQLite locking.
# However, the sidebar needs it too.
# Let's use a pattern where we pass the connection factory or just use the context manager inside functions.
# But the PRD architecture diagram showed passing `conn`.
# Let's stick to the PRD's implication but adapt for safety:
# We will use the context manager here to ensure the DB is initialized,
# then pass the context manager or just let components call get_connection().
# Actually, passing `conn` implies an open connection.
# Let's open one for this run.

with get_connection() as conn:
    # Render sidebar (always visible)
    render_sidebar(conn)

    # Route to appropriate page
    if st.session_state.current_view == 'dashboard':
        dashboard.render(conn)
    elif st.session_state.current_view == 'topic':
        # Ensure we have a topic ID
        if st.session_state.current_topic_id:
            topic.render(conn, st.session_state.current_topic_id)
        else:
            st.error("No topic selected!")
            st.session_state.current_view = 'dashboard'
            st.rerun()
    elif st.session_state.current_view == 'settings':
        settings.render(conn)
