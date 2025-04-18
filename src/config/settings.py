import os
from dotenv import load_dotenv
import google.generativeai as genai
import torch

# Load environment variables
load_dotenv()

# Configure Google Generative AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Email configuration
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

# Device configuration
DEVICE = 0 if torch.cuda.is_available() else -1

# Constants
MAX_PAGES = 1000
MAX_CHARS = 100000000000000
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
TRANSLATION_CHUNK_SIZE = 4000
SPEECH_CHUNK_SIZE = 5000
MAX_RETRIES = 3
