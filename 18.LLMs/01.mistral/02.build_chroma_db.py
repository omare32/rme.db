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
CHUNK_SIZE = 500  # characters per chunk (reduced for more precise retrieval)
CHUNK_OVERLAP = 200
ID_TRACK_FILE = os.path.join(CHROMA_DB_DIR, 'embedded_chunk_ids.txt')
BATCH_SIZE = 32  # Number of chunks to embed in one API call

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

def get_embeddings(texts):
    resp = openai.embeddings.create(
        input=texts,
        model="text-embedding-ada-002"
    )
    return [item.embedding for item in resp.data]

# Initialize Chroma DB
client = chromadb.PersistentClient(path=CHROMA_DB_DIR, settings=Settings(allow_reset=True))
if COLLECTION_NAME in [c.name for c in client.list_collections()]:
    collection = client.get_collection(COLLECTION_NAME)
else:
    collection = client.create_collection(COLLECTION_NAME)

def load_embedded_ids():
    if not os.path.exists(ID_TRACK_FILE):
        return set()
    with open(ID_TRACK_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def save_embedded_id(chunk_id):
    with open(ID_TRACK_FILE, 'a', encoding='utf-8') as f:
        f.write(chunk_id + '\n')

def process_json_files():
    files = [f for f in os.listdir(EXTRACTED_DIR) if f.endswith('.json')]
    doc_count = 0
    embedded_ids = load_embedded_ids()
    for file in files:
        with open(os.path.join(EXTRACTED_DIR, file), 'r', encoding='utf-8') as f:
            docs = json.load(f)
        for doc in tqdm(docs, desc=f"Processing {file}"):
            text = doc['text']
            if not text.strip():
                continue
            chunks = chunk_text(text)
            batch_chunks = []
            batch_metas = []
            batch_ids = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc['file_name']}_{i}"
                if chunk_id in embedded_ids:
                    continue  # Skip already embedded chunk
                meta = {
                    'file_name': doc['file_name'],
                    'file_path': doc['file_path'],
                    'type': doc['type'],
                    'project': doc.get('project', 'GLOBAL'),
                    'extracted_at': doc['extracted_at'],
                    'chunk': i
                }
                batch_chunks.append(chunk)
                batch_metas.append(meta)
                batch_ids.append(chunk_id)
                if len(batch_chunks) == BATCH_SIZE:
                    try:
                        embs = get_embeddings(batch_chunks)
                        collection.add(
                            documents=batch_chunks,
                            embeddings=embs,
                            metadatas=batch_metas,
                            ids=batch_ids
                        )
                        for cid in batch_ids:
                            save_embedded_id(cid)
                        doc_count += len(batch_chunks)
                    except Exception as e:
                        print(f"Error embedding batch: {e}")
                    batch_chunks, batch_metas, batch_ids = [], [], []
            # Process any remaining chunks in the batch
            if batch_chunks:
                try:
                    embs = get_embeddings(batch_chunks)
                    collection.add(
                        documents=batch_chunks,
                        embeddings=embs,
                        metadatas=batch_metas,
                        ids=batch_ids
                    )
                    for cid in batch_ids:
                        save_embedded_id(cid)
                    doc_count += len(batch_chunks)
                except Exception as e:
                    print(f"Error embedding batch: {e}")
    print(f"Finished! {doc_count} new chunks embedded and stored in Chroma DB.")

if __name__ == "__main__":
    process_json_files() 