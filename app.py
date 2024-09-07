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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def update_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    if os.path.exists("faiss_index"):
        vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        vector_store.add_texts(text_chunks)
    else:
        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_gemini_response(question, context):
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
    Answer the question as detailed as possible from the provided context. Make sure to provide all the details.
    If the answer is not in the provided context, just say, "Answer is not available in the context." Don't provide a wrong answer.
    

    Context: {context}

    Question: {question}

    Answer:
    """
    try:
        response = model.generate_content(prompt)
        logger.info(f"Raw response: {response}")
        logger.info(f"Response type: {type(response)}")
        logger.info(f"Response attributes: {dir(response)}")
        
        # Extract the text from the response
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                return ' '.join(part.text for part in candidate.content.parts)
        return "No readable response generated."
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return f"Error generating response: {str(e)}"

def user_input(user_question):
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(user_question, k=4)
        
        context = "\n".join([doc.page_content for doc in docs])
        
        #logger.info("Sending request to the model")
        response = get_gemini_response(user_question, context)
        
        #logger.info(f"Received response: {response}")
        
        return {"output_text": response}
    
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        return {"output_text": "An unexpected error occurred. Please try again."}

def main():
    st.set_page_config(page_title="AI-Powered Personalized Learning Assistant", layout="wide")
    
    # Sidebar for file upload and processing
    with st.sidebar:
        st.header("Document Upload")
        pdf_docs = st.file_uploader("Upload your PDFs", type="pdf", accept_multiple_files=True)
        if st.button("Process Documents"):
            if pdf_docs:
                with st.spinner("Processing documents..."):
                    raw_text = get_pdf_text(pdf_docs)
                    text_chunks = get_text_chunks(raw_text)
                    update_vector_store(text_chunks)
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
                response = user_input(prompt)

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
        st.session_state.messages = []
        st.rerun()
                    
if __name__ == "__main__":
    load_dotenv()
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    main()