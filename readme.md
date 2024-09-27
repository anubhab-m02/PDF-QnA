# AI-Powered Personalized Learning Assistant

Elevate your learning experience with our cutting-edge AI-powered assistant that transforms the way you interact with educational content. Leveraging the advanced capabilities of Google's Gemini Pro LLM, this application offers a suite of features designed to enhance comprehension, retention, and engagement with your study materials.

## 🚀 Features

- **Intelligent Document Processing:** Upload and analyze multiple PDF documents with ease.
- **Interactive Q&A:** Engage in dynamic conversations about your uploaded content.
- **Adaptive Quiz Generation:** Test your knowledge with automatically generated quizzes.
- **Smart Summarization:** Get concise overviews of complex documents.
- **Flashcard Creation:** Generate study aids for efficient revision.
- **Multilingual Support:** Translate content into various languages.
- **Document Sharing:** Collaborate by sharing processed documents via email.
- **Text Complexity Analysis:** Gain insights into the readability of your materials.
- **Key Concept Extraction:** Identify crucial ideas at a glance.
- **Audio Learning:** Convert text to speech for on-the-go studying. (**Coming Soon**)
- **Progress Tracking:** Maintain a comprehensive chat history of your learning journey.

## 🛠️ Technology Stack

- **Core:** `Python 3.11`
- **Framework:** `Streamlit`
- **AI Model:** `Google Gemini Pro`
- **NLP & ML:** `LangChain`, `Transformers`, `Scikit-learn`
- **Data Processing:** `PyPDF2`, `FAISS`
- **Visualization:** `Matplotlib`, `Seaborn`
- **Audio:** `gTTS` (Google Text-to-Speech)

## 🚀 Getting Started

1. **Clone & Setup:**
   ```bash
   git clone https://github.com/anubhab-m02/PDF-QnA.git
   cd PDF-QnA
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

2. **API Configuration:**
   - Obtain a Google Cloud API key with Gemini Pro access.
   - Create a `.env` file in the project root:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

3. **Launch:**
   ```bash
   streamlit run app.py
   ```

## 💡 Usage Guide

1. **Document Upload:** Use the sidebar to upload your PDF documents.
2. **Processing:** Click "Process Documents" to analyze your materials.
3. **Feature Selection:** Choose from a variety of learning tools in the main interface.
4. **Interaction:** Engage with the AI assistant through your chosen feature.

## 🔐 Security & Performance

- **Safe Deserialization:** Exercise caution with `allow_dangerous_deserialization=True`. Only use with trusted FAISS index sources.
- **Efficient Indexing:** The FAISS index updates incrementally, preserving knowledge from all uploaded documents.
- **Automatic Cleanup:** Old data and large caches are periodically removed to maintain performance.

## 🤝 Contributing

Contributions are welcome! Whether it's feature suggestions, bug reports, or code improvements, please feel free to open an issue or submit a pull request.
