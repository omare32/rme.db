import os
import os
import json
import networkx as nx
from datetime import datetime
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from io import BytesIO
from langchain_community.document_loaders.base import BaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM
from langchain.chains import RetrievalQA
from langchain_community.graphs import NetworkxEntityGraph

class OCRPDFLoader(BaseLoader):
    def __init__(self, file_path):
        self.file_path = file_path
        # Set Tesseract path - update this to your Tesseract installation path
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
    def load(self):
        # Convert PDF to images
        try:
            # Set poppler path - update this to your Poppler installation path
            images = convert_from_path(self.file_path, poppler_path=r'C:\Program Files\poppler-24.08.0\Library\bin')
        except Exception as e:
            print(f"Error converting PDF to images: {str(e)}")
            return []
            
        documents = []
        for i, image in enumerate(images):
            try:
                # Perform OCR with support for multiple languages (English and Arabic)
                text = pytesseract.image_to_string(image, lang='eng+ara')
                if text.strip():
                    doc = Document(
                        page_content=text,
                        metadata={"source": self.file_path, "page": i + 1}
                    )
                    documents.append(doc)
                    print(f"  Page {i+1}: {len(text)} characters")
                else:
                    print(f"  Page {i+1}: No text extracted")
            except Exception as e:
                print(f"Error processing page {i+1}: {str(e)}")
                
        return documents

class GraphRAG:
    def __init__(self, model_name="mistral", pdf_directory=None):
        self.model_name = model_name
        self.pdf_directory = pdf_directory or "D:\\OEssam\\01.pdfs"
        # Use a multilingual model for embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
        self.llm = OllamaLLM(model=model_name)
        self.graph = NetworkxEntityGraph()
        self.vector_store = None
        self.po_data = {}
        
    def extract_po_details(self, text):
        """Extract purchase order details using structured prompts"""
        prompt = f"""Extract the following information from this purchase order text. Return as JSON with these keys:
        - po_number: The purchase order number
        - date: The PO date
        - supplier: The supplier/company name
        - total_amount: The total amount with currency
        - items: List of items with quantities and prices

Text: {text}

JSON Output:"""
        
        try:
            response = self.llm.predict(prompt)
            # Try to find the JSON part in the response
            json_match = re.search(r'\{[^}]+\}', response.replace('\n', ' '))
            if json_match:
                data = json.loads(json_match.group())
                return data
        except:
            pass
        return None
        
    def load_pdfs(self):
        """Load PDF files from the specified directory"""
        if not os.path.exists(self.pdf_directory):
            raise ValueError(f"PDF directory not found: {self.pdf_directory}")
            
        documents = []
        pdf_files = [f for f in os.listdir(self.pdf_directory) if f.endswith(".pdf")]
        
        if not pdf_files:
            raise ValueError(f"No PDF files found in {self.pdf_directory}")
            
        for file in pdf_files:
            try:
                file_path = os.path.join(self.pdf_directory, file)
                loader = OCRPDFLoader(file_path)
                docs = loader.load()
                
                if docs:
                    print(f"\nLoaded {file} with {len(docs)} pages")
                    # Debug: Check content of each page
                    for i, doc in enumerate(docs):
                        content = doc.page_content.strip()
                        if content:
                            print(f"  Page {i+1}: {len(content)} characters")
                            documents.append(doc)
                        else:
                            print(f"  Page {i+1}: Empty content")
                            
            except Exception as e:
                print(f"Error loading {file}: {str(e)}")
                
        if not documents:
            raise ValueError("No content could be loaded from PDF files")
            
        print(f"\nSuccessfully loaded {len(documents)} pages with content")
        return documents
    
    def split_documents(self, documents, chunk_size=1000, chunk_overlap=200):
        """Split documents into chunks"""
        if not documents:
            raise ValueError("No documents to split")
            
        try:
            # Debug: Check content before splitting
            total_chars = sum(len(doc.page_content) for doc in documents)
            print(f"\nTotal characters before splitting: {total_chars}")
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""],
                length_function=len,
                is_separator_regex=False
            )
            
            chunks = text_splitter.split_documents(documents)
            
            # Debug: Check content after splitting
            if chunks:
                print(f"\nSplit {len(documents)} documents into {len(chunks)} chunks")
                print(f"First chunk preview: {chunks[0].page_content[:100]}...")
            else:
                raise ValueError("Splitting produced no chunks")
                
            return chunks
        except Exception as e:
            print(f"Error splitting documents: {str(e)}")
            raise
    
    def create_vector_store(self, documents):
        """Create FAISS vector store from documents"""
        if not documents:
            raise ValueError("No documents provided for vector store creation")
            
        try:
            texts = [doc.page_content for doc in documents]
            if not any(texts):
                raise ValueError("Documents contain no text content")
                
            print(f"Creating vector store from {len(documents)} documents")
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
            print("Vector store created successfully")
        except Exception as e:
            print(f"Error creating vector store: {str(e)}")
            raise
        
    def extract_entities_and_relationships(self, text, po_data=None):
        """Extract entities and relationships with business context"""
        context = ""
        if po_data:
            context = f"\nThis is from PO number {po_data.get('po_number', 'unknown')} "
            context += f"issued to {po_data.get('supplier', 'unknown')} "
            context += f"on {po_data.get('date', 'unknown')}"
        
        prompt = f"""Extract key business entities and their relationships from this purchase order text.
        Consider these relationship types:
        - supplies_to (between supplier and buyer)
        - ordered_by (between items and company)
        - has_value (between PO and amount)
        - dated_on (between PO and date)
        - includes (between PO and items)
        
        Format: Entity1 | Relationship | Entity2
        Text: {text}{context}
        
        Entities and Relationships:"""
        
        response = self.llm.predict(prompt)
        relationships = []
        
        for line in response.split('\n'):
            if '|' in line:
                try:
                    entity1, relation, entity2 = [x.strip() for x in line.split('|')]
                    relationships.append((entity1, relation, entity2))
                except:
                    continue
                
        return relationships
    
    def build_knowledge_graph(self, documents):
        """Build knowledge graph from documents with PO context"""
        for doc in documents:
            # First extract structured PO data
            po_data = self.extract_po_details(doc.page_content)
            if po_data:
                po_number = po_data.get('po_number', 'unknown_po')
                self.po_data[po_number] = po_data
                
                # Add basic PO information to graph
                self.graph.add_triple(po_number, 'issued_to', po_data.get('supplier', 'unknown'))
                self.graph.add_triple(po_number, 'dated_on', po_data.get('date', 'unknown'))
                self.graph.add_triple(po_number, 'has_value', str(po_data.get('total_amount', '0')))
                
                # Add items
                for item in po_data.get('items', []):
                    item_str = json.dumps(item, ensure_ascii=False)
                    self.graph.add_triple(po_number, 'includes', item_str)
            
            # Then extract general relationships
            relationships = self.extract_entities_and_relationships(doc.page_content, po_data)
            for entity1, relation, entity2 in relationships:
                self.graph.add_triple(entity1, relation, entity2)
    
    def query(self, question, use_graph=True, k=3):
        """Query the system using both vector store and knowledge graph"""
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Run process_documents first.")
            
        # Get relevant documents
        docs = self.vector_store.similarity_search(question, k=k)
        context = "\n".join([doc.page_content for doc in docs])
        
        if use_graph:
            # Get relevant graph context
            graph_context = self.graph.get_relevant_subgraph(question)
            context += f"\nKnowledge Graph Information:\n{graph_context}"
        
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever()
        )
        
        return qa_chain.run(question)
    
    def process_documents(self):
        """Main method to process documents and build both vector store and knowledge graph"""
        try:
            # Load PDFs
            documents = self.load_pdfs()
            print(f"\nTotal documents loaded: {len(documents)}")
            
            # Split into chunks
            print("\nSplitting documents into chunks...")
            chunks = self.split_documents(documents)
            
            # Create vector store
            print("\nCreating vector store...")
            self.create_vector_store(chunks)
            
            # Build knowledge graph
            print("\nBuilding knowledge graph...")
            self.build_knowledge_graph(chunks)
            
            print("\nDocument processing complete!")
        except Exception as e:
            print(f"\nError in document processing: {str(e)}")
            raise
        
def main():
    try:
        # Initialize GraphRAG
        print("Initializing GraphRAG...")
        rag = GraphRAG(model_name="mistral", pdf_directory="D:\\OEssam\\01.pdfs")
        
        # Process documents
        print("\nProcessing documents...")
        rag.process_documents()
        
        # Example queries
        print("\nRunning example queries...")
        questions = [
            "List all suppliers and their total order values",
            "What are the most commonly ordered items?",
            "What is the total value of all purchase orders?",
            "Show me the details of the latest purchase order"
        ]
        
        for question in questions:
            print(f"\nQ: {question}")
            try:
                answer = rag.query(question)
                print(f"A: {answer}")
            except Exception as e:
                print(f"Error processing query: {str(e)}")
                
    except Exception as e:
        print(f"\nError: {str(e)}")
        raise

if __name__ == "__main__":
    main()