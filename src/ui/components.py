import streamlit as st
import os
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
from utils.logging_config import logger
from ui.profile_components import profile_button
from services.profile_service import profile_service

def sidebar_components():
    with st.sidebar:
        # Add app logo and title at the top
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="font-size: 24px; margin-bottom: 0;">📚 Learning Assistant</h1>
                <p style="font-size: 14px;">Your AI Study Companion</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Profile button at the top of sidebar
        profile_button()
        
        # Document upload section with improved styling
        st.markdown(
            """
            <div style="margin-top: 20px; margin-bottom: 10px;">
                <h2 style="font-size: 18px; font-weight: bold;">
                    <span style="margin-right: 10px;">📄</span>Document Upload
                </h2>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Add a description
        st.markdown(
            """
            <p style="font-size: 14px; margin-bottom: 15px;">
                Upload your PDF documents to start learning and asking questions.
            </p>
            """, 
            unsafe_allow_html=True
        )
        
        # File uploader with better styling
        pdf_docs = st.file_uploader("Upload your PDFs", type="pdf", accept_multiple_files=True)
        
        # Process button with better styling
        process_btn = st.button("Process Documents", type="primary", use_container_width=True)
        
        if process_btn:
            if pdf_docs:
                with st.spinner("Processing documents..."):
                    st.session_state.pdf_docs = pdf_docs  # Store PDFs in session state
                    raw_text = get_pdf_text(pdf_docs)
                    text_chunks = get_text_chunks(raw_text)
                    update_vector_store(text_chunks)
                    st.session_state.context = raw_text
                    logger.info("Context extracted and stored in session state.")
                st.success("Documents processed successfully!")
            else:
                st.warning("Please upload PDF documents first.")
        
        # Add app info at the bottom
        st.markdown("<hr style='margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style="text-align: center; margin-top: 20px; font-size: 12px;">
                <p>AI-Powered Learning Assistant</p>
                <p>Version 1.0</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    return "Chat", pdf_docs  # Default to chat interface

def chat_interface():
    st.header("Chat with your Documents")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.text_input("Ask a question about your documents:"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        if os.path.exists("faiss_index"):
            with st.spinner("Generating response..."):
                response = ai_service.user_input(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response['output_text']})
        else:
            st.warning("Please upload and process documents before asking questions.")

def quiz_interface():
    st.header("Quiz Mode")
    
    # Check if user is logged in
    if "username" not in st.session_state:
        st.warning("Please log in to save your quiz results and get personalized learning paths.")
        username = None
    else:
        username = st.session_state.username
    
    # Initialize session state variables if they don't exist
    if "quiz_state" not in st.session_state:
        st.session_state.quiz_state = "not_started"
        st.session_state.questions = []
        st.session_state.current_question = 0
        st.session_state.score = 0
        st.session_state.user_answers = []
        st.session_state.answer_submitted = False
        st.session_state.current_answer_correct = False
        st.session_state.quiz_topic = ""
    
    # Ensure quiz_topic exists even for existing sessions
    if "quiz_topic" not in st.session_state:
        st.session_state.quiz_topic = ""
    
    if st.session_state.quiz_state == "not_started":
        # Allow user to specify a topic for the quiz
        topic = st.text_input("Quiz Topic (optional):", key="quiz_topic_input")
        
        if st.button("Start Quiz"):
            if "context" in st.session_state:
                # Save the topic
                st.session_state.quiz_topic = topic
                
                # Generate questions, passing username to avoid repeating questions
                questions = quiz_service.generate_quiz(st.session_state.context, username)
                if questions:
                    st.session_state.questions = questions
                    st.session_state.quiz_state = "in_progress"
                    st.session_state.user_answers = []
                    st.session_state.answer_submitted = False
                    st.session_state.current_answer_correct = False
                    st.rerun()
                else:
                    st.warning("Failed to generate quiz questions. Please try again.")
            else:
                st.warning("Please upload and process documents first.")

    elif st.session_state.quiz_state == "in_progress":
        current_question = st.session_state.current_question
        if current_question < len(st.session_state.questions):
            question = st.session_state.questions[current_question]
            st.write(f"**Question {current_question + 1}:** {question['question']}")
            options = question['options']
            
            # Create a list of options with letters
            option_letters = ['A', 'B', 'C', 'D']
            labeled_options = [f"{option_letters[i]}) {option}" for i, option in enumerate(options)]
            
            # Display options with letters
            selected_option_index = st.selectbox(
                "Choose an answer:", 
                range(len(labeled_options)), 
                format_func=lambda i: labeled_options[i],
                key=f"q_{current_question}"
            )

            # Show submit button only if answer not yet submitted
            if not st.session_state.answer_submitted:
                if st.button("Submit Answer"):
                    # Get the letter corresponding to the selected option
                    selected_letter = option_letters[selected_option_index]
                    
                    # Store user's answer (the letter)
                    if "user_answers" not in st.session_state:
                        st.session_state.user_answers = []
                    st.session_state.user_answers.append(selected_letter)
                    
                    is_correct = quiz_service.check_answer(question, selected_letter)
                    st.session_state.current_answer_correct = is_correct
                    
                    if is_correct:
                        st.session_state.score += 1
                        st.success("Correct!")
                    else:
                        st.error(f"Incorrect. The correct answer was {question['correct_answer']}.")
                    
                    # Mark answer as submitted but don't move to next question yet
                    st.session_state.answer_submitted = True
                    st.rerun()
            
            # Show feedback and next button if answer was submitted
            else:
                if st.session_state.current_answer_correct:
                    st.success("Correct!")
                else:
                    st.error(f"Incorrect. The correct answer was {question['correct_answer']}.")
                
                # Next button to move to the next question
                if st.button("Next Question"):
                    st.session_state.current_question += 1
                    st.session_state.answer_submitted = False
                    
                    # Check if this was the last question
                    if st.session_state.current_question >= len(st.session_state.questions):
                        st.session_state.quiz_state = "finished"
                    
                    st.rerun()
        else:
            st.session_state.quiz_state = "finished"
            st.rerun()

    elif st.session_state.quiz_state == "finished":
        st.write(f"**Quiz completed! Your score: {st.session_state.score}/{len(st.session_state.questions)}**")
        quiz_performance = (st.session_state.score / len(st.session_state.questions)) * 100
        
        # Check if user_answers exists in session state
        if "user_answers" not in st.session_state:
            st.session_state.user_answers = []
        
        # Generate personalized learning path
        learning_path = suggest_learning_paths(quiz_performance, st.session_state.questions, st.session_state.user_answers)
        st.write("**Suggested Learning Path:**")
        st.write(learning_path)
        
        # Save quiz results to profile if user is logged in
        if username:
            # Make sure quiz_topic exists in session state
            quiz_topic = ""
            if hasattr(st.session_state, "quiz_topic"):
                quiz_topic = st.session_state.quiz_topic
            
            # Save quiz results to the database
            saved = profile_service.save_quiz_result(
                username=username,
                score=st.session_state.score,
                total_questions=len(st.session_state.questions),
                questions=st.session_state.questions,
                user_answers=st.session_state.user_answers,
                topic=quiz_topic
            )
            
            if saved:
                st.success("Quiz results saved to your profile!")
            else:
                st.error("Failed to save quiz results to your profile.")
        else:
            st.warning("Log in to save your quiz results and track your progress.")
        
        if st.button("Start New Quiz"):
            st.session_state.quiz_state = "not_started"
            st.session_state.score = 0
            st.session_state.current_question = 0
            st.session_state.user_answers = []
            st.session_state.answer_submitted = False
            st.session_state.quiz_topic = ""
            st.rerun()

def flashcard_interface():
    st.header("Flashcards")
    if "context" in st.session_state:
        # Initialize flashcard generation counter if it doesn't exist
        if "flashcard_gen_count" not in st.session_state:
            st.session_state.flashcard_gen_count = 0
        
        # Generate flashcards if they don't exist
        if "flashcards" not in st.session_state:
            with st.spinner("Generating flashcards..."):
                # Pass the counter to ensure different generations
                flashcards, error = flashcard_service.generate_flashcards(
                    st.session_state.context, 
                    iteration=st.session_state.flashcard_gen_count
                )
                if not error:
                    st.session_state.flashcards = flashcards
                else:
                    st.error(error)
                    return
        
        # Display flashcards
        if "flashcards" in st.session_state:
            for card in st.session_state.flashcards:
                with st.expander(card["term"]):
                    st.write(card["definition"])
        
        # Always show regenerate button if we have context
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Regenerate Flashcards", use_container_width=True):
                # Increment the counter before regenerating
                st.session_state.flashcard_gen_count += 1
                del st.session_state.flashcards
                st.rerun()
    else:
        st.warning("Please upload and process documents first.")

def translation_interface():
    st.header("Translation")
    if "context" in st.session_state:
        target_lang = st.selectbox("Select target language:", ["es", "fr", "de", "it", "pt"])
        if st.button("Translate"):
            translated_text = translation_service.translate_text(st.session_state.context, target_lang)
            st.write(translated_text)
    else:
        st.warning("Please upload and process documents first.")

def analysis_interface():
    st.header("Text Analysis")
    if "context" in st.session_state:
        complexity_data = analyze_text_complexity(st.session_state.context)
        complexity_metrics = {
            "Average Words per Sentence": complexity_data['avg_words_per_sentence'],
            "Average Word Length": complexity_data['avg_word_length'],
            "Overall Complexity Score": complexity_data['complexity_score']
        }
        st.write("Text Complexity Analysis:")
        for metric, value in complexity_metrics.items():
            st.write(f"{metric}: {value:.2f}")
        visualize_text_complexity(complexity_data)
    else:
        st.warning("Please upload and process documents first.")

def sharing_interface():
    st.header("Share")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Share Chat History")
        if st.session_state.messages:
            recipient_email = st.text_input("Enter recipient email:", key="chat_history_email")
            if st.button("Share Chat History", key="share_chat"):
                with st.spinner("Sharing chat history..."):
                    result = sharing_service.send_chat_history(st.session_state.messages, recipient_email)
                    if "successfully" in result:
                        st.success(result)
                    else:
                        st.error(result)
        else:
            st.warning("No chat history available. Please have a conversation first.")

    with col2:
        st.subheader("Share Document")
        if "pdf_docs" in st.session_state and st.session_state.pdf_docs:
            recipient_email = st.text_input("Enter recipient email:", key="document_email")
            if st.button("Share Document", key="share_doc"):
                with st.spinner("Sharing document..."):
                    result = sharing_service.share_document(st.session_state.pdf_docs, recipient_email)
                    if "successfully" in result:
                        st.success(result)
                    else:
                        st.error(result)
        else:
            st.error("No documents available. Please upload PDF files first.")

def audio_interface():
    st.header("Audio Learning")
    if "context" in st.session_state:
        if st.button("Convert to Speech"):
            audio_file = speech_service.text_to_speech(st.session_state.context)
            if audio_file:
                st.audio(audio_file, format='audio/mp3')
                st.download_button(
                    label="Download Audio",
                    data=open(audio_file, "rb"),
                    file_name="text_to_speech.mp3",
                    mime="audio/mp3"
                )
            else:
                st.error("Failed to convert text to speech. Please try again later.")
    else:
        st.warning("Please upload and process documents first.")

def suggest_learning_paths(quiz_performance, questions=None, user_answers=None):
    """
    Suggest personalized learning paths based on quiz performance and specific questions.
    
    Args:
        quiz_performance (float): Overall quiz score percentage
        questions (list, optional): List of quiz questions with their details
        user_answers (list, optional): List of user's answers to each question
    
    Returns:
        str: Personalized learning path suggestion
    """
    # Default suggestion based on overall performance
    if questions is None or user_answers is None:
        if quiz_performance > 80:
            return "You're excelling! Consider exploring advanced topics or applying your knowledge to real-world projects."
        elif quiz_performance > 50:
            return "You're making good progress. Focus on reviewing the topics you found challenging and practice with more examples."
        else:
            return "It seems you might need more practice. Consider revisiting the fundamental concepts and try breaking down complex topics into smaller, manageable parts."
    
    # Analyze incorrect answers to identify specific areas for improvement
    incorrect_topics = []
    for i, question in enumerate(questions):
        if i < len(user_answers):
            is_correct = question.get('correct_answer') == user_answers[i]
            if not is_correct:
                # Extract topic from question
                question_text = question.get('question', '')
                
                # Try to extract a meaningful topic from the question
                # Remove common question phrases and get the key concept
                topic = question_text
                for phrase in ["What is", "How does", "Explain", "Define", "Describe", "?", "."]:
                    topic = topic.replace(phrase, "")
                
                # Limit topic length to keep suggestions concise
                if len(topic) > 50:
                    topic = topic[:47] + "..."
                
                incorrect_topics.append(topic.strip())
    
    # Generate personalized suggestions based on performance and incorrect topics
    suggestion = ""
    
    if quiz_performance > 80:
        suggestion = "You're excelling! "
        if incorrect_topics:
            suggestion += f"You might want to review: {', '.join(incorrect_topics[:2])}. "
        suggestion += "Consider exploring advanced topics or applying your knowledge to real-world projects."
    
    elif quiz_performance > 50:
        suggestion = "You're making good progress. "
        if incorrect_topics:
            suggestion += f"Focus on reviewing these specific areas: {', '.join(incorrect_topics)}. "
        suggestion += "Try practicing with more examples in these topics."
    
    else:
        suggestion = "It seems you might need more practice. "
        if incorrect_topics:
            suggestion += f"Concentrate on these fundamental concepts: {', '.join(incorrect_topics)}. "
        suggestion += "Try breaking down these complex topics into smaller, manageable parts and revisit the core principles."
    
    return suggestion
