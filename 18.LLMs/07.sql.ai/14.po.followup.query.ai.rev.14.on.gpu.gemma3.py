import gradio as gr
import mysql.connector
from mysql.connector import Error
import os
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
import requests
import difflib

# Load environment variables
load_dotenv()

DB_CONFIG = {
    'host': '10.10.11.242',
    'user': 'omar2',
    'password': 'Omar_54321',
    'database': 'RME_TEST'
}

OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "gemma3:latest"

NEW_TABLE = "po_followup_merged"

# Fetch and cache unique projects and suppliers at startup
def fetch_unique_list(column: str) -> list:
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(f"SELECT DISTINCT {column} FROM {NEW_TABLE} WHERE {column} IS NOT NULL AND {column} != '' ORDER BY {column}")
        results = [row[0] for row in cursor.fetchall() if row[0]]
        return results
    except Exception as e:
        print(f"Error fetching unique {column}: {e}")
        return []
    finally:
        if connection:
            connection.close()

def initialize_unique_lists():
    global UNIQUE_PROJECTS, UNIQUE_SUPPLIERS
    UNIQUE_PROJECTS = fetch_unique_list("PROJECT_NAME")
    UNIQUE_SUPPLIERS = fetch_unique_list("VENDOR_NAME")

# Enhanced entity extraction and fuzzy matching
def extract_entity_from_question(question: str, entity_type: str, entity_list: list) -> Tuple[Optional[str], float]:
    """
    Extract entity from question and return both the entity and the match confidence score
    """
    system_message = f"""You are an assistant that helps extract the most likely {entity_type} name from a user's question.
    
Here is a list of all valid {entity_type} names:
{chr(10).join(entity_list[:100])}  # Limiting to first 100 to avoid context length issues

If the question refers to a {entity_type}, output the exact substring from the question that refers to the {entity_type}. 
If not, output NONE."""

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": question}
        ],
        "stream": False
    }
    
    try:
        resp = requests.post(f"{OLLAMA_HOST}/v1/chat/completions", json=payload)
        resp.raise_for_status()
        response_data = resp.json()
        extracted_text = response_data['choices'][0]['message']['content'].strip()
        
        if extracted_text.upper() == "NONE":
            return None, 0.0
        
        # Improved fuzzy matching with higher confidence
        matches = difflib.get_close_matches(extracted_text, entity_list, n=3, cutoff=0.4)
        
        if not matches:
            return None, 0.0
            
        best_match = matches[0]
        # Calculate match score (rough approximation)
        match_score = difflib.SequenceMatcher(None, extracted_text.lower(), best_match.lower()).ratio()
        
        return best_match, match_score
    except Exception as e:
        print(f"Error extracting {entity_type}: {e}")
        return None, 0.0

def process_question(question: str) -> Tuple[str, str, list, list, dict]:
    """
    Process the question and return answer, query, columns, results, and detected entities
    """
    # Extract detected entities
    detected_entities = {
        "project": None,
        "project_confidence": 0.0,
        "supplier": None,
        "supplier_confidence": 0.0
    }
    
    # Try to extract project from the question
    project_guess, project_confidence = extract_entity_from_question(question, "project", UNIQUE_PROJECTS)
    if project_guess:
        detected_entities["project"] = project_guess
        detected_entities["project_confidence"] = project_confidence
    
    # Try to extract supplier from the question
    supplier_guess, supplier_confidence = extract_entity_from_question(question, "supplier", UNIQUE_SUPPLIERS)
    if supplier_guess:
        detected_entities["supplier"] = supplier_guess
        detected_entities["supplier_confidence"] = supplier_confidence
    
    # If an entity was found, rewrite the question with the exact name
    rewritten_question = question
    
    # Prioritize the entity with higher confidence if both are found
    if project_guess and supplier_guess:
        if project_confidence > supplier_confidence:
            entity = project_guess
        else:
            entity = supplier_guess
    elif project_guess:
        entity = project_guess
    elif supplier_guess:
        entity = supplier_guess
    else:
        entity = None
        
    if entity:
        words = entity.split()
        # Try to replace partial match in the question
        found = False
        for w in words:
            if w.lower() in question.lower() and len(w) > 2:  # Only replace meaningful words
                rewritten_question = question.replace(w, entity)
                found = True
                break
                
        if not found:
            rewritten_question = f"{question} ({entity})"
    
    # Generate SQL query with the rewritten question
    query = generate_sql_query(rewritten_question)
    if query.startswith("Error"):
        return "", query, ["Error"], [["Failed to generate SQL query"]], detected_entities
        
    # Execute the query
    columns, results = execute_query(query)
    
    # Generate natural language answer
    answer = generate_natural_language_answer(rewritten_question, query, columns, results)
    
    return answer, query, columns, results, detected_entities

def generate_sql_query(question: str) -> str:
    try:
        # Explain all columns to the LLM
        system_message = "You are a SQL query generator. Generate MySQL queries based on natural language questions.\n\n"
        system_message += "The table name is 'po_followup_merged' and it has these columns:\n"
        system_message += "- id: auto-increment row id (INT)\n"
        system_message += "- PO_NUM: purchase order number (VARCHAR)\n"
        system_message += "- COMMENTS: comments about the PO (TEXT)\n"
        system_message += "- APPROVED_DATE: date the PO was approved (DATE)\n"
        system_message += "- UOM: unit of measure (VARCHAR)\n"
        system_message += "- ITEM_DESCRIPTION: description of the item (TEXT)\n"
        system_message += "- UNIT_PRICE: unit price for the item (DECIMAL)\n"
        system_message += "- QUANTITY_RECEIVED: quantity received (DECIMAL)\n"
        system_message += "- LINE_AMOUNT: total line amount (DECIMAL)\n"
        system_message += "- PROJECT_NAME: project name (VARCHAR)\n"
        system_message += "- VENDOR_NAME: supplier/vendor name (VARCHAR)\n"
        system_message += "- TERMS: merged PO terms (TEXT)\n\n"
        system_message += "You can answer questions about purchase orders, terms, suppliers, projects, items, etc.\n\n"
        system_message += "Only use these columns in your query. Keep the query simple and focused on answering the question. "
        system_message += "Return ONLY the SQL query, with no explanations or markdown."
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Generate a MySQL query to answer this question: {question}"}
        ]
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False
        }
        
        resp = requests.post(f"{OLLAMA_HOST}/v1/chat/completions", json=payload)
        resp.raise_for_status()
        response = resp.json()
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error generating SQL query: {str(e)}"

def generate_natural_language_answer(question: str, sql_query: str, columns: list, results: list) -> str:
    if not results or len(results) == 0:
        return f"There are no results for this query."
        
    # Format results as readable string
    if columns[0] == "Error":
        result_str = results[0][0] if results and len(results) > 0 else "Unknown error"
    else:
        header = " | ".join(columns)
        sep = " | ".join(["---"] * len(columns))
        rows = [" | ".join(str(cell) for cell in row) for row in results]
        result_str = f"{header}\n{sep}\n" + "\n".join(rows)
        
    # Build the prompt using standard string concatenation to avoid any f-string issues
    prompt = "Given the user's question and the SQL query result below, write a clear, concise answer in English. If the result is empty, say so.\n\n"
    prompt += f"User question: {question}\n\n"
    prompt += f"SQL query: {sql_query}\n\n"
    prompt += f"Query result:\n{result_str}\n\n"
    prompt += "Answer:\n"

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    
    try:
        resp = requests.post(f"{OLLAMA_HOST}/v1/chat/completions", json=payload)
        resp.raise_for_status()
        response = resp.json()
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error generating natural language answer: {str(e)}"

def connect_to_database():
    """Connect to MySQL database"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def execute_query(query: str) -> Tuple[List[str], List[List]]:
    """Execute query and return columns and results"""
    connection = connect_to_database()
    if not connection:
        return ["Error"], [["Database connection failed"]]
        
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append([str(cell) if cell is not None else "NULL" for cell in row])
        return columns, results
    except Exception as e:
        return ["Error"], [[str(e)]]
    finally:
        cursor.close()
        connection.close()

def create_interface():
    with gr.Blocks(title="RME PO Query Assistant rev.14 (Merged Table)") as interface:
        gr.Markdown(
            "# PO Follow-Up Query AI (rev.14, Merged Table)\n"
            "This AI assistant queries the merged PO table with all columns and terms.\n\n"
            "**Powered by Ollama Gemma3 running on your local GPU server.**"
        )
        
        with gr.Row():
            with gr.Column(scale=85):
                question_input = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask a question about purchase orders, terms, items, suppliers, projects, etc...",
                    lines=2
                )
            with gr.Column(scale=15):
                submit_btn = gr.Button("Send", variant="primary")
                
        # New component to display detected entities
        with gr.Row():
            detected_entities = gr.Markdown(label="Detected Entities")
            
        with gr.Row():
            llm_answer = gr.Markdown(label="LLM Answer")
            
        with gr.Row():
            query_output = gr.Code(label="Generated SQL Query", language="sql")
            
        with gr.Row():
            results = gr.Dataframe(label="Query Results")
            
        with gr.Row():
            supplier_btn = gr.Button("Show Unique Suppliers", elem_id="supplier-btn")
            project_btn = gr.Button("Show Unique Projects", elem_id="project-btn")

        def on_submit(question):
            if not question.strip():
                return "No entities detected", "Please enter a question", "", gr.Dataframe(value=[["Please enter a question"]], headers=["Error"])
                
            try:
                answer, query, columns, results_data, entities = process_question(question)
                
                # Format detected entities for display
                entities_markdown = "### Detected Entities\n"
                
                if entities["project"]:
                    entities_markdown += f"**Project:** {entities['project']} *(confidence: {entities['project_confidence']:.2f})*\n"
                else:
                    entities_markdown += "**Project:** None\n"
                    
                if entities["supplier"]:
                    entities_markdown += f"**Supplier:** {entities['supplier']} *(confidence: {entities['supplier_confidence']:.2f})*\n"
                else:
                    entities_markdown += "**Supplier:** None\n"
                
                if query.startswith("Error") or columns[0] == "Error":
                    error_message = results_data[0][0] if columns[0] == "Error" else query
                    return entities_markdown, answer, query, gr.Dataframe(value=[[error_message]], headers=["Error"])
                    
                return entities_markdown, answer, query, gr.Dataframe(value=results_data, headers=columns)
                
            except Exception as e:
                return "Error detecting entities", f"Unexpected error: {str(e)}", "", gr.Dataframe(value=[[str(e)]], headers=["Error"])

        submit_btn.click(
            fn=on_submit,
            inputs=[question_input],
            outputs=[detected_entities, llm_answer, query_output, results]
        )
        
        question_input.submit(
            fn=on_submit,
            inputs=[question_input],
            outputs=[detected_entities, llm_answer, query_output, results]
        )
        
        supplier_btn.click(None, None, None, js="window.open('/suppliers', '_blank')")
        project_btn.click(None, None, None, js="window.open('/projects', '_blank')")
        
        gr.Examples(
            examples=[
                ["Show me all items for project Rabigh 2 (Mourjan)"],
                ["What are the terms for supplier الشركة المصرية"],
                ["List all POs for project MOC HQ at Diriyah-K0005"],
                ["Show all purchase orders with their terms"],
                ["Which item has the highest unit price in Ring Road project?"],
            ],
            inputs=question_input,
            outputs=[detected_entities, llm_answer, query_output, results],
            fn=on_submit
        )
        
    return interface

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import webbrowser

app = FastAPI()

def get_unique_list(column: str):
    return fetch_unique_list(column)

@app.get("/suppliers", response_class=HTMLResponse)
def suppliers():
    names = get_unique_list("VENDOR_NAME")
    html = "<h2>Unique Supplier Names</h2><ul>" + "".join(f"<li>{n}</li>" for n in names) + "</ul>"
    return HTMLResponse(content=html)

@app.get("/projects", response_class=HTMLResponse)
def projects():
    names = get_unique_list("PROJECT_NAME")
    html = "<h2>Unique Project Names</h2><ul>" + "".join(f"<li>{n}</li>" for n in names) + "</ul>"
    return HTMLResponse(content=html)

if __name__ == "__main__":
    initialize_unique_lists()
    interface = create_interface()
    app = gr.mount_gradio_app(app, interface, path="/")
    webbrowser.open("http://localhost:7868")
    uvicorn.run(app, host="0.0.0.0", port=7868)
