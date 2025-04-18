import streamlit as st
from dotenv import load_dotenv
import json
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
    
    st.markdown(
        """
        <div style="text-align: center; padding: 20px 0; margin-bottom: 20px; border-radius: 10px;">
            <h1 style="margin-bottom: 10px;">AI-Powered Personalized Learning Assistant</h1>
            <p style="font-size: 16px;">Your personalized study companion for document-based learning</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    tab1, tab2, tab3, tab4 = st.tabs(["Learn", "Test Knowledge", "Analyze", "Tools"])
    
    with tab1:
        st.markdown(
            """
            <div style="margin-bottom: 20px;">
                <h2 style="font-size: 20px; font-weight: bold; margin-bottom: 10px;">Learn from Your Documents</h2>
                <p>Ask questions, get summaries, and create flashcards from your uploaded documents.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        learn_option = st.radio(
            "Choose a learning option:",
            ["Ask a question", "Summarize Document", "Generate Flashcards"],
            horizontal=True
        )
        
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        if learn_option == "Ask a question":
            chat_container = st.container()
            with chat_container:
                st.markdown(
                    """
                    <div style="margin-bottom: 10px;">
                        <h3 style="font-size: 18px; font-weight: bold;">Chat with your Documents</h3>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
                
            # Create a simpler layout with three columns
            input_col, save_col, clear_col = st.columns([6, 1, 1])
            
            with input_col:
                prompt = st.chat_input("Ask a question about your documents:")
            
            with save_col:
                save_button = st.button("Save", key="save_chat", 
                                      disabled=not st.session_state.messages,
                                      use_container_width=True,
                                      type="primary")
            
            with clear_col:
                clear_button = st.button("Clear", key="clear_chat", 
                                       disabled=not st.session_state.messages,
                                       use_container_width=True,
                                       type="secondary")
            
            # Handle save button click
            if save_button and st.session_state.messages and 'username' in st.session_state:
                from ui.profile_components import profile_service
                chat_content = json.dumps(st.session_state.messages)
                
                default_name = "Chat Session"
                if 'pdf_docs' in st.session_state and st.session_state.pdf_docs:
                    pdf_names = [pdf.name for pdf in st.session_state.pdf_docs]
                    default_name = f"Chat about {', '.join(pdf_names[:2])}"
                    if len(pdf_names) > 2:
                        default_name += f" and {len(pdf_names) - 2} more"
                
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                project_name = f"{default_name} ({timestamp})"
                
                profile_service.save_chat_history(st.session_state.username, project_name, chat_content)
                # Set flag to indicate chat has been manually saved
                st.session_state.chat_manually_saved = True
                st.success("Chat history saved successfully!")
                
            # Handle clear button click
            if clear_button and st.session_state.messages:
                st.session_state.messages = []
                st.session_state.chat_cleared = True
                st.session_state.chat_manually_saved = False
                st.rerun()
                
            if prompt:
                st.session_state.messages.append({"role": "user", "content": prompt})
                # Reset chat_cleared flag when new messages are added
                st.session_state.chat_cleared = False
                
                with chat_container:
                    with st.chat_message("user"):
                        st.markdown(prompt)
                
                if st.session_state.context and st.session_state.pdf_docs:
                    with st.spinner("Generating response..."):
                        response = ai_service.user_input(prompt)
                        st.session_state.messages.append({"role": "assistant", "content": response['output_text']})
                        
                        if 'username' in st.session_state and st.session_state.username:
                            if 'current_chat_id' not in st.session_state:
                                import time
                                st.session_state.current_chat_id = f"chat_{int(time.time())}"
                                st.session_state.chat_cleared = False
                            
                            # Only auto-save if chat hasn't been manually saved and hasn't been cleared
                            if not st.session_state.get('chat_cleared', False) and not st.session_state.get('chat_manually_saved', False):
                                from ui.profile_components import profile_service
                                chat_content = json.dumps(st.session_state.messages)
                                
                                default_name = "Chat Session"
                                if 'pdf_docs' in st.session_state and st.session_state.pdf_docs:
                                    pdf_names = [pdf.name for pdf in st.session_state.pdf_docs]
                                    default_name = f"Chat about {', '.join(pdf_names[:2])}"
                                    if len(pdf_names) > 2:
                                        default_name += f" and {len(pdf_names) - 2} more"
                                
                                import datetime
                                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                                project_name = f"{default_name} ({timestamp})"
                                
                                profile_service.save_chat_history(st.session_state.username, project_name, chat_content)
                    
                    with chat_container:
                        with st.chat_message("assistant"):
                            st.markdown(response['output_text'])
                else:
                    st.error("Please upload and process documents first.")
        
        elif learn_option == "Summarize Document":
            st.markdown(
                """
                <div style="margin-bottom: 10px;">
                    <h3 style="font-size: 18px; font-weight: bold;">Document Summary</h3>
                    <p>Get a concise summary of your uploaded documents.</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            context = st.session_state.get("context", "")
            if context:
                with st.spinner("Generating summary..."):
                    summary = summarize_document(context)
                
                st.markdown(
                    f"""
                    <div style="padding: 20px; border-radius: 10px; margin-top: 20px; border: 1px solid #ddd;">
                        <h4>Document Summary:</h4>
                        <p>{summary}</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            else:
                st.error("No context available. Please upload and process documents first.")
        
        elif learn_option == "Generate Flashcards":
            flashcard_interface()
    
    with tab2:
        st.markdown(
            """
            <div style="margin-bottom: 20px;">
                <h2 style="font-size: 20px; font-weight: bold; margin-bottom: 10px;">Test Your Knowledge</h2>
                <p>Take quizzes based on your uploaded documents to reinforce your learning.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        quiz_interface()
    
    with tab3:
        st.markdown(
            """
            <div style="margin-bottom: 20px;">
                <h2 style="font-size: 20px; font-weight: bold; margin-bottom: 10px;">Analyze Your Documents</h2>
                <p>Get insights into text complexity and extract key concepts from your documents.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        analyze_option = st.radio(
            "Choose an analysis option:",
            ["Analyze Text Complexity", "Extract Key Concepts"],
            horizontal=True
        )
        
        if analyze_option == "Analyze Text Complexity":
            analysis_interface()
        
        elif analyze_option == "Extract Key Concepts":
            st.markdown(
                """
                <div style="margin-bottom: 10px;">
                    <h3 style="font-size: 18px; font-weight: bold;">Key Concepts</h3>
                    <p>Extract the most important concepts from your documents.</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            context = st.session_state.get("context", "")
            if context:
                with st.spinner("Extracting key concepts..."):
                    key_concepts = extract_key_concepts(context)
                
                st.markdown("<h4>Key Concepts:</h4>", unsafe_allow_html=True)
                
                concept_cols = st.columns(2)
                for i, (concept, score) in enumerate(key_concepts):
                    col_idx = i % 2
                    with concept_cols[col_idx]:
                        st.markdown(
                            f"""
                            <div style="padding: 10px; border-radius: 5px; margin-bottom: 10px; border: 1px solid #ddd;">
                                <p style="margin: 0; font-weight: bold;">{concept}</p>
                                <div style="width: 100%; height: 5px; border-radius: 5px; margin-top: 5px; border: 1px solid #ddd;">
                                    <div style="width: {int(score * 100)}%; height: 5px; border-radius: 5px;"></div>
                                </div>
                                <p style="margin: 0; font-size: 12px; text-align: right;">{score:.2f}</p>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
            else:
                st.error("No context available. Please upload and process documents first.")
    
    with tab4:
        st.markdown(
            """
            <div style="margin-bottom: 20px;">
                <h2 style="font-size: 20px; font-weight: bold; margin-bottom: 10px;">Useful Tools</h2>
                <p>Additional tools to enhance your learning experience.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        tools_option = st.radio(
            "Choose a tool:",
            ["Translate Text", "Share Document", "Text to Speech", "Save Chat"],
            horizontal=True
        )
        
        if tools_option == "Translate Text":
            translation_interface()
        
        elif tools_option == "Share Document":
            sharing_interface()
        
        elif tools_option == "Text to Speech":
            audio_interface()
        
        elif tools_option == "Save Chat":
            save_current_chat()

    with st.sidebar:
        sidebar_components()

if __name__ == "__main__":
    main()
