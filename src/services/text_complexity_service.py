import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from utils.logging_config import logger

def analyze_text_complexity(text):
    """Analyze the complexity of the text."""
    sentences = text.split('.')
    word_counts = [len(sentence.split()) for sentence in sentences if sentence.strip()]
    avg_words_per_sentence = sum(word_counts) / len(word_counts)
    
    words = text.split()
    avg_word_length = sum(len(word) for word in words) / len(words)
    
    complexity_score = (avg_words_per_sentence * 0.5) + (avg_word_length * 5)
    
    return {
        "avg_words_per_sentence": avg_words_per_sentence,
        "avg_word_length": avg_word_length,
        "complexity_score": complexity_score
    }

def visualize_text_complexity(complexity_data):
    """Visualize the text complexity data."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create a bar plot for all metrics
    metrics = ['avg_words_per_sentence', 'avg_word_length', 'complexity_score']
    values = [complexity_data[metric] for metric in metrics]
    
    sns.barplot(x=metrics, y=values, ax=ax)
    ax.set_title('Text Complexity Metrics')
    ax.set_ylabel('Value')
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels on top of each bar
    for i, v in enumerate(values):
        ax.text(i, v, f'{v:.2f}', ha='center', va='bottom')
    
    # Add a color-coded text for complexity score
    complexity_score = complexity_data['complexity_score']
    if complexity_score < 10:
        color = 'green'
        label = 'Low'
    elif complexity_score < 15:
        color = 'orange'
        label = 'Medium'
    else:
        color = 'red'
        label = 'High'
    
    plt.text(0.5, -0.15, f'Complexity: {label} ({complexity_score:.2f})', 
             color=color, fontsize=12, ha='center', transform=ax.transAxes)
    
    plt.tight_layout()
    st.pyplot(fig)
