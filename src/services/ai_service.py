import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from utils.logging_config import logger
from config.settings import GOOGLE_API_KEY

class AIService:
    def get_gemini_response(self, question, context):
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

    def user_input(self, user_question):
        """Handle user input and generate a response based on the question."""
        try:
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
            docs = new_db.similarity_search(user_question, k=2)
            context = "\n".join([doc.page_content for doc in docs])
            logger.info(f"Retrieved context: {context}...")
            response = self.get_gemini_response(user_question, context)
            return {"output_text": response}
        except Exception as e:
            logger.error(f"Error in user_input: {str(e)}")
            return {"output_text": f"An error occurred: {str(e)}"}

# Create a singleton instance
ai_service = AIService()