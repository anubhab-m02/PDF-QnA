import streamlit as st
from passlib.hash import pbkdf2_sha256
import sqlite3
import os
from utils.logging_config import logger

def get_db_path():
    """Get the path to the users.db file."""
    # Check if the file exists in the current directory
    if os.path.exists('users.db'):
        return 'users.db'
    # Check if the file exists in the src directory
    elif os.path.exists('src/users.db'):
        return 'src/users.db'
    # Default to the root directory
    else:
        return 'users.db'

def create_usertable():
    """Create a table for users if it doesn't exist."""
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT, password TEXT)')
        conn.commit()
        conn.close()
        logger.info("User table created successfully.")
    except Exception as e:
        logger.error(f"Error creating user table: {str(e)}")

def add_userdata(username, password):
    """Add a new user to the database."""
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        # Hash the password before storing
        hashed_password = pbkdf2_sha256.hash(password)
        c.execute('INSERT INTO userstable(username,password) VALUES (?,?)', (username, hashed_password))
        conn.commit()
        conn.close()
        logger.info(f"User {username} added successfully.")
        return True
    except Exception as e:
        logger.error(f"Error adding user: {str(e)}")
        return False

def login_user(username, password):
    """Check if the provided username and password match a user in the database."""
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM userstable WHERE username =?', (username,))
        data = c.fetchone()
        conn.close()
        if data:
            # Verify password against the stored hash
            return pbkdf2_sha256.verify(password, data[1])
        else:
            return False
    except Exception as e:
        logger.error(f"Error logging in user: {str(e)}")
        return False

class Authentication:
    """Authentication class for handling login and signup."""
    
    def __init__(self):
        """Initialize the Authentication class."""
        # No Streamlit commands here, just initialization
        pass
        
    def login(self):
        """Streamlit login/signup form."""
        # Create a centered layout
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # App logo and title
            st.title("📚 Learning Assistant")
            st.subheader("Welcome to your AI-Powered Learning Tool")
            
            # Create the user table if it doesn't exist
            create_usertable()
            
            # Login/Signup tabs
            tab1, tab2 = st.tabs(["Login", "Sign Up"])
            
            with tab1:
                st.header("Login to Your Account")
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type='password', key="login_password")
                
                remember_me = st.checkbox("Remember me")
                
                login_button = st.button("Login", use_container_width=True)
                
                if login_button:
                    if username and password:  # Basic validation
                        if login_user(username, password):
                            st.success("Login successful!")
                            st.session_state["authenticated"] = True
                            st.session_state["username"] = username
                            logger.info(f"User {username} logged in successfully.")
                            
                            # Add a spinner to show loading before redirect
                            with st.spinner("Redirecting to dashboard..."):
                                import time
                                time.sleep(1)  # Brief pause for UX
                                st.rerun()
                        else:
                            st.error("Incorrect username or password")
                            logger.warning(f"Failed login attempt for user {username}.")
                    else:
                        st.warning("Please enter both username and password")
            
            with tab2:
                st.header("Create a New Account")
                new_username = st.text_input("Choose a Username", key="signup_username")
                new_password = st.text_input("Create Password", type='password', key="signup_password")
                confirm_password = st.text_input("Confirm Password", type='password', key="confirm_password")
                
                # Password strength indicator
                if new_password:
                    strength = self._check_password_strength(new_password)
                    if strength == "weak":
                        st.warning("Password is weak. Consider using a stronger password.")
                    elif strength == "medium":
                        st.info("Password strength: Medium")
                    else:
                        st.success("Password strength: Strong")
                
                signup_button = st.button("Create Account", use_container_width=True)
                
                if signup_button:
                    if new_username and new_password and confirm_password:  # Basic validation
                        if new_password == confirm_password:
                            if self._check_password_strength(new_password) != "weak":
                                if add_userdata(new_username, new_password):
                                    st.success("Account created successfully!")
                                    st.info("Please go to the Login tab to sign in.")
                                    logger.info(f"New user {new_username} registered successfully.")
                                else:
                                    st.error("Error creating account. Please try again.")
                            else:
                                st.error("Please use a stronger password")
                        else:
                            st.error("Passwords don't match")
                            logger.warning("Password mismatch during signup.")
                    else:
                        st.warning("Please fill in all fields")
            
    
    def _check_password_strength(self, password):
        """Check the strength of a password."""
        # Simple password strength checker
        if len(password) < 8:
            return "weak"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        # Count the criteria met
        criteria_met = sum([has_upper, has_lower, has_digit, has_special])
        
        if criteria_met >= 3 and len(password) >= 10:
            return "strong"
        elif criteria_met >= 2 and len(password) >= 8:
            return "medium"
        else:
            return "weak"
    
    def logout(self):
        """Log out the user and clear session state."""
        
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Set authenticated to False
        st.session_state.authenticated = False
        
        from utils.logging_config import logger
        logger.info("User logged out successfully.")
        return True