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
        st.subheader("Login/Signup")
        create_usertable()
        choice = st.radio("Login or Signup", ["Login", "Signup"])
        if choice == "Login":
            username = st.text_input("Username")
            password = st.text_input("Password", type='password')
            if st.button("Login"):
                if login_user(username, password):
                    st.success("Logged in as {}".format(username))
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    logger.info(f"User {username} logged in successfully.")
                else:
                    st.warning("Incorrect username/password")
                    logger.warning(f"Failed login attempt for user {username}.")
        elif choice == "Signup":
            username = st.text_input("Username")
            password = st.text_input("Password", type='password')
            confirm_password = st.text_input("Confirm Password", type='password')
            if st.button("Signup"):
                if password == confirm_password:
                    if add_userdata(username, password):
                        st.success("You have successfully created an account")
                        st.info("Go to the Login tab to login")
                        logger.info(f"New user {username} registered successfully.")
                    else:
                        st.error("Error creating account. Please try again.")
                else:
                    st.warning("Passwords don't match")
                    logger.warning("Password mismatch during signup.")