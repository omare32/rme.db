import os
import json
import openai
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from tqdm import tqdm

# Load OpenAI API key from .env
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# New paths outside the repo
EXTRACTED_DIR = r'C:/Users/Omar Essam2/OneDrive - Rowad Modern Engineering/x004 Data Science/03.rme.db/05.llm/extracted_json'
CHROMA_DB_DIR = r'C:/Users/Omar Essam2/OneDrive - Rowad Modern Engineering/x004 Data Science/03.rme.db/05.llm/chroma_db'
COLLECTION_NAME = 'company_docs'
CHUNK_SIZE = 1000  # characters per chunk
CHUNK_OVERLAP = 200

# Helper: chunk text
def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

# Helper: get OpenAI embeddings
def get_embedding(text):
    resp = openai.embeddings.create(
        input=[text],
        model="text-embedding-ada-002"
    )
    return resp.data[0].embedding

# Initialize Chroma DB
client = chromadb.PersistentClient(path=CHROMA_DB_DIR, settings=Settings(allow_reset=True))
if COLLECTION_NAME in [c.name for c in client.list_collections()]:
    collection = client.get_collection(COLLECTION_NAME)
else:
    collection = client.create_collection(COLLECTION_NAME)

def get_existing_ids(collection):
    # Get all existing IDs in the collection
    # Chroma doesn't have a direct way to list all IDs, so we use get() with a large limit
    try:
        results = collection.get(include=["ids"], limit=1000000)
        return set(results["ids"])
    except Exception:
        return set()

def process_json_files():
    files = [f for f in os.listdir(EXTRACTED_DIR) if f.endswith('.json')]
    doc_count = 0
    existing_ids = get_existing_ids(collection)
    for file in files:
        with open(os.path.join(EXTRACTED_DIR, file), 'r', encoding='utf-8') as f:
            docs = json.load(f)
        for doc in tqdm(docs, desc=f"Processing {file}"):
            text = doc['text']
            if not text.strip():
                continue
            chunks = chunk_text(text)
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc['file_name']}_{i}_{doc_count}"
                if chunk_id in existing_ids:
                    continue  # Skip already embedded chunk
                meta = {
                    'file_name': doc['file_name'],
                    'file_path': doc['file_path'],
                    'type': doc['type'],
                    'extracted_at': doc['extracted_at'],
                    'chunk': i
                }
                try:
                    emb = get_embedding(chunk)
                    collection.add(
                        documents=[chunk],
                        embeddings=[emb],
                        metadatas=[meta],
                        ids=[chunk_id]
                    )
                    doc_count += 1
                except Exception as e:
                    print(f"Error embedding chunk: {e}")
    print(f"Finished! {doc_count} new chunks embedded and stored in Chroma DB.")

if __name__ == "__main__":
    process_json_files() 