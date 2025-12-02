import streamlit as st
from database.repositories.module_repo import ModuleRepository
from database.repositories.topic_repo import TopicRepository
from database.models import Module, Topic

def render_sidebar(conn):
    """Renders the application sidebar with navigation."""
    module_repo = ModuleRepository(conn)
    topic_repo = TopicRepository(conn)
    
    with st.sidebar:
        st.header("LawFlow ⚖️")
        
        # Navigation
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.current_view = 'dashboard'
            st.session_state.current_module_id = None
            st.session_state.current_topic_id = None
            st.rerun()
            
        st.divider()
        
        # Modules List
        st.subheader("Modules")
        
        modules = module_repo.get_all()
        
        for module in modules:
            with st.expander(f"📚 {module.name}", expanded=st.session_state.get('current_module_id') == module.id):
                # Topics for this module
                topics = topic_repo.get_for_module(module.id)
                
                for topic in topics:
                    # Highlight active topic
                    is_active = st.session_state.get('current_topic_id') == topic.id
                    icon = "📂" if not is_active else "📂" # Could change icon if active
                    
                    if st.button(f"{icon} {topic.name}", key=f"nav_topic_{topic.id}", use_container_width=True):
                        st.session_state.current_view = 'topic'
                        st.session_state.current_module_id = module.id
                        st.session_state.current_topic_id = topic.id
                        st.rerun()
                
                # Add Topic Button
                if st.button("➕ New Topic", key=f"add_topic_btn_{module.id}"):
                    st.session_state[f"show_topic_form_{module.id}"] = True
                
                if st.session_state.get(f"show_topic_form_{module.id}", False):
                    with st.form(f"new_topic_form_{module.id}"):
                        st.write(f"Add Topic to {module.name}")
                        topic_name = st.text_input("Topic Name")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Create"):
                                if topic_name:
                                    try:
                                        new_topic = Topic.create(module.id, topic_name)
                                        topic_repo.create(new_topic)
                                        st.success(f"Created {topic_name}!")
                                        st.session_state[f"show_topic_form_{module.id}"] = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                                else:
                                    st.warning("Name required")
                        with col2:
                            if st.form_submit_button("Cancel"):
                                st.session_state[f"show_topic_form_{module.id}"] = False
                                st.rerun()
        
        st.divider()
        
        # Add Module Button
        if st.button("➕ New Module", use_container_width=True):
            st.session_state.show_module_form = True
            
        if st.session_state.get('show_module_form', False):
             with st.form("new_module_form"):
                 st.write("Create New Module")
                 name = st.text_input("Module Name")
                 project = st.text_input("Claude Project Name")
                 
                 col1, col2 = st.columns(2)
                 with col1:
                     if st.form_submit_button("Create"):
                         if name:
                             try:
                                 new_module = Module.create(name, project)
                                 module_repo.create(new_module)
                                 st.success(f"Created {name}!")
                                 st.session_state.show_module_form = False
                                 st.rerun()
                             except Exception as e:
                                 st.error(f"Error: {e}")
                         else:
                             st.warning("Name required")
                 with col2:
                     if st.form_submit_button("Cancel"):
                         st.session_state.show_module_form = False
                         st.rerun()

        st.divider()
        
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.current_view = 'settings'
            st.rerun()
