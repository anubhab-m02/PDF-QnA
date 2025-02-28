import streamlit as st
import json
from services.profile_service import profile_service

def profile_button():
    """Display the profile button in the sidebar."""
    if 'username' not in st.session_state and st.session_state.authenticated:
        # Get the username from the database
        import sqlite3
        import os
        
        # Get the database path
        db_path = 'users.db'
        if os.path.exists('src/users.db'):
            db_path = 'src/users.db'
            
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            # Get the username of the currently logged in user from the session state
            if 'username' in st.session_state:
                username = st.session_state.username
                c.execute('SELECT username FROM userstable WHERE username = ?', (username,))
            else:
                # Fallback to getting the first user if no username in session state
                c.execute('SELECT username FROM userstable LIMIT 1')
                
            result = c.fetchone()
            conn.close()
            if result:
                st.session_state.username = result[0]
            else:
                st.session_state.username = "User"
        except Exception as e:
            from utils.logging_config import logger
            logger.error(f"Error retrieving username: {str(e)}")
            st.session_state.username = "User"
    
    # Display the profile button with the username
    if st.session_state.authenticated:
        # Use a container to style the button
        profile_container = st.sidebar.container()
        profile_container.markdown("---")  # Add a separator line
        if profile_container.button(f"👤 {st.session_state.get('username', 'Profile')}", key="profile_btn"):
            st.session_state.show_profile = True
        profile_container.markdown("---")  # Add a separator line

def profile_page():
    """Display the user profile page."""
    st.title(f"Profile: {st.session_state.get('username', 'User')}")
    
    
    
    # User's projects
    st.header("Your Chat History")
    projects = profile_service.get_user_projects(st.session_state.get('username', ''))
    
    if not projects:
        st.info("You haven't saved any chat sessions yet.")
    else:
        # Display projects in a more organized way
        for project in projects:
            project_id, project_name, timestamp = project
            
            # Create an expander for each project
            with st.expander(f"**{project_name}** - {timestamp}"):
                # Get the chat content
                chat_content = profile_service.get_chat_history(project_id)
                if chat_content:
                    try:
                        chat_data = json.loads(chat_content)
                        
                        # Display a preview of the chat
                        for i, message in enumerate(chat_data):
                            if i < 3:  # Show only first 3 messages as preview
                                st.write(f"**{message['role'].capitalize()}**: {message['content'][:150]}..." if len(message['content']) > 150 else f"**{message['role'].capitalize()}**: {message['content']}")
                        
                        if len(chat_data) > 3:
                            st.write(f"*...and {len(chat_data) - 3} more messages*")
                        
                        # Action buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Load Chat", key=f"load_{project_id}"):
                                st.session_state.messages = chat_data
                                st.session_state.show_profile = False
                                st.rerun()
                        with col2:
                            if st.button("Delete", key=f"delete_{project_id}"):
                                if profile_service.delete_project(project_id):
                                    st.success("Project deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete project.")
                    except Exception as e:
                        from utils.logging_config import logger
                        logger.error(f"Error displaying chat history: {str(e)}")
                        st.error("Could not load chat history.")
    # Back and Logout buttons in the same row
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("← Back"):
            st.session_state.show_profile = False
            st.rerun()
    with col2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.show_profile = False
            st.rerun()

def save_current_chat():
    """Save the current chat session."""
    if 'messages' in st.session_state and st.session_state.messages:
        st.subheader("Save Current Chat Session")
        
        # Generate a default project name based on PDFs if available
        default_name = "Chat Session"
        if 'pdf_docs' in st.session_state and st.session_state.pdf_docs:
            pdf_names = [pdf.name for pdf in st.session_state.pdf_docs]
            default_name = f"Chat about {', '.join(pdf_names[:2])}"
            if len(pdf_names) > 2:
                default_name += f" and {len(pdf_names) - 2} more"
        
        # Add timestamp to make the name unique
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        default_name = f"{default_name} ({timestamp})"
        
        project_name = st.text_input("Project Name:", value=default_name)
        
        # Display a preview of the chat
        st.subheader("Chat Preview")
        for message in st.session_state.messages:
            st.write(f"**{message['role'].capitalize()}**: {message['content'][:100]}..." if len(message['content']) > 100 else f"**{message['role'].capitalize()}**: {message['content']}")
        
        if st.button("Save Chat History") and project_name:
            chat_content = json.dumps(st.session_state.messages)
            username = st.session_state.get('username', '')
            
            if username and profile_service.save_chat_history(username, project_name, chat_content):
                st.success("Chat history saved successfully!")
                
                # Generate a new chat ID for future auto-saves
                import time
                st.session_state.current_chat_id = f"chat_{int(time.time())}"
            else:
                st.error("Failed to save chat history. Make sure you're logged in.")
