import streamlit as st
from database.repositories.topic_repo import TopicRepository

def render(conn, topic_id: str):
    topic_repo = TopicRepository(conn)
    topic = topic_repo.get_by_id(topic_id)
    
    if not topic:
        st.error("Topic not found!")
        return

    st.title(f"Topic: {topic.name}")
    st.write("Content Vault and Generation tools coming in Sprint 2 & 3.")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Content Vault")
        st.info("Uploads will appear here.")
        
    with col2:
        st.subheader("Generations")
        st.info("Mk-1, Mk-2, Mk-3 cards will appear here.")
