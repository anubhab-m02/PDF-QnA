import streamlit as st
from dotenv import load_dotenv
from ui.components import (
    sidebar_components,
    chat_interface,
    quiz_interface,
    flashcard_interface,
    translation_interface,
    sharing_interface,
    analysis_interface,
    audio_interface
)
from ui.profile_components import profile_page, save_current_chat
from utils.cleanup import cleanup_old_data
from utils.logging_config import logger
import google.generativeai as genai
from config.settings import GOOGLE_API_KEY

# Import the required functions from the document_processor service
from services.document_processor import get_pdf_text, get_text_chunks, update_vector_store
from services.ai_service import ai_service
from services.quiz_service import quiz_service
from services.flashcard_service import flashcard_service
from services.translation_service import translation_service
from services.sharing_service import sharing_service
from services.text_complexity_service import analyze_text_complexity, visualize_text_complexity
from services.key_concepts_service import extract_key_concepts
from services.text_summary_service import summarize_document
from services.text_translation_service import TranslationService
from services.speech_service import speech_service
from services.profile_service import profile_service
from auth.authentication import Authentication

# Load environment variables
load_dotenv()

# Configure genai with the API key
genai.configure(api_key=GOOGLE_API_KEY)

# Set page config at the top level, before any other Streamlit commands
st.set_page_config(page_title="AI-Powered Personalized Learning Assistant", layout="wide")

auth = Authentication()

def main():
    cleanup_old_data()
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'show_profile' not in st.session_state:
        st.session_state.show_profile = False
    
    if not st.session_state.authenticated:
        auth.login()
        if st.session_state.authenticated:
            st.success("Login successful!")
            st.rerun()  # Rerun to show the app
        else:
            return  # Don't show the app if not authenticated
    
    # Show profile page if requested
    if st.session_state.show_profile:
        profile_page()
        return
    
    st.header("AI-Powered Personalized Learning Assistant")
    
    # Information box below the header
    st.info("""
    Welcome to your AI-Powered Learning Assistant! This application helps you:
    - Upload and process PDF documents
    - Ask questions about the uploaded content
    - Take quizzes to test your knowledge
    - Generate summaries and flashcards
    - Translate text to different languages
    - Analyze text complexity and extract key concepts
    - Convert text to speech (Still Work in Progress)
    
    Get started by uploading your documents in the sidebar!
    """)

    with st.sidebar:
        sidebar_components()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    user_choice = st.selectbox("Choose an option:", 
                               ["Ask a question", "Take a quiz", "Summarize Document", 
                                "Generate Flashcards", "Translate Text", 
                                "Share Document", "Analyze Text Complexity", "Extract Key Concepts", "Text to Speech", "Save Chat"])

    if user_choice == "Ask a question":
        if prompt := st.chat_input("Ask a question about your documents:"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            if st.session_state.context and st.session_state.pdf_docs:
                with st.spinner("Generating response..."):
                    response = ai_service.user_input(prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response['output_text']})
                    
                    # Auto-save the chat session if it's not already saved
                    if 'pdf_docs' in st.session_state and st.session_state.pdf_docs and 'username' in st.session_state:
                        # Get the names of the PDFs to use as project name
                        pdf_names = [pdf.name for pdf in st.session_state.pdf_docs]
                        project_name = f"Chat about {', '.join(pdf_names[:2])}"
                        if len(pdf_names) > 2:
                            project_name += f" and {len(pdf_names) - 2} more"
                            
                        # Only auto-save if we have enough messages to be worth saving
                        if len(st.session_state.messages) >= 2:
                            # Generate a unique chat ID based on the current time if not already set
                            import time
                            if 'current_chat_id' not in st.session_state or st.session_state.get('chat_cleared', False):
                                st.session_state.current_chat_id = f"chat_{int(time.time())}"
                                st.session_state.chat_cleared = False
                            
                            # Save the chat history in the background
                            import json
                            chat_content = json.dumps(st.session_state.messages)
                            profile_service.save_chat_history(st.session_state.username, 
                                                             f"{project_name} ({st.session_state.current_chat_id})", 
                                                             chat_content)
                    
                with st.chat_message("assistant"):
                    st.markdown(response['output_text'])
            else:
                st.warning("Please upload and process documents before asking questions.")
        
        if st.button("Clear Chat History"):
            # Save the current chat before clearing if it has content
            if 'messages' in st.session_state and len(st.session_state.messages) >= 2:
                import json
                import time
                import datetime
                
                # Only auto-save if we have a username and PDF docs
                if 'username' in st.session_state and 'pdf_docs' in st.session_state and st.session_state.pdf_docs:
                    # Generate a project name
                    pdf_names = [pdf.name for pdf in st.session_state.pdf_docs]
                    project_name = f"Chat about {', '.join(pdf_names[:2])}"
                    if len(pdf_names) > 2:
                        project_name += f" and {len(pdf_names) - 2} more"
                    
                    # Add timestamp to make the name unique
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    project_name = f"{project_name} ({timestamp}) [Auto-saved]"
                    
                    # Save the chat history
                    chat_content = json.dumps(st.session_state.messages)
                    profile_service.save_chat_history(st.session_state.username, project_name, chat_content)
            
            # Clear the chat history
            st.session_state.messages = []
            st.session_state.chat_cleared = True
            
            # Generate a new chat ID for the next conversation
            import time
            st.session_state.current_chat_id = f"chat_{int(time.time())}"
            
            st.rerun()

    elif user_choice == "Take a quiz":
        quiz_interface()

    elif user_choice == "Summarize Document":
        context = st.session_state.get("context", "")
        if context:
            summary = summarize_document(context)
            st.write("Document Summary:")
            st.write(summary)
        else:
            st.error("No context available. Please upload and process documents first.")

    elif user_choice == "Generate Flashcards":
        flashcard_interface()

    elif user_choice == "Translate Text":
        translation_interface()

    elif user_choice == "Share Document":
        sharing_interface()

    elif user_choice == "Analyze Text Complexity":
        analysis_interface()

    elif user_choice == "Extract Key Concepts":
        context = st.session_state.get("context", "")
        if context:
            key_concepts = extract_key_concepts(context)
            st.write("Key Concepts:")
            for concept, score in key_concepts:
                st.write(f"{concept}: {score:.4f}")
        else:
            st.error("No context available. Please upload and process documents first.")

    elif user_choice == "Text to Speech":
        audio_interface()

    elif user_choice == "Save Chat":
        save_current_chat()

if __name__ == "__main__":
    main()
