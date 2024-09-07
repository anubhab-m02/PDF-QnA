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

# Set up logging for debugging and information
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Configure Google Generative AI with the API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_pdf_text(pdf_docs):
    #Extract text from uploaded PDF documents.
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)  # Read the PDF file
        for page in pdf_reader.pages:
            text += page.extract_text()  # Extract text from each page
    return text

def get_text_chunks(text):
    #Split the extracted text into manageable chunks.
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)  # Split text into chunks
    return chunks

def update_vector_store(text_chunks):
    #Update the FAISS vector store with new text chunks.
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    if os.path.exists("faiss_index"):
        # Load existing vector store if it exists
        vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        vector_store.add_texts(text_chunks)  # Add new text chunks to the vector store
    else:
        # Create a new vector store if it doesn't exist
        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")  # Save the updated vector store

def get_gemini_response(question, context):
    #Generate a response to a question based on the provided context.
    model = genai.GenerativeModel('gemini-pro')  # Initialize the generative model
    prompt = f"""
    Answer the question as detailed as possible from the provided context. Make sure to provide all the details.
    If the answer is not in the provided context, just say, "Answer is not available in the context." Don't provide a wrong answer.
    
    Context: {context}

    Question: {question}

    Answer:
    """
    try:
        response = model.generate_content(prompt)  # Generate content based on the prompt
        logger.info(f"Raw response: {response}")
        logger.info(f"Response type: {type(response)}")
        logger.info(f"Response attributes: {dir(response)}")
        
        # Extract the text from the response
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                return ' '.join(part.text for part in candidate.content.parts)  # Join parts of the response
        return "No readable response generated."
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")  # Log any errors
        return f"Error generating response: {str(e)}"

def user_input(user_question):
    #Handle user input and generate a response based on the question.
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(user_question, k=4)  # Search for similar documents
        
        context = "\n".join([doc.page_content for doc in docs])  # Create context from found documents
        
        response = get_gemini_response(user_question, context)  # Get response from the model
        
        return {"output_text": response}
    
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")  # Log unexpected errors
        return {"output_text": "An unexpected error occurred. Please try again."}

def generate_quiz(context):
    #Generate a quiz based on the provided context.
    if not context.strip():
        logger.error("No context provided for generating quiz.")
        return []

    questions = []
    model = genai.GenerativeModel('gemini-pro')
    
    # Generate questions based on the context
    question_prompt = f"""
    Based on the following context, generate a list of detailed and relevant multiple-choice questions with four options each:
    
    Context: {context}
    
    Questions:
    """
    try:
        question_response = model.generate_content(question_prompt)  # Generate quiz questions
        if question_response.candidates:
            candidate = question_response.candidates[0]
            if candidate.content and candidate.content.parts:
                generated_questions = [part.text.strip() for part in candidate.content.parts if part.text.strip()]
                for q in generated_questions:
                    questions.append({"question": q})  # Append generated questions to the list
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")  # Log errors during quiz generation
    
    return questions

def main():
    #Main function to run the Streamlit app.
    st.set_page_config(page_title="AI-Powered Personalized Learning Assistant", layout="wide")
    
    # Sidebar for file upload and processing
    with st.sidebar:
        st.header("Document Upload")
        pdf_docs = st.file_uploader("Upload your PDFs", type="pdf", accept_multiple_files=True)
        if st.button("Process Documents"):
            if pdf_docs:
                with st.spinner("Processing documents..."):
                    raw_text = get_pdf_text(pdf_docs)  # Extract text from uploaded PDFs
                    text_chunks = get_text_chunks(raw_text)  # Split text into chunks
                    update_vector_store(text_chunks)  # Update the vector store with new chunks
                    st.session_state.context = raw_text  # Store the context in session state
                    logger.info("Context extracted and stored in session state.")
                st.success("Documents processed successfully!")
            else:
                st.warning("Please upload PDF documents first.")

    # Main chat interface
    st.header("AI-Powered Personalized Learning Assistant")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # User choice: Quiz or Gemini Response
    user_choice = st.selectbox("Choose an option:", ["Ask a question", "Take a quiz"])

    if user_choice == "Ask a question":
        # User Input
        if prompt := st.chat_input("Ask a question about your documents:"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message in chat
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            if os.path.exists("faiss_index"):
                with st.spinner("Generating response..."):
                    response = user_input(prompt)  # Get response for the user's question

                    # Add AI message to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response['output_text']})
                    
                    # Display AI message in chat
                    with chat_container:
                        with st.chat_message("assistant"):
                            st.markdown(response['output_text'])
            else:
                with chat_container:
                    with st.chat_message("assistant"):
                        st.warning("Please upload and process documents before asking questions.")

        # Add a button to clear chat history
        if st.button("Clear Chat History"):
            st.session_state.messages = []  # Clear chat history
            st.rerun()

    elif user_choice == "Take a quiz":
        # Quiz Section
        st.header("Quiz Section")
        if "quiz_started" not in st.session_state:
            st.session_state.quiz_started = False
            st.session_state.current_question = 0
            st.session_state.questions = []

        if not st.session_state.quiz_started:
            if st.button("Start Quiz"):
                st.session_state.quiz_started = True
                st.session_state.current_question = 0
                context = st.session_state.get("context", "")
                if not context:
                    st.error("No context available. Please upload and process documents first.")
                    return
                st.session_state.questions = generate_quiz(context)  # Generate quiz questions
                st.rerun()

        if st.session_state.quiz_started:
            questions = st.session_state.questions
            current_question = st.session_state.current_question

            if current_question < len(questions):
                question = questions[current_question]
                st.write(question["question"])  # Display the current question
                # Display options (to be implemented)

            if st.button("Generate New Questions"):
                context = st.session_state.get("context", "")
                if context:
                    st.session_state.questions = generate_quiz(context)  # Generate new quiz questions
                    st.session_state.current_question = 0
                    st.rerun()
                else:
                    st.error("No context available. Please upload and process documents first.")

if __name__ == "__main__":
    load_dotenv()  # Load environment variables
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))  # Configure the API key
    main()  # Run the main function