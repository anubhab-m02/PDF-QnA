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
from utils.cleanup import cleanup_old_data
from utils.logging_config import logger
import google.generativeai as genai
from config.settings import GOOGLE_API_KEY

# Import the required functions from the document_processor service
from services.document_processor import get_pdf_text, get_text_chunks, update_vector_store
from services.ai_service import ai_service
from services.quiz_service import quiz_service
from services.flashcard_service import flashcard_service, flashcard_interface
from services.translation_service import translation_service
from services.sharing_service import sharing_service
from services.text_complexity_service import analyze_text_complexity, visualize_text_complexity
from services.key_concepts_service import extract_key_concepts
from services.text_summary_service import summarize_document
from services.text_translation_service import TranslationService
from services.speech_service import speech_service

# Load environment variables
load_dotenv()

# Configure genai with the API key
genai.configure(api_key=GOOGLE_API_KEY)

def main():
    cleanup_old_data()
    st.set_page_config(page_title="AI-Powered Personalized Learning Assistant", layout="wide")
    
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
                                "Share Document", "Analyze Text Complexity", "Extract Key Concepts", "Text to Speech"])

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
                    
                    with chat_container:
                        with st.chat_message("assistant"):
                            st.markdown(response['output_text'])
            else:
                with chat_container:
                    with st.chat_message("assistant"):
                        st.warning("Please upload and process documents before asking questions.")
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.experimental_rerun()

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
        share_document = st.button("Share Document")
        if share_document:
            recipient_email = st.text_input("Enter recipient email:")
            if recipient_email:
                with st.spinner("Sharing document..."):
                    result = sharing_service.send_document(st.session_state.pdf_docs, recipient_email)
                    if "successfully" in result:
                        st.success(result)
                    else:
                        st.error(result)
            else:
                st.warning("Please enter a valid email address.")

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

if __name__ == "__main__":
    main()
