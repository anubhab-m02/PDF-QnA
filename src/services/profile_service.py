import sqlite3
import streamlit as st
import os
import json
from utils.logging_config import logger

class ProfileService:
    def __init__(self):
        """Initialize the ProfileService class."""
        self.db_path = self._get_db_path()
        self.create_chat_history_table()
        self.create_quiz_history_table()
    
    def _get_db_path(self):
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
    
    def create_chat_history_table(self):
        """Create a table for storing user chat history if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
            CREATE TABLE IF NOT EXISTS chat_history(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                project_name TEXT,
                chat_content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            conn.commit()
            conn.close()
            logger.info("Chat history table created successfully.")
        except Exception as e:
            logger.error(f"Error creating chat history table: {str(e)}")
    
    def create_quiz_history_table(self):
        """Create a table for storing user quiz history if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
            CREATE TABLE IF NOT EXISTS quiz_history(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                quiz_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                score REAL,
                total_questions INTEGER,
                questions TEXT,
                user_answers TEXT,
                topic TEXT
            )
            ''')
            conn.commit()
            conn.close()
            logger.info("Quiz history table created successfully.")
        except Exception as e:
            logger.error(f"Error creating quiz history table: {str(e)}")
    
    def save_chat_history(self, username, project_name, chat_content):
        """Save a chat session to the database."""
        if not username:
            logger.error("Username is empty, cannot save chat history.")
            return False
            
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Check if there's an existing project with the same name for this user
            c.execute('SELECT id FROM chat_history WHERE username = ? AND project_name = ?', 
                     (username, project_name))
            existing = c.fetchone()
            
            if existing:
                # Update existing project
                c.execute('UPDATE chat_history SET chat_content = ?, timestamp = CURRENT_TIMESTAMP WHERE id = ?', 
                         (chat_content, existing[0]))
                logger.info(f"Updated existing chat history for user {username} with project name {project_name}")
            else:
                # Insert new project
                c.execute('INSERT INTO chat_history(username, project_name, chat_content) VALUES (?,?,?)', 
                         (username, project_name, chat_content))
                logger.info(f"Created new chat history for user {username} with project name {project_name}")
                
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving chat history: {str(e)}")
            return False
    
    def get_user_projects(self, username):
        """Get all projects for a specific user."""
        if not username:
            logger.error("Username is empty, cannot retrieve projects.")
            return []
            
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('SELECT id, project_name, timestamp FROM chat_history WHERE username = ? ORDER BY timestamp DESC', (username,))
            projects = c.fetchall()
            conn.close()
            return projects
        except Exception as e:
            logger.error(f"Error retrieving user projects: {str(e)}")
            return []
    
    def get_chat_history(self, project_id):
        """Get the chat history for a specific project."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('SELECT chat_content FROM chat_history WHERE id = ?', (project_id,))
            result = c.fetchone()
            conn.close()
            if result:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error retrieving chat history: {str(e)}")
            return None
    
    def delete_project(self, project_id):
        """Delete a project from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('DELETE FROM chat_history WHERE id = ?', (project_id,))
            conn.commit()
            conn.close()
            logger.info(f"Project {project_id} deleted successfully.")
            return True
        except Exception as e:
            logger.error(f"Error deleting project: {str(e)}")
            return False
    
    def save_quiz_result(self, username, score, total_questions, questions, user_answers, topic=""):
        """
        Save quiz results to the database.
        
        Args:
            username (str): The username of the user
            score (float): The score achieved in the quiz
            total_questions (int): Total number of questions in the quiz
            questions (list): List of question dictionaries
            user_answers (list): List of user's answers
            topic (str, optional): The topic of the quiz
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not username:
            logger.error("Username is empty, cannot save quiz results.")
            return False
            
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Convert questions and answers to JSON strings for storage
            questions_json = json.dumps(questions)
            answers_json = json.dumps(user_answers)
            
            c.execute('''
            INSERT INTO quiz_history(username, score, total_questions, questions, user_answers, topic) 
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, score, total_questions, questions_json, answers_json, topic))
            
            conn.commit()
            conn.close()
            logger.info(f"Saved quiz results for user {username}")
            return True
        except Exception as e:
            logger.error(f"Error saving quiz results: {str(e)}")
            return False
    
    def get_user_quiz_history(self, username):
        """
        Get quiz history for a specific user.
        
        Args:
            username (str): The username of the user
            
        Returns:
            list: List of quiz history records
        """
        if not username:
            logger.error("Username is empty, cannot retrieve quiz history.")
            return []
            
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
            SELECT id, quiz_date, score, total_questions, topic 
            FROM quiz_history 
            WHERE username = ? 
            ORDER BY quiz_date DESC
            ''', (username,))
            
            quiz_history = c.fetchall()
            conn.close()
            return quiz_history
        except Exception as e:
            logger.error(f"Error retrieving user quiz history: {str(e)}")
            return []
    
    def get_quiz_details(self, quiz_id):
        """
        Get detailed information about a specific quiz.
        
        Args:
            quiz_id (int): The ID of the quiz
            
        Returns:
            dict: Quiz details including questions and answers
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
            SELECT username, quiz_date, score, total_questions, questions, user_answers, topic 
            FROM quiz_history 
            WHERE id = ?
            ''', (quiz_id,))
            
            result = c.fetchone()
            conn.close()
            
            if result:
                username, quiz_date, score, total_questions, questions_json, answers_json, topic = result
                
                # Parse JSON strings back to Python objects
                questions = json.loads(questions_json)
                user_answers = json.loads(answers_json)
                
                return {
                    "username": username,
                    "quiz_date": quiz_date,
                    "score": score,
                    "total_questions": total_questions,
                    "questions": questions,
                    "user_answers": user_answers,
                    "topic": topic
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving quiz details: {str(e)}")
            return None
    
    def get_previously_asked_questions(self, username):
        """
        Get all questions previously asked to a user.
        
        Args:
            username (str): The username of the user
            
        Returns:
            list: List of previously asked questions
        """
        if not username:
            logger.error("Username is empty, cannot retrieve previously asked questions.")
            return []
            
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('SELECT questions FROM quiz_history WHERE username = ?', (username,))
            
            results = c.fetchall()
            conn.close()
            
            all_questions = []
            for result in results:
                questions_json = result[0]
                questions = json.loads(questions_json)
                all_questions.extend(questions)
                
            return all_questions
        except Exception as e:
            logger.error(f"Error retrieving previously asked questions: {str(e)}")
            return []

# Create singleton instance
profile_service = ProfileService()
