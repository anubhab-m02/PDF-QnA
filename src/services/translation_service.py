from deep_translator import GoogleTranslator
import traceback
from utils.logging_config import logger

class TranslationService:
    def translate_text(self, text, dest_language):
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

# Create singleton instance
translation_service = TranslationService()
