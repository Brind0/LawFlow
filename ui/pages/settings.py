import streamlit as st
from config.settings import settings

def render(conn):
    st.title("Settings")
    
    st.subheader("Configuration")
    st.text_input("Notion Token", value=settings.NOTION_TOKEN, type="password", disabled=True)
    st.caption("Set via .env file")
    
    st.subheader("Database")
    st.write(f"Path: `{settings.DATABASE_PATH}`")
