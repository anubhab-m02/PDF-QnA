from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from utils.logging_config import logger
from config.settings import MAX_PAGES, MAX_CHARS, CHUNK_SIZE, CHUNK_OVERLAP

def get_pdf_text(pdf_docs):
    """Extract text from uploaded PDF documents."""
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for i, page in enumerate(pdf_reader.pages):
            if i >= MAX_PAGES:
                break
            page_text = page.extract_text()
            if page_text:
                text += page_text
                if len(text) > MAX_CHARS:
                    text = text[:MAX_CHARS]
                    return text
    
    logger.info(f"Extracted text length: {len(text)}")
    return text

def get_text_chunks(text):
    """Split the extracted text into manageable chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, 
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = text_splitter.split_text(text)
    return chunks

def update_vector_store(text_chunks):
    """Update the FAISS vector store with new text chunks."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    try:
        vector_store = FAISS.load_local(
            "faiss_index", 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        vector_store.add_texts(text_chunks)
        logger.info("Added new text chunks to existing FAISS index.")
    except:
        vector_store = FAISS.from_texts(text_chunks, embeddings)
        logger.info("Created new FAISS index from text chunks.")
    
    vector_store.save_local("faiss_index")
    logger.info("FAISS index saved locally.")
