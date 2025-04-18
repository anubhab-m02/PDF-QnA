import google.generativeai as genai
from typing import List, Dict
import traceback
from utils.logging_config import logger
from services.profile_service import profile_service

class QuizService:
    def generate_quiz(self, context: str, username: str = None) -> List[Dict]:
        """
        Generate quiz questions from the document content.
        
        Args:
            context (str): The document content to generate questions from
            username (str, optional): The username to check for previously asked questions
            
        Returns:
            List[Dict]: List of generated quiz questions
        """
        if not context or len(context) < 100:
            logger.error("Input text is too short for generating quiz.")
            return []

        try:
            # Get previously asked questions if username is provided
            previously_asked = []
            if username:
                previously_asked = profile_service.get_previously_asked_questions(username)
                
            model = genai.GenerativeModel('gemini-1.5-flash-002')
            
            # Add instruction to avoid repeating questions if there are previous questions
            avoid_repetition = ""
            if previously_asked and len(previously_asked) > 0:
                # Extract question texts from previously asked questions
                prev_question_texts = [q.get('question', '') for q in previously_asked if 'question' in q]
                if prev_question_texts:
                    avoid_repetition = f"""
                    IMPORTANT: Do NOT generate questions similar to these previously asked questions:
                    {prev_question_texts[:10]}  # Limit to 10 questions to avoid token limits
                    
                    Generate completely new and different questions.
                    """
            
            quiz_prompt = f"""
            Based on the following context, generate 5 multiple-choice questions to test understanding.
            Each question should have 4 options with only one correct answer.
            
            Context: {context}
            
            {avoid_repetition}
            
            Format each question as follows:
            Question: [Question text]
            A) [Option A]
            B) [Option B]
            C) [Option C]
            D) [Option D]
            Correct Answer: [Correct option letter]
            
            Please provide exactly 5 questions.
            """

            response = model.generate_content(quiz_prompt)
            logger.info("Received response from model")

            if response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    quiz_text = candidate.content.parts[0].text
                    questions = []
                    current_question = {}

                    for line in quiz_text.split('\n'):
                        line = line.strip()
                        if not line:
                            continue

                        if line.startswith('Question:'):
                            if current_question:
                                questions.append(current_question)
                            current_question = {
                                'question': line[len('Question:'):].strip(),
                                'options': [],
                                'correct_answer': None
                            }
                        elif line.startswith(('A)', 'B)', 'C)', 'D)')):
                            current_question['options'].append(line[2:].strip())
                        elif line.startswith('Correct Answer:'):
                            current_question['correct_answer'] = line[len('Correct Answer:'):].strip()

                    if current_question:
                        questions.append(current_question)

                    logger.info(f"Generated {len(questions)} questions")
                    return questions

            logger.error("Failed to generate quiz questions")
            return []

        except Exception as e:
            logger.error(f"Error generating quiz: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    def check_answer(self, question: Dict, user_answer: str) -> bool:
        """Check if the user's answer is correct."""
        return user_answer.upper() == question['correct_answer'].upper()

# Create singleton instance
quiz_service = QuizService()
