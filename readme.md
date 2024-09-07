# AI-Powered Personalized Learning Assistant

This project leverages the power of Large Language Models (LLMs) and document embeddings to create a personalized learning assistant that can answer questions based on the content of uploaded PDF documents.

## Features

*   **Document Understanding:**  Upload multiple PDF documents and the assistant will process and understand their content.
*   **Question Answering:**  Ask questions about the uploaded documents in a conversational manner.
*   **Chat History:**  Maintain a chat history to keep track of your interactions with the assistant.
*   **Powered by Google Gemini Pro:**  Utilizes the advanced capabilities of the Google Gemini Pro LLM for natural language understanding and generation.

## Getting Started

1.  **Prerequisites:**
    *   `Python 3.10`
    *   `streamlit`
    *   `google-generativeai`
    *   `python-dotenv`
    *   `langchain`
    *   `PyPDF2`
    *   `faiss-cpu`
    *   `langchain_google_genai`

2.  **Installation:**
    *   Clone this repository.
    *   Create a virtual environment:  `python -m venv venv`
    *   Activate the virtual environment:
        *   Windows:  `venv\Scripts\activate`
        *   macOS/Linux:  `source venv/bin/activate`
    *   Install dependencies:  `pip install -r requirements.txt`

3.  **API Key:**
    *   Obtain a Google Cloud API key with access to the Gemini Pro model.
    *   Create a `.env` file in the project root and add your API key:

    ```
    GOOGLE_API_KEY=your_api_key_here
    ```

4.  **Run the app:**
    *   `streamlit run app.py`

## Usage

1.  **Upload PDFs:**  Use the file uploader to select and upload your PDF documents.
2.  **Process & Ask:**  Click the "Process Documents" button to process the documents and enable the chat interface.
3.  **Ask Questions:**  Type your questions in the chat input field and press Enter.
4.  **View Responses:**  The assistant's responses will be displayed in the chat area along with your questions, creating a conversation history.

## Important Notes

*   **Security:**  Be cautious when setting `allow_dangerous_deserialization=True` in the code. Only do this if you trust the source of your FAISS index file.
*   **Model Availability:**  Ensure you have access to the Google Gemini Pro model through your Google Cloud API key.
*   **Error Handling:**  The code includes basic error handling, but further enhancements can be made for a more robust user experience.
*   **FAISS Index:**  The FAISS index is updated with new documents instead of being deleted and recreated each time. This ensures that the assistant can answer questions based on all uploaded documents.

## Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.
