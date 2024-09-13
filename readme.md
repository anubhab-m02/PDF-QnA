# AI-Powered Personalized Learning Assistant

This project leverages the power of Large Language Models (LLMs) and document embeddings to create a personalized learning assistant that can answer questions based on the content of uploaded PDF documents.

## Features

*   **Document Understanding:** Upload multiple PDF documents and the assistant will process and understand their content.
*   **Question Answering:** Ask questions about the uploaded documents in a conversational manner.
*   **Quiz Generation:** Generate multiple-choice quizzes based on the content of the uploaded documents.
*   **Chat History:** Maintain a chat history to keep track of your interactions with the assistant.
*   **Powered by Google Gemini Pro:** Utilizes the advanced capabilities of the Google Gemini Pro LLM for natural language understanding and generation.
*   **Document Summarization:** Summarize uploaded documents for quick overview.
*   **Flashcard Generation:** Create flashcards from document content for effective studying.
*   **Text Translation:** Translate document content to various languages.
*   **Document Sharing:** Share processed documents via email.
*   **Text Complexity Analysis:** Analyze and visualize the complexity of the document text.
*   **Key Concept Extraction:** Identify and extract key concepts from the document.
*   **Text-to-Speech Conversion:** Convert document text to speech for audio learning.
*   **Chat History Sharing:** Send chat history to specified email addresses.

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
    *   `transformers`
    *   `deep_translator`
    *   `scikit-learn`
    *   `matplotlib`
    *   `seaborn`
    *   `gtts`
    *   `torch`

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

1.  **Upload PDFs:** Use the file uploader to select and upload your PDF documents.
2.  **Process & Ask:** Click the "Process Documents" button to process the documents and enable the chat interface.
3.  **Choose an Option:** Select from various features like asking questions, taking quizzes, summarizing documents, generating flashcards, translating text, sharing documents, analyzing text complexity, extracting key concepts, or converting text to speech.
4.  **Interact:** Follow the prompts for each feature to interact with the AI assistant and learn from your documents.

## Important Notes

*   **Security:** Be cautious when setting `allow_dangerous_deserialization=True` in the code. Only do this if you trust the source of your FAISS index file.
*   **Model Availability:** Ensure you have access to the Google Gemini Pro model through your Google Cloud API key.
*   **Error Handling:** The code includes basic error handling, but further enhancements can be made for a more robust user experience.
*   **FAISS Index:** The FAISS index is updated with new documents instead of being deleted and recreated each time. This ensures that the assistant can answer questions based on all uploaded documents.
*   **Data Cleanup:** The application now includes a cleanup function to remove old FAISS index files and clear large Streamlit caches.

## Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.
