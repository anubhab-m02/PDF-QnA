from gtts import gTTS
import os
import traceback
import time
from utils.logging_config import logger
from config.settings import SPEECH_CHUNK_SIZE, MAX_RETRIES

class SpeechService:
    def text_to_speech(self, text: str, language: str = 'en') -> str:
        """Convert text to speech and save as MP3."""
        try:
            if not text:
                return None
            
            # Split text into chunks if it's too long
            chunks = [text[i:i+SPEECH_CHUNK_SIZE] for i in range(0, len(text), SPEECH_CHUNK_SIZE)]
            
            audio_files = []
            for i, chunk in enumerate(chunks):
                retry_count = 0
                while retry_count < MAX_RETRIES:
                    try:
                        tts = gTTS(text=chunk, lang=language)
                        filename = f"audio_output/speech_{i}.mp3"
                        tts.save(filename)
                        audio_files.append(filename)
                        time.sleep(1)  # Add a delay between requests
                        break
                    except Exception as e:
                        logger.error(f"Error in text-to-speech conversion: {str(e)}")
                        retry_count += 1
                        time.sleep(2 ** retry_count)  # Exponential backoff
                
                if retry_count == MAX_RETRIES:
                    logger.error(f"Failed to convert chunk {i} after {MAX_RETRIES} retries")
            
            if not audio_files:
                return None
            
            # Combine audio files
            combined_audio = f"combined_output.mp3"
            os.makedirs('audio_output', exist_ok=True)
            with open(combined_audio, 'wb') as outfile:
                for fname in audio_files:
                    with open(fname, 'rb') as infile:
                        outfile.write(infile.read())
            
            # Clean up individual chunk files
            for file in audio_files:
                os.remove(file)
            
            logger.info(f"Generated speech file: {combined_audio}")
            return combined_audio
        
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def cleanup_audio_files(self):
        """Remove old audio files."""
        try:
            if os.path.exists('audio_output'):
                for file in os.listdir('audio_output'):
                    if file.endswith('.mp3'):
                        os.remove(os.path.join('audio_output', file))
            logger.info("Cleaned up audio files")
        except Exception as e:
            logger.error(f"Error cleaning up audio files: {str(e)}")

# Create singleton instance
speech_service = SpeechService()
