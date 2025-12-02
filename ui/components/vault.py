import streamlit as st
import humanize
from services.content_service import ContentService
from database.models import ContentType

def render_vault(conn, module, topic):
    """
    Renders the Content Vault for a specific topic.
    """
    st.subheader("📂 Content Vault")
    
    service = ContentService(conn)
    
    # --- File Uploader ---
    with st.expander("Upload New Content", expanded=False):
        uploaded_file = st.file_uploader(
            "Choose a file", 
            type=['pdf', 'txt'],
            help="Upload lecture slides (PDF) or transcripts (TXT)"
        )
        
        if uploaded_file is not None:
            if st.button("Upload & Process", type="primary"):
                with st.spinner("Uploading to Drive..."):
                    try:
                        service.upload_content(
                            file_obj=uploaded_file,
                            filename=uploaded_file.name,
                            topic_id=topic.id,
                            module_name=module.name,
                            topic_name=topic.name
                        )
                        st.success(f"Successfully uploaded {uploaded_file.name}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Upload failed: {str(e)}")

    # --- Content List ---
    content_items = service.get_topic_content(topic.id)
    
    if not content_items:
        st.info("No content uploaded yet. Upload slides to get started!")
    else:
        for item in content_items:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    icon = "📄" if item.content_type == ContentType.LECTURE_PDF else "📝"
                    st.markdown(f"**{icon} {item.file_name}**")
                    
                with col2:
                    st.caption(f"{humanize.naturalsize(item.file_size_bytes)}")
                    
                with col3:
                    st.caption(f"Uploaded {humanize.naturaltime(item.uploaded_at)}")
                    
                with col4:
                    # Actions
                    if item.drive_url:
                        st.markdown(f"[View]({item.drive_url})")
                    
                    # Delete button (using a unique key)
                    if st.button("🗑️", key=f"del_{item.id}", help="Delete"):
                        if service.delete_content(item.id):
                            st.success("Deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete")
                
                st.divider()
