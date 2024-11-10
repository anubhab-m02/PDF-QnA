import os
import time
import shutil
from utils.logging_config import logger

def cleanup_old_data():
    # Remove old FAISS index files
    if os.path.exists("faiss_index"):
        if time.time() - os.path.getmtime("faiss_index") > 24 * 60 * 60:  # 24 hours
            shutil.rmtree("faiss_index")
            logger.info("Removed old FAISS index")

    # Clear Streamlit cache if it's too large
    cache_path = os.path.join(os.path.expanduser("~"), ".streamlit/cache")
    if os.path.exists(cache_path):
        cache_size = sum(os.path.getsize(os.path.join(dirpath,filename)) 
                        for dirpath, dirnames, filenames in os.walk(cache_path) 
                        for filename in filenames)
        if cache_size > 1e9:  # 1 GB
            shutil.rmtree(cache_path)
            logger.info("Cleared Streamlit cache due to large size")
