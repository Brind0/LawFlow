import streamlit as st
from database.repositories.topic_repo import TopicRepository
from database.repositories.module_repo import ModuleRepository
from ui.components.vault import render_vault
from ui.components.stage_cards import render_stage_cards
from ui.components.generation_modal import show_generation_modal
from config.settings import settings

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
        st.header("AI Generation Pipeline")
        st.markdown("""
        Generate structured notes from your uploaded content using AI:
        - **MK-1**: Foundation notes from lecture slides
        - **MK-2**: Tutorial prep with detailed analysis
        - **MK-3**: Exam revision master document
        """)

        # Render stage cards
        clicked_stage = render_stage_cards(
            topic_id=topic.id,
            module_name=module.name,
            conn=conn
        )

        # If user clicked Generate/Regenerate, show modal
        if clicked_stage:
            # Show generation modal (database ID fetched from module)
            success = show_generation_modal(
                topic_id=topic.id,
                stage=clicked_stage,
                module_name=module.name,
                conn=conn
            )

            # If generation completed, celebrate and refresh
            if success:
                st.balloons()
                st.rerun()
