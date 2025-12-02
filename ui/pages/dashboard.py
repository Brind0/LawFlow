import streamlit as st

def render(conn):
    st.title("Dashboard")
    st.info("Welcome to LawFlow! Select a module from the sidebar to get started.")
    
    # Sprint 1 Placeholder content
    st.markdown("""
    ### Getting Started
    1. Create a **Module** in the sidebar (e.g., "Land Law")
    2. Create a **Topic** under that module (e.g., "Registration")
    3. Upload your lecture slides and start generating notes!
    """)
