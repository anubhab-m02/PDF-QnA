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
    profile_tab, history_tab, quiz_tab = st.tabs(["Profile Info", "Chat History", "Quiz History"])
    
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
    
    with quiz_tab:
        st.subheader("Quiz History")
        
        # Get user's quiz history
        quiz_history = profile_service.get_user_quiz_history(username)
        
        if not quiz_history:
            st.info("You haven't taken any quizzes yet. Go to the Quiz Mode to test your knowledge!")
        else:
            # Display quiz history in a table
            st.write(f"You have taken {len(quiz_history)} quizzes.")
            
            # Create a dataframe for the quiz history
            import pandas as pd
            
            # Convert quiz history to a dataframe
            quiz_data = []
            for quiz_id, quiz_date, score, total_questions, topic in quiz_history:
                score_percentage = (score / total_questions) * 100
                quiz_data.append({
                    "Quiz ID": quiz_id,
                    "Date": quiz_date,
                    "Topic": topic if topic else "General",
                    "Score": f"{score}/{total_questions} ({score_percentage:.1f}%)",
                    "Performance": score_percentage
                })
            
            df = pd.DataFrame(quiz_data)
            
            # Function to color rows based on performance
            def color_rows(row):
                performance = float(row["Score"].split("(")[1].split("%")[0])
                if performance >= 80:
                    return ['background-color: rgba(0, 255, 0, 0.2)'] * len(row)
                elif performance >= 50:
                    return ['background-color: rgba(255, 255, 0, 0.2)'] * len(row)
                else:
                    return ['background-color: rgba(255, 0, 0, 0.2)'] * len(row)
            
            # Apply styling and display the table
            # Use a copy of the dataframe without dropping any columns
            display_df = df.drop(columns=["Performance"])
            styled_df = display_df.style.apply(color_rows, axis=1)
            st.dataframe(styled_df, use_container_width=True)
            
            # Add a section for viewing quiz details
            st.subheader("Quiz Details")
            
            # Let user select a quiz to view details
            selected_quiz = st.selectbox(
                "Select a quiz to view details:",
                options=[f"Quiz {q[0]}: {q[4] if q[4] else 'General'} - {q[1]}" for q in quiz_history],
                key="quiz_selector"
            )
            
            if selected_quiz:
                # Extract quiz ID from the selection
                quiz_id = int(selected_quiz.split(":")[0].replace("Quiz ", ""))
                
                # Get quiz details
                quiz_details = profile_service.get_quiz_details(quiz_id)
                
                if quiz_details:
                    st.write(f"**Topic:** {quiz_details['topic'] if quiz_details['topic'] else 'General'}")
                    st.write(f"**Date:** {quiz_details['quiz_date']}")
                    st.write(f"**Score:** {quiz_details['score']}/{quiz_details['total_questions']} ({(quiz_details['score']/quiz_details['total_questions'])*100:.1f}%)")
                    
                    # Display questions and answers
                    st.write("**Questions and Answers:**")
                    
                    for i, question in enumerate(quiz_details['questions']):
                        with st.expander(f"Question {i+1}: {question['question']}"):
                            # Display options
                            for j, option in enumerate(question['options']):
                                option_letter = chr(65 + j)  # A, B, C, D
                                
                                # Determine if this option was selected by the user
                                user_selected = False
                                if i < len(quiz_details['user_answers']):
                                    user_selected = quiz_details['user_answers'][i] == option_letter
                                
                                # Determine if this is the correct answer
                                is_correct = question['correct_answer'] == option_letter
                                
                                # Style the option based on correctness and selection
                                if is_correct and user_selected:
                                    st.markdown(f"✅ **{option_letter}) {option}** (Your correct answer)")
                                elif is_correct:
                                    st.markdown(f"✅ **{option_letter}) {option}** (Correct answer)")
                                elif user_selected:
                                    st.markdown(f"❌ **{option_letter}) {option}** (Your incorrect answer)")
                                else:
                                    st.markdown(f"{option_letter}) {option}")
                    
                    # Generate personalized learning path based on this quiz
                    from ui.components import suggest_learning_paths
                    
                    quiz_performance = (quiz_details['score'] / quiz_details['total_questions']) * 100
                    learning_path = suggest_learning_paths(
                        quiz_performance, 
                        quiz_details['questions'], 
                        quiz_details['user_answers']
                    )
                    
                    st.write("**Personalized Learning Path:**")
                    st.info(learning_path)
                else:
                    st.error("Failed to retrieve quiz details.")
            
            # Add a section for overall performance analysis
            st.subheader("Performance Analysis")
            
            # Calculate average score from the score percentages extracted from the quiz data
            if df.empty:
                avg_score = 0
            else:
                # Extract performance percentages from the Score column
                performance_values = [float(d["Score"].split("(")[1].split("%")[0]) for d in quiz_data]
                avg_score = sum(performance_values) / len(performance_values)
            
            # Display overall stats
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Quizzes", len(quiz_history))
            with col2:
                st.metric("Average Score", f"{avg_score:.1f}%")
            
            # Create a simple bar chart of quiz scores over time
            if len(quiz_data) > 1:
                # Extract performance percentages for the chart
                performance_values = [float(d["Score"].split("(")[1].split("%")[0]) for d in quiz_data]
                
                chart_data = pd.DataFrame({
                    "Quiz": [f"Quiz {i+1}" for i in range(len(quiz_data))],
                    "Score (%)": performance_values
                })
                
                st.bar_chart(chart_data.set_index("Quiz")["Score (%)"])
                
                # Add trend analysis
                recent_scores = performance_values[:3]
                avg_recent = sum(recent_scores) / len(recent_scores)
                
                if avg_recent > avg_score:
                    st.success("Your recent quiz performance is improving! Keep up the good work.")
                elif avg_recent < avg_score:
                    st.warning("Your recent quiz performance has been declining. Consider reviewing the suggested learning paths.")
                else:
                    st.info("Your quiz performance has been consistent. Keep practicing to improve!")
    
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
