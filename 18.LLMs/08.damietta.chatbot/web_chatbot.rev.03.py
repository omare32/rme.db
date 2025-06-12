import os
import glob
from docx import Document
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import subprocess
import gradio as gr

# === CONFIG ===
WORD_DOCS_DIR = r'D:\OEssam\Test\gemma3-3rd-time'
DEFAULT_MODEL = 'gemma3:latest'  # Changed default model to gemma3
EMBED_MODEL = 'all-MiniLM-L6-v2'
TOP_K = 3

# === 1. Extract summaries from Word files ===
def extract_summaries(word_docs_dir):
    summaries = []
    for path in glob.glob(os.path.join(word_docs_dir, '*.docx')):
        doc = Document(path)
        summary_text = ''
        in_summary = False
        for para in doc.paragraphs:
            if 'Final Comprehensive Summary' in para.text:
                in_summary = True
                continue
            if in_summary:
                if para.text.strip() == '':
                    break
                summary_text += para.text + '\n'
        if summary_text.strip():
            summaries.append({'doc': os.path.basename(path), 'path': path, 'summary': summary_text.strip()})
    return summaries

# ... rest of the code remains unchanged ...

# Make sure to launch Gradio with server_name="0.0.0.0" and server_port=7860 as in rev.02
