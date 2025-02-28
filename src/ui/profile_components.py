import streamlit as st
import json
from services.profile_service import profile_service
from auth.authentication import Authentication
import datetime

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
        
        # Create a more attractive profile button
        username = st.session_state.get('username', 'Profile')
        
        # Style the profile button to make it more prominent
        profile_container.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 10px;">
                <div style="display: inline-block; border-radius: 50%; width: 40px; height: 40px; 
                     line-height: 40px; text-align: center; margin-right: 10px; font-size: 20px; border: 1px solid #ddd;">
                    👤
                </div>
                <span style="font-weight: bold; font-size: 16px;">{username}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Add the actual button but make it look like a link
        col1, col2, col3 = profile_container.columns([1, 2, 1])
        with col2:
            if st.button("View Profile", key="profile_btn", type="primary", use_container_width=True):
                st.session_state.show_profile = True
            
        profile_container.markdown("---")  # Add a separator line

def profile_page():
    """Display the user profile page."""
    # Create a more attractive header with user info
    username = st.session_state.get('username', 'User')
    
    # Header with user avatar and name
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; margin-bottom: 20px;">
            <div style="border-radius: 50%; width: 80px; height: 80px; border: 1px solid #ddd;
                 line-height: 80px; text-align: center; margin-right: 20px; font-size: 40px;">
                👤
            </div>
            <div>
                <h1 style="margin-bottom: 0;">{username}</h1>
                <p style="margin-top: 0;">User Profile</p>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Add tabs for different sections
    profile_tab, history_tab = st.tabs(["Profile Info", "Chat History"])
    
    with profile_tab:
        st.subheader("Account Information")
        
        # Display when the account was created (placeholder)
        st.info(f"Account created: {datetime.datetime.now().strftime('%B %d, %Y')}")
        
        # Add some statistics
        col1, col2 = st.columns(2)
        with col1:
            # Count the number of chat sessions
            projects = profile_service.get_user_projects(username)
            st.metric("Saved Chats", len(projects) if projects else 0)
        with col2:
            # This could be replaced with actual data in the future
            st.metric("Documents Processed", "5")
    
    with history_tab:
        st.subheader("Your Chat History")
        projects = profile_service.get_user_projects(username)
        
        if not projects:
            # Display a message if no projects are found
            st.info("No saved chat sessions found.")
        else:
            # Create a more organized display for projects
            for i, project in enumerate(projects):
                project_id = project[0]
                project_name = project[1]
                timestamp = project[2] if len(project) > 2 else "Unknown"
                
                # Create a card-like appearance for each project
                st.markdown(
                    f"""
                    <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                        <h3 style="margin-top: 0;">{project_name}</h3>
                        <p style="font-size: 14px;">Created: {timestamp}</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                # Create an expander for the chat content
                with st.expander("View Chat Content"):
                    # Get the chat content for this project
                    chat_content = profile_service.get_chat_history(project_id)
                    if chat_content:
                        try:
                            chat_data = json.loads(chat_content)
                            
                            # Display a preview of the chat
                            for j, message in enumerate(chat_data):
                                if j < 3:  # Show only first 3 messages as preview
                                    st.write(f"**{message['role'].capitalize()}**: {message['content'][:150]}..." if len(message['content']) > 150 else f"**{message['role'].capitalize()}**: {message['content']}")
                            
                            if len(chat_data) > 3:
                                st.write(f"*...and {len(chat_data) - 3} more messages*")
                            
                            # Action buttons
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Delete", key=f"delete_{i}"):
                                    profile_service.delete_project(project_id)
                                    st.success(f"Deleted chat: {project_name}")
                                    st.rerun()
                            with col2:
                                if st.button("Load", key=f"load_{i}"):
                                    st.session_state.messages = chat_data
                                    st.session_state.show_profile = False
                                    st.success(f"Loaded chat: {project_name}")
                                    st.rerun()
                        except Exception as e:
                            from utils.logging_config import logger
                            logger.error(f"Error displaying chat history: {str(e)}")
                            st.error("Could not load chat history.")
    
    # Add a footer with action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("← Back to App", type="primary", use_container_width=True):
            st.session_state.show_profile = False
            st.rerun()
    with col2:
        if st.button("Logout", type="secondary", use_container_width=True):
            # Use the Authentication class logout method
            auth = Authentication()
            auth.logout()
            st.rerun()

def save_current_chat():
    """Save the current chat session."""
    if 'messages' in st.session_state and len(st.session_state.messages) > 0:
        st.markdown("""
        <div style="border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px;">
            <h2>Save Your Chat Session</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate a default project name based on PDFs if available
        default_name = "Chat Session"
        if 'pdf_docs' in st.session_state and st.session_state.pdf_docs:
            pdf_names = [pdf.name for pdf in st.session_state.pdf_docs]
            default_name = f"Chat about {', '.join(pdf_names[:2])}"
            if len(pdf_names) > 2:
                default_name += f" and {len(pdf_names) - 2} more"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        default_name = f"{default_name} ({timestamp})"
        
        # Create a form-like appearance
        st.markdown("""
        <div style="padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #ddd;">
            <p style="margin-bottom: 10px;">Give your chat session a name to easily find it later.</p>
        </div>
        """, unsafe_allow_html=True)
        
        project_name = st.text_input("Project Name:", value=default_name)
        
        # Display a preview of the chat in a card-like container
        st.markdown("""
        <h3 style="margin-top: 20px; margin-bottom: 10px;">Chat Preview</h3>
        <div style="border: 1px solid #ddd; border-radius: 5px; padding: 15px; max-height: 300px; overflow-y: auto;">
        """, unsafe_allow_html=True)
        
        # Show a limited preview
        preview_count = min(5, len(st.session_state.messages))
        for i, message in enumerate(st.session_state.messages[:preview_count]):
            role_color = "#0068c9" if message["role"] == "assistant" else "#464e5f"
            st.markdown(
                f"""
                <div style="margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #eee;">
                    <strong style="color: {role_color};">{message['role'].capitalize()}</strong>: 
                    {message['content'][:100]}{"..." if len(message['content']) > 100 else ""}
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        if len(st.session_state.messages) > preview_count:
            st.markdown(
                f"""
                <div style="text-align: center; padding: 10px;">
                    <em>...and {len(st.session_state.messages) - preview_count} more messages</em>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Add a save button with better styling
        if st.button("Save Chat History", type="primary", use_container_width=True) and project_name:
            chat_content = json.dumps(st.session_state.messages)
            username = st.session_state.get('username', '')
            
            if username:
                profile_service.save_chat_history(username, project_name, chat_content)
                st.success(f"Chat saved as: {project_name}")
            else:
                st.error("You must be logged in to save chat history.")
    else:
        st.info("No chat messages to save. Start a conversation first!")
