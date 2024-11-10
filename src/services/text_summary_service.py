import google.generativeai as genai
import traceback
from utils.logging_config import logger

def summarize_document(text):
    """Summarize the uploaded document using Gemini API."""
    if not text or len(text) < 30:
        logger.error("Input text is too short for summarization.")
        return "Input text is too short for summarization."
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-002')
        prompt = f"""
        Please provide a concise summary of the following text. The summary should capture the main points and key ideas:

        {text}

        Summary:
        """
        
        response = model.generate_content(prompt)
        
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                summary = ' '.join(part.text for part in candidate.content.parts)
                logger.info(f"Generated summary: {summary}")
                return summary
        
        return "Unable to generate summary."
    except Exception as e:
        logger.error(f"Error during summarization: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Error during summarization: {str(e)}"