import os
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
import openai
import requests
from flask import Flask, render_template_string, request, send_file
from urllib.parse import quote
import json
import re

# Load OpenAI API key from .env
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Chroma DB paths (LOCAL)
CHROMA_DB_DIR = r'C:/Users/Omar Essam2/OneDrive - Rowad Modern Engineering/x004 Data Science/03.rme.db/05.llm/chroma_db_local'
COLLECTION_NAME = 'company_docs'
OLLAMA_URL = 'http://localhost:11434/api/generate'
MISTRAL_MODEL = 'mistral:latest'

TRAIN_LOG_DIR = r'C:/Users/Omar Essam2/OneDrive - Rowad Modern Engineering/x004 Data Science/03.rme.db/05.llm/gpt.tuning'
LOG_FILE = os.path.join(TRAIN_LOG_DIR, 'gpt_feedback_log.jsonl')
os.makedirs(TRAIN_LOG_DIR, exist_ok=True)

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
    <title>RME Company Knowledge Q&A (Local DB)</title>
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
        <h1>RME Company Knowledge Q&amp;A (Local DB)</h1>
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
                <div>- <a class="source-link" href="/serve_pdf?path={{ src['file_path'] | urlencode }}" target="_blank">{{ src['file_name'] }}</a> ({{ src['file_path'] }})</div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

def extract_project_name_from_question(question):
    # Simple heuristic: look for words like 'project', 'port', 'lot', 'zed', etc.
    keywords = r'(project|port|lot|zed|damietta|rashwan|saint gobain|ring road|silos|dashboard|sector|global|company)'
    match = re.search(rf'([A-Za-z0-9\- ]*{keywords}[A-Za-z0-9\- ]*)', question, re.IGNORECASE)
    if match:
        return match.group(0).strip().lower()
    return None

def search_chroma_with_project(query, top_k=10):
    project_name = extract_project_name_from_question(query)
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR, settings=Settings(allow_reset=True))
    collection = client.get_collection(COLLECTION_NAME)
    emb = openai.embeddings.create(input=[query], model="text-embedding-ada-002").data[0].embedding
    results = collection.query(query_embeddings=[emb], n_results=top_k, include=['documents', 'metadatas'])
    docs = results['documents'][0]
    metas = results['metadatas'][0]
    # Filter or boost by project name
    if project_name:
        filtered = [(doc, meta) for doc, meta in zip(docs, metas) if meta.get('project', '').lower() == project_name]
        if filtered:
            return filtered[:5]  # Return top 5 matching project
    # Fallback: return top 5 as is
    return list(zip(docs, metas))[:5]

def ask_mistral(question, context_chunks, project_name=None):
    context = "\n\n".join(context_chunks)
    project_str = f"Project: {project_name}\n" if project_name else ""
    prompt = f"You are a helpful assistant for a construction company. Only answer if the context is about the correct project.\n{project_str}Use the following context to answer the question.\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
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

def ask_openai(question, context_chunks, project_name=None):
    context = "\n\n".join(context_chunks)
    project_str = f"Project: {project_name}\n" if project_name else ""
    prompt = f"You are a helpful assistant for a construction company. Only answer if the context is about the correct project.\n{project_str}Use the following context to answer the question.\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
    resp = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.2
    )
    return resp.choices[0].message.content.strip()

def log_gpt_feedback(context_chunks, question, answer):
    record = {
        'context': context_chunks,
        'question': question,
        'answer': answer
    }
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')

@app.route('/', methods=['GET', 'POST'])
def index():
    answer = None
    sources = None
    question = None
    mistral_version = get_mistral_version()
    if request.method == 'POST':
        question = request.form['question']
        llm = request.form.get('llm', 'mistral')
        project_name = extract_project_name_from_question(question)
        results = search_chroma_with_project(question, top_k=10)
        context_chunks = [doc for doc, meta in results]
        if llm == 'gpt':
            answer = ask_openai(question, context_chunks, project_name)
            log_gpt_feedback(context_chunks, question, answer)
        else:
            answer = ask_mistral(question, context_chunks, project_name)
        # Collect unique sources
        seen = set()
        sources = []
        for doc, meta in results:
            key = meta['file_path']
            if key not in seen:
                sources.append({'file_name': meta['file_name'], 'file_path': meta['file_path']})
                seen.add(key)
    return render_template_string(HTML, answer=answer, sources=sources, question=question, mistral_version=mistral_version)

@app.route('/serve_pdf')
def serve_pdf():
    from flask import send_file, abort
    import urllib.parse
    path = request.args.get('path')
    if not path or not os.path.isfile(path):
        return abort(404)
    try:
        return send_file(path, mimetype='application/pdf', as_attachment=False)
    except Exception as e:
        return f"Failed to serve file: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True) 