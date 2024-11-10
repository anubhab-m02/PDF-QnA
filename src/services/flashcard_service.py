from typing import List, Dict, Tuple
from utils.logging_config import logger
from services.ai_service import ai_service
import google.generativeai as genai
import traceback

class FlashcardService:
    def generate_flashcards(self, context, iteration=0):
        """Generate flashcards from the document content."""
        if not context or len(context) < 100:
            logger.error("Input text is too short for generating flashcards.")
            return [], "Input text is too short."

        model = genai.GenerativeModel('gemini-1.5-flash-002')
        flashcard_prompt = f"""
        Based on the following context, generate 5 different flashcards with key terms or concepts and their definitions.
        Each flashcard should contain a term and its corresponding definition.
        Make sure to generate different flashcards than previous attempts (this is attempt #{iteration}).
        Focus on different aspects of the content for variety.
        
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

# Create singleton instance
flashcard_service = FlashcardService()