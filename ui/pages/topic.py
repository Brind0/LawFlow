import streamlit as st
from database.repositories.topic_repo import TopicRepository
from database.repositories.module_repo import ModuleRepository
from ui.components.vault import render_vault

def render(conn, topic_id: str):
    topic_repo = TopicRepository(conn)
    module_repo = ModuleRepository(conn)
    topic = topic_repo.get_by_id(topic_id)
    if not topic:
        st.error("Topic not found!")
        return
        
    module = module_repo.get_by_id(topic.module_id)
    
    st.title(f"{module.name} / {topic.name}")
    
    # Layout: Vault on top (or side), Generations below
    # For now, let's put Vault in a tab or just top section
    
    tab1, tab2 = st.tabs(["📚 Content Vault", "✨ Generations"])
    
    with tab1:
        render_vault(conn, module, topic)
        
    with tab2:
        st.header("Generations")
        st.info("Generation features coming in Sprint 5!")
