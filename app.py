import streamlit as st 
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

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

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")
    
def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, 
    if the answer is not in the provided context just say, "answer is not available in the context", don't provide the wrong answer.\n\n
    Context:\n {context}?\n
    Question:\n {question}\n
    
    Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.8)
    prompt=PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model,chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)
    
    chain = get_conversational_chain()
    
    response = chain(
        {"input_documents":docs, "question":user_question}
        , return_only_outputs = True)
    
    print(response)
    
    st.write(response["output_text"])
    
def main():
    st.set_page_config("AI-Powered Personalized Learning Assistant")
    st.header("AI-Powered Personalized Learning Assistant")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # File Uploader
    pdf_docs = st.file_uploader("Upload your PDFs", type="pdf", accept_multiple_files=True)

    if st.button("Process & Ask"):
        if pdf_docs:
            with st.spinner("Processing..."):
                # 1. Get PDF Text
                raw_text = get_pdf_text(pdf_docs)

                # 2. Split into Chunks
                text_chunks = get_text_chunks(raw_text)

                # 3. Create Vector Store (Only if it doesn't exist)
                if not os.path.exists("faiss_index"):
                    get_vector_store(text_chunks)

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Input   

    if prompt := st.chat_input("Ask a question about your documents:"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat   

        with st.chat_message("user"):
            st.markdown(prompt)

        if pdf_docs:
            with st.spinner("Generating response..."):
                response = user_input(prompt)  # Get the response from your existing function

                # Add AI message to chat history
                st.session_state.messages.append({"role": "assistant", "content": response['output_text']})
                # Display AI message in chat
                with st.chat_message("assistant"):
                    st.markdown(response['output_text'])
                    
if __name__ == "__main__":
    load_dotenv()
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    main()