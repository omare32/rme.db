import os
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
import openai
import requests
from flask import Flask, render_template_string, request, send_file
from urllib.parse import quote

# Load OpenAI API key from .env
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Chroma DB paths
CHROMA_DB_DIR = r'C:/Users/Omar Essam2/OneDrive - Rowad Modern Engineering/x004 Data Science/03.rme.db/05.llm/chroma_db'
COLLECTION_NAME = 'company_docs'
OLLAMA_URL = 'http://localhost:11434/api/generate'
MISTRAL_MODEL = 'mistral:latest'

def get_mistral_version():
    try:
        r = requests.get('http://localhost:11434/api/tags', timeout=5)
        if r.status_code == 200:
            models = r.json().get('models', [])
            for model in models:
                if model['name'].startswith('mistral'):
                    details = model.get('details', {})
                    param_size = details.get('parameter_size', '7B')
                    return f"Mistral v.{param_size}"
            return 'Mistral v.7B'
        else:
            return 'Mistral v.7B'
    except Exception:
        return 'Mistral v.7B'

# Web app
app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RME Company Knowledge Q&A</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f6fb; margin: 0; padding: 0; }
        .container { max-width: 700px; margin: 40px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 8px #0001; padding: 32px; }
        h1 { text-align: center; color: #333; }
        .llm-info { text-align: center; background: #e0e7ff; color: #222; border-radius: 6px; padding: 8px 0; margin-bottom: 24px; font-weight: bold; }
        textarea { width: 100%; min-height: 80px; padding: 10px; border-radius: 6px; border: 1px solid #ccc; font-size: 1rem; }
        .btn-row { display: flex; gap: 12px; margin-top: 12px; }
        button { background: #4f8cff; color: #fff; border: none; padding: 12px 24px; border-radius: 6px; font-size: 1rem; cursor: pointer; }
        button:hover { background: #2563eb; }
        .gpt-btn { background: #ffd700; color: #222; font-weight: bold; }
        .gpt-btn:hover { background: #ffb300; }
        .response { margin-top: 24px; background: #f0f4fa; padding: 16px; border-radius: 6px; white-space: pre-wrap; font-size: 1.05rem; }
        .sources { margin-top: 16px; font-size: 0.98rem; }
        .source-link { color: #2563eb; text-decoration: underline; }
        label { font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>RME Company Knowledge Q&amp;A</h1>
        <div class="llm-info">Using Local LLM: {{ mistral_version }}</div>
        <form method="post">
            <label for="question">Ask a question:</label><br>
            <textarea id="question" name="question" required>{{ question or '' }}</textarea><br>
            <div class="btn-row">
                <button type="submit" name="llm" value="mistral">Ask (Local LLM)</button>
                <button type="submit" name="llm" value="gpt" class="gpt-btn">Ask GPT (💲)</button>
            </div>
        </form>
        {% if answer %}
        <div class="response">
            <strong>Answer:</strong><br>
            {{ answer }}
        </div>
        {% endif %}
        {% if sources %}
        <div class="sources">
            <strong>Sources:</strong><br>
            {% for src in sources %}
                <div>- <a class="source-link" href="/open_file?path={{ src['file_path'] | urlencode }}" target="_blank">{{ src['file_name'] }}</a> ({{ src['file_path'] }})</div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

# Helper: search Chroma DB
def search_chroma(query, top_k=5):
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR, settings=Settings(allow_reset=True))
    collection = client.get_collection(COLLECTION_NAME)
    # Embed the query
    emb = openai.embeddings.create(input=[query], model="text-embedding-ada-002").data[0].embedding
    results = collection.query(query_embeddings=[emb], n_results=top_k, include=['documents', 'metadatas'])
    docs = results['documents'][0]
    metas = results['metadatas'][0]
    return list(zip(docs, metas))

# Helper: ask Mistral (Ollama)
def ask_mistral(question, context_chunks):
    context = "\n\n".join(context_chunks)
    prompt = f"You are a helpful assistant for a construction company. Use the following context to answer the question.\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                'model': MISTRAL_MODEL,
                'prompt': prompt,
                'stream': False
            },
            timeout=120
        )
        if r.status_code == 200:
            return r.json().get('response', '(No response)')
        else:
            return f"Ollama API error: {r.status_code}"
    except Exception as e:
        return f"Error: {e}"

# Helper: ask OpenAI with context
def ask_openai(question, context_chunks):
    context = "\n\n".join(context_chunks)
    prompt = f"You are a helpful assistant for a construction company. Use the following context to answer the question.\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
    resp = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.2
    )
    return resp.choices[0].message.content.strip()

@app.route('/', methods=['GET', 'POST'])
def index():
    answer = None
    sources = None
    question = None
    mistral_version = get_mistral_version()
    if request.method == 'POST':
        question = request.form['question']
        llm = request.form.get('llm', 'mistral')
        results = search_chroma(question, top_k=5)
        context_chunks = [doc for doc, meta in results]
        if llm == 'gpt':
            answer = ask_openai(question, context_chunks)
        else:
            answer = ask_mistral(question, context_chunks)
        # Collect unique sources
        seen = set()
        sources = []
        for doc, meta in results:
            key = meta['file_path']
            if key not in seen:
                sources.append({'file_name': meta['file_name'], 'file_path': meta['file_path']})
                seen.add(key)
    return render_template_string(HTML, answer=answer, sources=sources, question=question, mistral_version=mistral_version)

@app.route('/open_file')
def open_file():
    import sys
    import subprocess
    path = request.args.get('path')
    if not path:
        return "No file path provided.", 400
    # Try to open the file using the default application
    try:
        if os.name == 'nt':  # Windows
            os.startfile(path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.call(['open', path])
        else:  # Linux
            subprocess.call(['xdg-open', path])
        return f"Opened {path}", 200
    except Exception as e:
        return f"Failed to open file: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True) 