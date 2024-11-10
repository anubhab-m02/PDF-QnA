import streamlit as st 
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import logging
import shutil
import re
from deep_translator import GoogleTranslator
import traceback
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from gtts import gTTS
import os
import time
import torch
import requests
from io import StringIO

###################
# Logging Setup
###################

class StringIOHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        self.stream = StringIO()

    def emit(self, record):
        msg = self.format(record)
        self.stream.write(msg + '\n')

    def get_contents(self):
        return self.stream.getvalue()

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
string_io_handler = StringIOHandler()
logger.addHandler(string_io_handler)

###################
# Environment Setup
###################

# Load environment variables from .env file
load_dotenv()

# Configure Google Generative AI with the API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Check if CUDA is available and set the device accordingly
device = 0 if torch.cuda.is_available() else -1

###################
# PDF Processing
###################

def get_pdf_text(pdf_docs):
    """Extract text from uploaded PDF documents."""
    text = ""
    max_pages = 1000  # Limit to first 1000 pages per document
    max_chars = 100000000  # Limit to 100,000,000 characters total

    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for i, page in enumerate(pdf_reader.pages):
            if i >= max_pages:
                break
            page_text = page.extract_text()
            if page_text:
                text += page_text
                if len(text) > max_chars:
                    text = text[:max_chars]
                    return text
    
    logger.info(f"Extracted text length: {len(text)}")
    return text

def get_text_chunks(text):
    """Split the extracted text into manageable chunks."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_text(text)
    return chunks

def update_vector_store(text_chunks):
    """Update the FAISS vector store with new text chunks."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    if os.path.exists("faiss_index"):
        vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        vector_store.add_texts(text_chunks)
        logger.info("Added new text chunks to existing FAISS index.")
    else:
        vector_store = FAISS.from_texts(text_chunks, embeddings)
        logger.info("Created new FAISS index from text chunks.")
    
    vector_store.save_local("faiss_index")
    logger.info("FAISS index saved locally.")

###################
# AI Response Generation
###################

def get_gemini_response(question, context):
    """Generate a response to a question based on the provided context."""
    model = genai.GenerativeModel('gemini-1.5-flash-002')
    prompt = f"""
    Answer the question as detailed as possible from the provided context. Make sure to provide all the details.
    If the answer is not in the provided context, just say, "Answer is not available in the context." Don't provide a wrong answer.
    
    Context: {context}

    Question: {question}

    Answer:
    """
    try:
        response = model.generate_content(prompt)
        
        # Log the raw response from the model
        logger.info(f"Model response: {response}")
        
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                reply = ' '.join(part.text for part in candidate.content.parts)
                logger.info(f"Generated reply: {reply}")  # Log the generated reply
                return reply
        
        return "No readable response generated."
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return f"Error generating response: {str(e)}"

def user_input(user_question):
    """Handle user input and generate a response based on the question."""
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(user_question, k=2)
        context = "\n".join([doc.page_content for doc in docs])
        logger.info(f"Retrieved context: {context}...")
        response = get_gemini_response(user_question, context)
        return {"output_text": response}
    except Exception as e:
        logger.error(f"Error in user_input: {str(e)}")
        return {"output_text": f"An error occurred: {str(e)}"}

###################
# Quiz Generation and Handling
###################

def extract_options(question_text):
    """Extract answer choices from the generated quiz question."""
    options = re.findall(r'\b[A-D]\.\s(.*?)(?=\n[A-D]\.|\Z)', question_text, re.DOTALL)
    return [option.strip() for option in options]

def display_quiz(question):
    """Display a single quiz question and options."""
    st.write(question["question"])
    options = [opt.split('. ', 1)[-1].strip() for opt in question["options"]]
    selected_option = st.radio("Choose an answer:", options, key=f"q_{st.session_state.current_question}")
    return selected_option

def check_answer(selected_option, correct_answer):
    """Check if the selected answer is correct and provide feedback."""
    if selected_option == correct_answer:
        st.success("Correct!")
        return 1
    else:
        st.error(f"Incorrect. The correct answer is: {correct_answer}")
        return 0

def generate_quiz(context):
    """Generate a quiz based on the provided context."""
    if not context.strip():
        logger.error("No context provided for generating quiz.")
        return []

    context = context  # Use only the first 1000 characters of the context

    questions = []
    model = genai.GenerativeModel('gemini-1.5-flash-002')
    question_prompt = f"""
    Based on the following context, generate a list of 5 concise multiple-choice questions with four options each. For each question, also provide the correct answer.
    
    Context: {context}
    
    Format each question as follows:
    Question: [Question text]
    A. [Option A]
    B. [Option B]
    C. [Option C]
    D. [Option D]
    Correct Answer: [A/B/C/D]

    Ensure there is a blank line between each question.
    """
    try:
        logger.info("Sending request to generate quiz questions...")
        question_response = model.generate_content(question_prompt)
        logger.info(f"Received response: {question_response}")
        
        if question_response.candidates:
            candidate = question_response.candidates[0]
            if candidate.content and candidate.content.parts:
                generated_questions = candidate.content.parts[0].text.split('\n\n')
                logger.info(f"Number of generated questions: {len(generated_questions)}")
                for q in generated_questions:
                    question_parts = q.split('\n')
                    if len(question_parts) >= 6:  # Ensure we have all parts of the question
                        question_text = question_parts[0].replace('Question: ', '').strip()
                        options = [opt.strip() for opt in question_parts[1:5]]
                        correct_answer = question_parts[-1].split(': ')[1].strip()
                        questions.append({
                            "question": question_text,
                            "options": options,
                            "correct_answer": correct_answer
                        })
                    else:
                        logger.warning(f"Skipping malformed question: {q}")
            else:
                logger.error("No content in the response")
        else:
            logger.error("No candidates in the response")
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    logger.info(f"Generated {len(questions)} valid questions")
    return questions

###################
# Document Summarization
###################

def summarize_document(text):
    """Summarize the uploaded document using Gemini API."""
    if not text or len(text) < 30:
        logger.error("Input text is too short for summarization.")
        return "Input text is too short for summarization."
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-002')
        prompt = f"""
        Please provide a concise summary of the following text. The summary should capture the main points and key ideas:

        {text}

        Summary:
        """
        
        response = model.generate_content(prompt)
        
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                summary = ' '.join(part.text for part in candidate.content.parts)
                logger.info(f"Generated summary: {summary}")
                return summary
        
        return "Unable to generate summary."
    except Exception as e:
        logger.error(f"Error during summarization: {str(e)}")
        return f"Error during summarization: {str(e)}"

###################
# Learning Path Suggestion
###################

def suggest_learning_paths(quiz_performance):
    """Suggest personalized learning paths based on quiz performance."""
    if quiz_performance > 80:
        return "You're excelling! Consider exploring advanced topics or applying your knowledge to real-world projects."
    elif quiz_performance > 50:
        return "You're making good progress. Focus on reviewing the topics you found challenging and practice with more examples."
    else:
        return "It seems you might need more practice. Consider revisiting the fundamental concepts and try breaking down complex topics into smaller, manageable parts."

###################
# Flashcard Generation
###################

def generate_flashcards(context):
    """Generate flashcards from the document content."""
    if not context or len(context) < 100:
        logger.error("Input text is too short for generating flashcards.")
        return [], "Input text is too short."

    model = genai.GenerativeModel('gemini-1.5-flash-002')
    flashcard_prompt = f"""
    Based on the following context, generate 5 flashcards with key terms or concepts and their definitions.
    Each flashcard should contain a term and its corresponding definition.
    
    Context: {context}
    
    Format each flashcard as follows:
    Term: [Key term or concept]
    Definition: [Concise definition or explanation]

    Please provide exactly 5 flashcards.
    """
    try:
        logger.info("Sending request to generate flashcards...")
        flashcard_response = model.generate_content(flashcard_prompt)
        logger.info(f"Received response: {flashcard_response}")
        
        if flashcard_response.candidates:
            candidate = flashcard_response.candidates[0]
            if candidate.content and candidate.content.parts:
                flashcards_text = candidate.content.parts[0].text
                logger.info(f"Raw flashcards text: {flashcards_text}")
                flashcards = []
                for card in flashcards_text.split('\n\n'):
                    parts = card.split('\n')
                    if len(parts) == 2:
                        term = parts[0].split(': ', 1)[-1].strip()
                        definition = parts[1].split(': ', 1)[-1].strip()
                        if term and definition:
                            flashcards.append({"term": term, "definition": definition})
                    else:
                        logger.warning(f"Skipping malformed flashcard: {card}")
                
                if flashcards:
                    logger.info(f"Generated {len(flashcards)} flashcards successfully.")
                    return flashcards, None
                else:
                    error_msg = "No valid flashcards were extracted from the response."
                    logger.error(error_msg)
                    return [], error_msg
            else:
                error_msg = "No content in the response from the model."
                logger.error(error_msg)
                return [], error_msg
        else:
            error_msg = "No candidates in the response from the model."
            logger.error(error_msg)
            return [], error_msg
    except Exception as e:
        error_msg = f"Error generating flashcards: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        return [], error_msg

    # Fallback: If we reach here, something unexpected happened
    return [], "Unexpected error occurred during flashcard generation."

###################
# Text Translation
###################

def translate_text(text, dest_language):
    """Translate text to the specified language using deep_translator."""
    if not text:
        logger.error("No text provided for translation.")
        return "No text provided for translation."
    
    try:
        translator = GoogleTranslator(source='auto', target=dest_language)
        
        # Split the text into smaller chunks
        max_chunk_length = 4000  # Reduced from 5000 to be more conservative
        chunks = [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
        
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            try:
                translated_chunk = translator.translate(chunk)
                translated_chunks.append(translated_chunk)
                logger.info(f"Chunk {i+1}/{len(chunks)} translated successfully.")
            except Exception as chunk_error:
                logger.error(f"Error translating chunk {i+1}: {str(chunk_error)}")
                translated_chunks.append(f"[Translation error in chunk {i+1}]")
        
        translated_text = ' '.join(translated_chunks)
        
        logger.info(f"Translation completed. Original length: {len(text)}, Translated length: {len(translated_text)}")
        return translated_text
    except Exception as e:
        logger.error(f"Error during translation process: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Error during translation process: {str(e)}"

###################
# Document Sharing
###################

def share_document(pdf_docs, recipient_email):
    """Share PDF documents with another user via email."""
    sender_email = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_APP_PASSWORD")

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = "Shared Documents from AI Learning Assistant"

    # Add body text
    body = "Here are the documents shared with you from the AI Learning Assistant."
    message.attach(MIMEText(body, "plain"))

    # Attach PDF files
    for pdf in pdf_docs:
        pdf.seek(0)  # Reset file pointer to beginning
        part = MIMEBase("application", "octet-stream")
        part.set_payload(pdf.read())
        encoders.encode_base64(part)
        
        # Add header with PDF filename
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {pdf.name}",
        )
        message.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(message)
        return f"Documents shared successfully with {recipient_email}"
    except Exception as e:
        logger.error(f"Error sharing documents: {str(e)}")
        return f"Error sharing documents: {str(e)}"

###################
# Text Complexity Analysis
###################

def analyze_text_complexity(text):
    """Analyze the complexity of the text."""
    sentences = text.split('.')
    word_counts = [len(sentence.split()) for sentence in sentences if sentence.strip()]
    avg_words_per_sentence = sum(word_counts) / len(word_counts)
    
    words = text.split()
    avg_word_length = sum(len(word) for word in words) / len(words)
    
    complexity_score = (avg_words_per_sentence * 0.5) + (avg_word_length * 5)
    
    return {
        "avg_words_per_sentence": avg_words_per_sentence,
        "avg_word_length": avg_word_length,
        "complexity_score": complexity_score
    }

def visualize_text_complexity(complexity_data):
    """Visualize the text complexity data."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create a bar plot for all metrics
    metrics = ['avg_words_per_sentence', 'avg_word_length', 'complexity_score']
    values = [complexity_data[metric] for metric in metrics]
    
    sns.barplot(x=metrics, y=values, ax=ax)
    ax.set_title('Text Complexity Metrics')
    ax.set_ylabel('Value')
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels on top of each bar
    for i, v in enumerate(values):
        ax.text(i, v, f'{v:.2f}', ha='center', va='bottom')
    
    # Add a color-coded text for complexity score
    complexity_score = complexity_data['complexity_score']
    if complexity_score < 10:
        color = 'green'
        label = 'Low'
    elif complexity_score < 15:
        color = 'orange'
        label = 'Medium'
    else:
        color = 'red'
        label = 'High'
    
    plt.text(0.5, -0.15, f'Complexity: {label} ({complexity_score:.2f})', 
             color=color, fontsize=12, ha='center', transform=ax.transAxes)
    
    plt.tight_layout()
    st.pyplot(fig)

###################
# Key Concept Extraction
###################

def extract_key_concepts(text):
    """Extract key concepts from the text using TF-IDF."""
    vectorizer = TfidfVectorizer(stop_words='english', max_features=10)
    tfidf_matrix = vectorizer.fit_transform([text])
    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = tfidf_matrix.toarray()[0]
    key_concepts = sorted(zip(feature_names, tfidf_scores), key=lambda x: x[1], reverse=True)
    return key_concepts

###################
# Text-to-Speech Conversion
###################

def text_to_speech(text, max_retries=3):
    """Convert text to speech using gTTS with chunking and retries."""
    chunk_size = 5000  # Characters per chunk
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    audio_files = []
    for i, chunk in enumerate(chunks):
        retry_count = 0
        while retry_count < max_retries:
            try:
                tts = gTTS(text=chunk, lang='en')
                filename = f"output_{i}.mp3"
                tts.save(filename)
                audio_files.append(filename)
                time.sleep(1)  # Add a delay between requests
                break
            except Exception as e:
                logger.error(f"Error in text-to-speech conversion: {str(e)}")
                retry_count += 1
                time.sleep(2 ** retry_count)  # Exponential backoff
        
        if retry_count == max_retries:
            logger.error(f"Failed to convert chunk {i} after {max_retries} retries")
    
    if not audio_files:
        return None
    
    # Combine audio files
    combined_audio = f"combined_output.mp3"
    os.system(f"cat {' '.join(audio_files)} > {combined_audio}")
    
    # Clean up individual chunk files
    for file in audio_files:
        os.remove(file)
    
    return combined_audio

def send_chat_history(chat_history, recipient_email):
    """Send chat history to the specified email."""
    sender_email = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_APP_PASSWORD")

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = "Chat History from AI Learning Assistant"

    body = "Here's the chat history:\n\n"
    for chat in chat_history:
        body += f"{chat['role'].capitalize()}: {chat['content']}\n\n"

    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(message)
        return f"Chat history shared successfully with {recipient_email}"
    except Exception as e:
        logger.error(f"Error sharing chat history: {str(e)}")
        return f"Error sharing chat history: {str(e)}"

def cleanup_old_data():
    # Remove old FAISS index files
    if os.path.exists("faiss_index"):
        if time.time() - os.path.getmtime("faiss_index") > 24 * 60 * 60:  # 24 hours
            shutil.rmtree("faiss_index")
            logger.info("Removed old FAISS index")

    # Clear Streamlit cache if it's too large
    cache_path = os.path.join(os.path.expanduser("~"), ".streamlit/cache")
    if os.path.exists(cache_path):
        cache_size = sum(os.path.getsize(os.path.join(dirpath,filename)) for dirpath, dirnames, filenames in os.walk(cache_path) for filename in filenames)
        if cache_size > 1e9:  # 1 GB
            shutil.rmtree(cache_path)
            logger.info("Cleared Streamlit cache due to large size")

def main():
    cleanup_old_data()
    st.set_page_config(page_title="AI-Powered Personalized Learning Assistant", layout="wide")
    
    st.header("AI-Powered Personalized Learning Assistant")
    
    # Add this information box below the header
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
        st.header("Document Upload")
        pdf_docs = st.file_uploader("Upload your PDFs", type="pdf", accept_multiple_files=True)
        if st.button("Process Documents"):
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

            if os.path.exists("faiss_index"):
                with st.spinner("Generating response..."):
                    response = user_input(prompt)
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
            st.rerun()

    elif user_choice == "Take a quiz":
        st.header("Quiz Section")
        
        if "quiz_state" not in st.session_state:
            st.session_state.quiz_state = "not_started"
            st.session_state.questions = []
            st.session_state.current_question = 0
            st.session_state.score = 0
            st.session_state.num_questions = 5  # Default number of questions

        if st.session_state.quiz_state == "not_started":
            if st.button("Start Quiz"):
                st.session_state.quiz_state = "select_num_questions"
                st.rerun()

        elif st.session_state.quiz_state == "select_num_questions":
            num_questions_options = list(range(1, 26))  # Options from 1 to 25
            st.session_state.num_questions = st.selectbox(
                "Select number of questions:", 
                options=num_questions_options, 
                index=4  # Default to 5 questions (index 4 in the list)
            )
            if st.button("Generate Questions"):
                context = st.session_state.get("context", "")
                if not context:
                    st.error("No context available. Please upload and process documents first.")
                    return
                with st.spinner("Generating quiz questions..."):
                    st.session_state.questions = generate_quiz(context)[:st.session_state.num_questions]
                if not st.session_state.questions:
                    st.error("Failed to generate quiz questions. Please try again.")
                    return
                st.session_state.quiz_state = "answering"
                st.session_state.current_question = 0
                st.session_state.score = 0
                st.rerun()

        elif st.session_state.quiz_state == "answering":
            current_question = st.session_state.current_question
            question = st.session_state.questions[current_question]
            
            st.write(f"Question {current_question + 1} of {len(st.session_state.questions)}:")
            selected_option = display_quiz(question)
            
            if st.button("Submit Answer"):
                correct_answer = question["correct_answer"].strip()
                correct_option_index = ord(correct_answer) - ord('A')
                correct_option_full = question["options"][correct_option_index]
                correct_option = correct_option_full.split('. ', 1)[-1].strip()
                
                is_correct = selected_option.strip() == correct_option
                
                if is_correct:
                    st.success("Correct!")
                    st.session_state.score += 1
                else:
                    st.error(f"Incorrect. The correct answer is: {correct_option}")
                
                st.session_state.current_question += 1
                
                if st.session_state.current_question < len(st.session_state.questions):
                    if st.button("Next Question"):
                        st.rerun()
                else:
                    st.session_state.quiz_state = "finished"
                st.rerun()

        elif st.session_state.quiz_state == "finished":
            st.write(f"Quiz completed! Your score: {st.session_state.score}/{len(st.session_state.questions)}")
            quiz_performance = (st.session_state.score / len(st.session_state.questions)) * 100
            learning_path = suggest_learning_paths(quiz_performance)
            st.write("Suggested Learning Path:")
            st.write(learning_path)
            if st.button("Start New Quiz"):
                st.session_state.quiz_state = "not_started"
                st.rerun()

    elif user_choice == "Summarize Document":
        context = st.session_state.get("context", "")
        if context:
            summary = summarize_document(context)
            st.write("Document Summary:")
            st.write(summary)
        else:
            st.error("No context available. Please upload and process documents first.")

    elif user_choice == "Generate Flashcards":
        context = st.session_state.get("context", "")
        if context:
            # Add a button to regenerate flashcards
            regenerate = st.button("Regenerate Flashcards")
            
            # Generate flashcards if they don't exist or if regenerate button is pressed
            if "flashcards" not in st.session_state or regenerate:
                with st.spinner("Generating flashcards..."):
                    flashcards, error_msg = generate_flashcards(context)
                st.session_state.flashcards = flashcards
                st.session_state.flashcard_error = error_msg
            else:
                flashcards = st.session_state.flashcards
                error_msg = st.session_state.flashcard_error

            if flashcards:
                st.write("Flashcards:")
                for i, card in enumerate(flashcards, 1):
                    st.write(f"Flashcard {i}:")
                    st.write(f"Term: {card['term']}")
                    st.write(f"Definition: {card['definition']}")
                    st.write("---")
            else:
                st.warning("Unable to generate flashcards. Please try again or check the input text.")
                st.error(f"Error: {error_msg}")
                st.write("Debug information:")
                st.write(f"Context length: {len(context)}")
                st.write(f"First 100 characters of context: {context[:100]}...")
                st.write("Check the application logs for more details.")
        else:
            st.error("No context available. Please upload and process documents first.")

    elif user_choice == "Translate Text":
        context = st.session_state.get("context", "")
        if context:
            dest_language = st.selectbox("Select language:", ["es", "fr", "de", "zh-CN", "ja", "ko", "ru"])
            if st.button("Translate"):
                st.info("Translation in progress... This may take a while for long texts.")
                logger.info(f"Attempting to translate text. Length: {len(context)}, First 100 chars: {context[:100]}...")
                translated_text = translate_text(context, dest_language)
                st.write("Translated Text:")
                st.write(translated_text[:1000] + "..." if len(translated_text) > 1000 else translated_text)
                
                st.write("Debug Information:")
                st.write(f"Original text length: {len(context)}")
                st.write(f"Translated text length: {len(translated_text)}")
                st.write(f"Target language: {dest_language}")
                
                if "[Translation error in chunk" in translated_text:
                    st.warning("Some parts of the text could not be translated. Please check the logs for details.")
        else:
            st.error("No context available. Please upload and process documents first.")

    elif user_choice == "Share Document":
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Share Chat History")
            if st.session_state.messages:
                recipient_email = st.text_input("Enter recipient email:", key="chat_history_email")
                if st.button("Share Chat History", key="share_chat"):
                    with st.spinner("Sharing chat history..."):
                        result = send_chat_history(st.session_state.messages, recipient_email)
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
                        result = share_document(st.session_state.pdf_docs, recipient_email)
                        if "successfully" in result:
                            st.success(result)
                        else:
                            st.error(result)
            else:
                st.error("No documents available. Please upload PDF files first.")

    elif user_choice == "Analyze Text Complexity":
        context = st.session_state.get("context", "")
        if context:
            complexity_data = analyze_text_complexity(context)
            st.write("Text Complexity Analysis:")
            st.write(f"Average Words per Sentence: {complexity_data['avg_words_per_sentence']:.2f}")
            st.write(f"Average Word Length: {complexity_data['avg_word_length']:.2f}")
            st.write(f"Overall Complexity Score: {complexity_data['complexity_score']:.2f}")
            visualize_text_complexity(complexity_data)
        else:
            st.error("No context available. Please upload and process documents first.")

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
        context = st.session_state.get("context", "")
        if context:
            st.write("Text to be converted to speech:")
            display_text = context[:1000] + "..." if len(context) > 1000 else context
            st.write(display_text)
            
            if st.button("Convert to Speech"):
                with st.spinner("Converting text to speech... This may take a while for long texts."):
                    audio_file = text_to_speech(context)
                    if audio_file:
                        st.audio(audio_file, format='audio/mp3')
                        st.success("Text converted to speech successfully!")
                        st.download_button(
                            label="Download Audio",
                            data=open(audio_file, "rb"),
                            file_name="text_to_speech.mp3",
                            mime="audio/mp3"
                        )
                    else:
                        st.error("Failed to convert text to speech. Please try again later.")
        else:
            st.error("No context available. Please upload and process documents first.")


if __name__ == "__main__":
    load_dotenv()
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    main()
