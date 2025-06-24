import gradio as gr
import psycopg2
from psycopg2 import Error
import os
import json
import re
import sys
import time
from typing import Dict, List, Tuple, Optional, Any
from dotenv import load_dotenv
import requests
import difflib
from datetime import datetime
import ollama
import webbrowser
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

# Load environment variables
load_dotenv()

# PostgreSQL database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'postgres',
    'password': 'PMO@1234',
    'database': 'postgres',
    'schema': 'public'
}

OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "gemma3:latest"

# Function to check if Ollama is running and the model is available
def check_ollama_and_model():
    print("Checking Ollama server and model availability...")
    try:
        # Check if Ollama server is running
        response = requests.get(f"{OLLAMA_HOST}/api/version", timeout=5)
        if response.status_code != 200:
            print(f"Error: Ollama server is not responding properly. Status code: {response.status_code}")
            print("Please make sure Ollama is installed and running.")
            print("You can download Ollama from: https://ollama.com/download")
            return False
            
        # Check if the model is available
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code != 200:
            print("Error: Could not fetch model list from Ollama.")
            return False
            
        models = response.json().get('models', [])
        model_names = [model.get('name') for model in models]
        
        if OLLAMA_MODEL not in model_names:
            print(f"Error: Model '{OLLAMA_MODEL}' is not available in Ollama.")
            print(f"Available models: {', '.join(model_names)}")
            print(f"\nTo pull the required model, run: ollama pull {OLLAMA_MODEL}")
            return False
            
        print(f"[OK] Ollama server is running and model '{OLLAMA_MODEL}' is available.")
        return True
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Ollama server.")
        print("Please make sure Ollama is installed and running.")
        print("You can download Ollama from: https://ollama.com/download")
        return False
    except Exception as e:
        print(f"Error checking Ollama: {str(e)}")
        return False

# PostgreSQL uses lowercase column names by default
NEW_TABLE = "po_followup_rev19"

# Column name mapping to handle case sensitivity in PostgreSQL
# In PostgreSQL, we need to use quotes for case-sensitive column names
COLUMN_MAP = {
    "project_name": "\"PROJECT_NAME\"",
    "vendor_name": "\"VENDOR_NAME\"",
    "po_num": "\"PO_NUM\"",
    "comments": "\"COMMENTS\"",
    "approved_date": "\"APPROVED_DATE\"",
    "uom": "\"UOM\"",
    "item_description": "\"ITEM_DESCRIPTION\"",
    "unit_price": "\"UNIT_PRICE\"",
    "quantity_received": "\"QUANTITY_RECEIVED\"",
    "line_amount": "\"LINE_AMOUNT\"",
    "terms": "\"TERMS\""
}

# Hardcoded list of unique projects
UNIQUE_PROJECTS = [
    "Rabigh 2 (Mourjan)",
    "MOC HQ at Diriyah-K0005",
    "Ring Road",
    "NEOM Smart City Phase 1",
    "Al-ASEMA Bridge",
    "Riyadh Metro Line 3",
    "King Abdullah Financial District",
    "Jeddah Tower",
    "Qiddiya Entertainment City",
    "Red Sea Project"
]

# Hardcoded list of unique suppliers
UNIQUE_SUPPLIERS = [
    "الشركة المصرية",
    "Saudi Binladin Group",
    "Al Rashid Trading & Contracting",
    "Saudi Aramco",
    "SABIC",
    "Al-Ayuni Investment and Contracting",
    "Abdullah A. M. Al-Khodari Sons",
    "El Seif Engineering Contracting",
    "Saudi Oger",
    "Nesma & Partners Contracting"
]

# Conversation history management
class ConversationManager:
    def __init__(self, max_history=5):
        self.conversation_history = []
        self.detected_entities = {}
        self.last_query_result = None
        self.last_sql_query = None
        self.max_history = max_history
        self.memory_was_cleared = False  # Flag to track if memory was explicitly cleared
    
    def add_interaction(self, question: str, answer: str, entities: Dict, sql_query: str = None, query_result: Dict = None):
        """Add a new interaction to the conversation history"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # When adding a new interaction, we're no longer in a cleared state
        self.memory_was_cleared = False
        
        # Save important entities for context
        if entities.get("project"):
            self.detected_entities["project"] = entities["project"]
        if entities.get("supplier"):
            self.detected_entities["supplier"] = entities["supplier"]
            
        # Save query results for reference
        if query_result:
            self.last_query_result = query_result
        if sql_query:
            self.last_sql_query = sql_query
            
        # Add to history
        self.conversation_history.append({
            "timestamp": timestamp,
            "question": question,
            "answer": answer,
            "entities": {k: v for k, v in entities.items() if k in ["project", "supplier"] and v is not None}
        })
        
        # Maintain max history size
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def get_context_for_llm(self) -> str:
        """Format conversation history for the LLM"""
        if not self.conversation_history:
            return ""
            
        context = "Previous conversation:\n"
        for i, interaction in enumerate(self.conversation_history):
            context += f"User: {interaction['question']}\n"
            context += f"Assistant: {interaction['answer']}\n"
        return context
    
    def get_active_entities(self) -> Dict:
        """Get detected entities from the conversation"""
        return self.detected_entities
    
    def reset(self):
        """Reset the conversation history"""
        self.conversation_history = []
        self.detected_entities = {}
        self.last_query_result = None
        self.last_sql_query = None
        self.memory_was_cleared = True  # Set flag to indicate memory was explicitly cleared

# Initialize conversation manager
CONVERSATION = ConversationManager()

# Since we're using hardcoded lists, we don't need these functions anymore
# but we'll keep them as stubs for compatibility
def fetch_unique_list(column: str) -> list:
    """Return the hardcoded list based on the column name."""
    if column.upper() == "PROJECT_NAME":
        return UNIQUE_PROJECTS
    elif column.upper() == "VENDOR_NAME":
        return UNIQUE_SUPPLIERS
    return []

def initialize_unique_lists():
    """No need to initialize since we're using hardcoded lists."""
    pass

# Enhanced entity extraction and matching

def format_detected_entities(entities: dict) -> str:
    """Format detected entities for display in the UI."""
    entities_markdown = "### Detected Entities\n"
    
    # Display project if available
    if entities.get("project"):
        entities_markdown += f"**Project:** {entities['project']}\n"
    else:
        entities_markdown += "**Project:** None\n"
        
    # Display supplier if available
    if entities.get("supplier"):
        entities_markdown += f"**Supplier:** {entities['supplier']}\n"
    else:
        entities_markdown += "**Supplier:** None\n"
    
    return entities_markdown

def detect_entity_from_list_with_llm(question: str, entity_type: str, entity_list: list) -> str | None:
    """Asks the LLM to find the best entity from a list based on the user's question."""
    # Prepare the list for the prompt, ensuring it's not too long
    if len(entity_list) > 200:
        # If the list is too long, we might need a smarter way to narrow it down first
        # For now, we'll truncate it for the prompt to avoid exceeding context limits
        display_list = entity_list[:200]
    else:
        display_list = entity_list
        
    system_message = (
        f"You are an expert entity detection model. Your task is to identify one '{entity_type}' from the user's question. "
        f"The available {entity_type}s are: {', '.join(display_list)}. "
        f"Respond with only the name of the detected {entity_type} from the list. "
        f"If no {entity_type} from the list is mentioned or relevant, respond with 'None'."
    )
    user_prompt = f"Question: {question}"

    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            # First check if Ollama is available
            try:
                # Simple health check
                requests.get(f"{OLLAMA_HOST}/api/version", timeout=2)
            except requests.exceptions.RequestException:
                print(f"Ollama server not responding at {OLLAMA_HOST}. Attempt {attempt+1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
                
            # Now try to use the model
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {'role': 'system', 'content': system_message},
                    {'role': 'user', 'content': user_prompt},
                ],
                options={'temperature': 0.0}
            )
            
            if not isinstance(response, dict):
                print(f"Unexpected response type from Ollama: {type(response)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
                
            if 'message' not in response:
                print(f"'message' not found in Ollama response: {response}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
                
            if 'content' not in response['message']:
                print(f"'content' not found in Ollama message: {response['message']}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
            
            llm_response = response['message']['content'].strip()
            if llm_response.lower() == 'none' or not llm_response:
                return None
                
            return llm_response
            
        except ollama.RequestError as e:
            print(f"Ollama connection error during entity detection for {entity_type}: {e.args}")
            if attempt < max_retries - 1:
                print(f"Retrying... Attempt {attempt+1}/{max_retries}")
                time.sleep(retry_delay)
            else:
                return None
        except Exception as e:
            print(f"An unexpected error occurred during entity detection for {entity_type}: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying... Attempt {attempt+1}/{max_retries}")
                time.sleep(retry_delay)
            else:
                return None
    
    return None

def format_detected_entities(entities: dict) -> str:
    """Formats the detected entities dictionary into a readable string."""
    if not entities or (not entities.get("project") and not entities.get("supplier")):
        return "No entities detected."
    
    lines = []
    if entities.get("project"):
        lines.append(f"Project: {entities['project']}")
    if entities.get("supplier"):
        lines.append(f"Supplier: {entities['supplier']}")
        
    return "\n".join(lines)

def create_sql_query_with_llm(question: str, detected_entities: Dict[str, Any], table_name: str, columns: List[str], conn=None) -> Tuple[str, str]:
    """Generate a SQL query using the LLM based on the user's question and detected entities."""
    # Format the detected entities for the prompt
    entity_info = ""
    if detected_entities.get("project"):
        entity_info += f"Project: {detected_entities['project']}\n"
    if detected_entities.get("supplier"):
        entity_info += f"Supplier: {detected_entities['supplier']}\n"
    
    # Create a system message with detailed instructions for SQL generation
    system_message = (
        "You are an expert SQL query generator for a purchase order database. "
        "Generate a PostgreSQL query based on the user's question and detected entities. "
        "Follow these rules strictly:\n"
        "1. Use exact column names as provided\n"
        "2. Always use double quotes for case-sensitive column names\n"
        "3. Use ILIKE for case-insensitive string matching\n"
        "4. Include appropriate aggregations (SUM, COUNT, AVG) when needed\n"
        "5. Use proper GROUP BY clauses when using aggregations\n"
        "6. Return only the SQL query without any explanations\n"
        "7. If you cannot generate a valid query, return 'ERROR: ' followed by the reason\n\n"
        f"Table: {table_name}\n"
        f"Columns: {', '.join(columns)}\n\n"
        f"Detected Entities:\n{entity_info}"
    )
    
    user_prompt = f"Question: {question}"
    
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            # First check if Ollama is available
            try:
                # Simple health check
                requests.get(f"{OLLAMA_HOST}/api/version", timeout=2)
            except requests.exceptions.RequestException:
                print(f"Ollama server not responding at {OLLAMA_HOST}. Attempt {attempt+1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return "", "Error: Ollama server is not responding. Please ensure Ollama is running."
            
            # Now try to use the model
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {'role': 'system', 'content': system_message},
                    {'role': 'user', 'content': user_prompt},
                ],
                options={'temperature': 0.0}
            )
            
            if not isinstance(response, dict):
                print(f"Unexpected response type from Ollama: {type(response)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return "", "Error: Received invalid response from LLM"
                
            if 'message' not in response:
                print(f"'message' not found in Ollama response: {response}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return "", "Error: Incomplete response from LLM (no message field)"
                
            if 'content' not in response['message']:
                print(f"'content' not found in Ollama message: {response['message']}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return "", "Error: Incomplete response from LLM (no content field)"
            
            sql_query = response['message']['content'].strip()
            
            # Check if the response indicates an error
            if sql_query.upper().startswith("ERROR:"):
                return "", sql_query
            
            # Basic validation of the SQL query
            if not sql_query.lower().startswith("select"):
                error_msg = f"Error: Generated query does not appear to be a valid SELECT statement: {sql_query}"
                if attempt < max_retries - 1:
                    print(f"{error_msg}. Retrying...")
                    time.sleep(retry_delay)
                    continue
                return "", error_msg
            
            return sql_query, ""
            
        except ollama.RequestError as e:
            error_message = f"Ollama connection error during SQL generation: {e.args}"
            print(error_message)
            if attempt < max_retries - 1:
                print(f"Retrying... Attempt {attempt+1}/{max_retries}")
                time.sleep(retry_delay)
            else:
                return "", error_message
        except Exception as e:
            error_message = f"An unexpected error occurred during SQL generation: {str(e)}"
            print(error_message)
            if attempt < max_retries - 1:
                print(f"Retrying... Attempt {attempt+1}/{max_retries}")
                time.sleep(retry_delay)
            else:
                return "", error_message
    
    return "", "Failed to generate SQL query after multiple attempts"

def generate_natural_language_answer(question: str, sql_query: str, columns: list, results: list, use_history: bool) -> str:
    """Generates a natural language answer from an SQL query and its results, with robust error handling."""
    if not columns or not results:
        return "No data found that matches your query."

    # Check if there was an error in the query execution
    if columns[0] == "Error":
        return results[0][0]

    # Format the results for the prompt
    formatted_results = "Results:\n"
    
    # Add column headers
    formatted_results += ", ".join(columns) + "\n"
    
    # Add result rows (limit to 10 rows to avoid overwhelming the LLM)
    max_rows = min(10, len(results))
    for i in range(max_rows):
        formatted_results += ", ".join(str(cell) for cell in results[i]) + "\n"
    
    if len(results) > max_rows:
        formatted_results += f"... and {len(results) - max_rows} more rows\n"

    system_message = (
        "You are an expert data analyst for purchase orders. "
        "Generate a clear, concise answer to the user's question based on the SQL query and its results. "
        "Focus on directly answering the question with the key insights from the data. "
        "Keep your answer brief and to the point. "
        "If the results are empty, explain that no matching data was found. "
        "If there was an error, explain it in user-friendly terms."
    )

    user_prompt = (
        f"Question: {question}\n\n"
        f"SQL Query: {sql_query}\n\n"
        f"{formatted_results}"
    )

    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            # First check if Ollama is available
            try:
                # Simple health check
                requests.get(f"{OLLAMA_HOST}/api/version", timeout=2)
            except requests.exceptions.RequestException:
                print(f"Ollama server not responding at {OLLAMA_HOST}. Attempt {attempt+1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return "Error: Ollama server is not responding. Please ensure Ollama is running."
            
            # Now try to use the model
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {'role': 'system', 'content': system_message},
                    {'role': 'user', 'content': user_prompt},
                ],
                options={'temperature': 0.0}
            )
            
            if not isinstance(response, dict):
                print(f"Unexpected response type from Ollama: {type(response)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return "Error: Received invalid response from LLM"
                
            if 'message' not in response:
                print(f"'message' not found in Ollama response: {response}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return "Error: Incomplete response from LLM (no message field)"
                
            if 'content' not in response['message']:
                print(f"'content' not found in Ollama message: {response['message']}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return "Error: Incomplete response from LLM (no content field)"
            
            answer = response['message']['content'].strip()
            return answer
            
        except ollama.RequestError as e:
            error_message = f"Ollama connection error during answer generation: {e.args}"
            print(error_message)
            if attempt < max_retries - 1:
                print(f"Retrying... Attempt {attempt+1}/{max_retries}")
                time.sleep(retry_delay)
            else:
                return "Error: Failed to connect to Ollama. Please ensure it is running."
        except Exception as e:
            error_message = f"An unexpected error occurred during answer generation: {str(e)}"
            print(error_message)
            if attempt < max_retries - 1:
                print(f"Retrying... Attempt {attempt+1}/{max_retries}")
                time.sleep(retry_delay)
            else:
                return f"Error: {str(e)}"
    
    return "Failed to generate an answer after multiple attempts. Please try again."

def process_question(question: str, use_history: bool = True) -> Tuple[str, str, List[str], List[List], str]:
    """Process the question, generate and execute SQL, and return a natural language answer."""
    # Detect entities using the LLM
    detected_project = detect_entity_from_list_with_llm(question, "project", UNIQUE_PROJECTS)
    detected_supplier = detect_entity_from_list_with_llm(question, "supplier", UNIQUE_SUPPLIERS)

    detected_entities = {"project": detected_project, "supplier": detected_supplier}

    if use_history:
        active_entities = CONVERSATION.get_active_entities()
        if not detected_entities["project"] and active_entities.get('project'):
            detected_entities['project'] = active_entities['project']
        if not detected_entities["supplier"] and active_entities.get('supplier'):
            detected_entities['supplier'] = active_entities['supplier']
    
    formatted_entities = format_detected_entities(detected_entities)

    sql_query, error_message = create_sql_query_with_llm(
        question=question,
        detected_entities=detected_entities,
        table_name=f'{DB_CONFIG["schema"]}.{NEW_TABLE}',
        columns=list(COLUMN_MAP.keys()),
        conn=None
    )

    if error_message:
        answer = error_message
        CONVERSATION.add_interaction(question, answer, detected_entities, sql_query)
        return answer, sql_query or "Failed to generate query", [], [], formatted_entities

    columns, results = execute_query(sql_query)
    
    if columns and columns[0] == "Error":
        answer = results[0][0]
        CONVERSATION.add_interaction(question, answer, detected_entities, sql_query)
        return answer, sql_query, columns, results, formatted_entities

    answer = generate_natural_language_answer(question, sql_query, columns, results, use_history)

    CONVERSATION.add_interaction(
        question=question,
        answer=answer,
        entities=detected_entities,
        sql_query=sql_query,
        query_result={"columns": columns, "results": results}
    )

    return answer, sql_query, columns, results, formatted_entities

def connect_to_database() -> psycopg2.extensions.connection | None:
    """Connects to the PostgreSQL database."""
    try:
        connection = psycopg2.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        # Set search_path to our schema
        cursor = connection.cursor()
        cursor.execute(f"SET search_path TO {DB_CONFIG['schema']}")
        connection.commit()
        cursor.close()
        
        return connection
    except Error as e:
        print(f"Error connecting to PostgreSQL database: {e}")
        return None

def execute_query(query: str) -> Tuple[List[str], List[List]]:
    """Execute query and return columns and results"""
    connection = None
    try:
        connection = connect_to_database()
        if connection is None:
            return ["Error"], [["Could not connect to database"]]
            
        cursor = connection.cursor()
        cursor.execute(query)
        
        # For SELECT queries, fetch results and column names
        if query.strip().upper().startswith("SELECT"):
            columns = [desc[0] for desc in cursor.description]
            results = [list(row) for row in cursor.fetchall()]
        else:
            # For non-SELECT queries, just show status
            connection.commit()
            columns = ["Status"]
            results = [[f"Query executed successfully. Affected rows: {cursor.rowcount}"]] 
        
        # Close cursor and connection
        cursor.close()
        connection.close()
        
        return columns, results
    except Exception as e:
        if connection:
            connection.close()
        return ["Error"], [[str(e)]]
    finally:
        if connection:
            connection.close()

def create_interface():
    with gr.Blocks(title="RME PO Query Assistant rev.21 (PostgreSQL with Memory)") as interface:
        # Title only at the top - moved descriptive text to bottom
        gr.Markdown("# PO Follow-Up Query AI (rev.21, PostgreSQL with Memory)")
        
        # Two column layout - Chat on left, Entities on right
        with gr.Row():
            # Left column for chat interface
            with gr.Column(scale=7):
                chatbot = gr.Chatbot(label="Conversation", height=400)
                
                with gr.Row():
                    with gr.Column(scale=8):
                        # Standard textbox for question input
                        question_input = gr.Textbox(
                            label="Your Question",
                            placeholder="Ask a question about purchase orders, terms, items, suppliers, projects, etc...",
                            lines=2
                        )
                    with gr.Column(scale=2):
                        submit_btn = gr.Button("Send", variant="primary")
                        clear_history_btn = gr.Button("Clear Memory", variant="secondary")
            
            # Right column for entity detection
            with gr.Column(scale=3):
                detected_entities_display = gr.Markdown(label="Detected Entities", value="No entities detected yet.")
                
                with gr.Row():
                    supplier_btn = gr.Button("Show Suppliers", elem_id="supplier-btn")
                    project_btn = gr.Button("Show Projects", elem_id="project-btn")
        
        # SQL and results section (below the conversation)
        with gr.Accordion("SQL Query and Results", open=False):
            query_output = gr.Code(label="Current SQL Query", language="sql")
            results = gr.Dataframe(label="Query Results")
            
        # Informational text moved to bottom of the interface
        gr.Markdown(
            "### System Information\n"
            "This AI assistant queries the merged PO table with all columns and terms.\n\n"
            "- Using local PostgreSQL database with **861,403 PO records**\n"
            "- Ask questions about suppliers, terms, projects, etc.\n"
            "- Ask follow-up questions without repeating entities mentioned before\n"
            "- Navigation entity memory is applied to all follow-up questions\n"
            "- Using hardcoded lists of projects and suppliers for entity detection\n"
        )
            
        def clear_history():
            # Completely reset the conversation memory
            global CONVERSATION
            # Create a new instance to ensure complete reset
            CONVERSATION = ConversationManager()
            print("Conversation memory has been completely cleared")
            print(f"Conversation state after reset: {CONVERSATION.conversation_history}")
            print(f"Entities after reset: {CONVERSATION.detected_entities}")
            
            # Return empty/reset values for all UI components
            return [], "### No entities detected yet.", "", None
            
        def on_submit(question, chat_history):
            if not question.strip():
                return chat_history, question, "### No entities detected yet.", "", None
                
            try:
                # Process the question with conversation history enabled
                answer, query, columns, results_data, entities_text = process_question(question, use_history=True)
                
                # Update the chat history with the new question and answer
                chat_history = chat_history + [(question, answer)]
                
                # Get the detected entities from the conversation manager
                entities = CONVERSATION.get_active_entities()
                
                # Format detected entities for display in the right panel
                entities_markdown = "### Detected Entities\n"
                
                # Display project if available
                if entities.get("project"):
                    entities_markdown += f"**Project:** {entities['project']}\n"
                else:
                    entities_markdown += "**Project:** None\n"
                    
                # Display supplier if available
                if entities.get("supplier"):
                    entities_markdown += f"**Supplier:** {entities['supplier']}\n"
                else:
                    entities_markdown += "**Supplier:** None\n"
                
                if query.startswith("Error") or (columns and columns[0] == "Error"):
                    error_message = results_data[0][0] if columns and columns[0] == "Error" else query
                    return chat_history, "", entities_markdown, query, gr.Dataframe(value=[[error_message]], headers=["Error"])
                    
                # Create dataframe for results
                df = gr.Dataframe(value=results_data, headers=columns)
                return chat_history, "", entities_markdown, query, df
                
            except Exception as e:
                error_message = f"Unexpected error: {str(e)}"
                chat_history = chat_history + [(question, error_message)]
                return chat_history, "", "### Error in entity detection", "", None

        # Set up event listeners
        submit_btn.click(
            fn=on_submit,
            inputs=[question_input, chatbot],
            outputs=[chatbot, question_input, detected_entities_display, query_output, results]
        )
        
        # Add Enter key submission functionality
        question_input.submit(
            fn=on_submit,
            inputs=[question_input, chatbot],
            outputs=[chatbot, question_input, detected_entities_display, query_output, results]
        )
        
        # Connect the clear history button
        clear_history_btn.click(
            fn=clear_history,
            inputs=[],
            outputs=[chatbot, detected_entities_display, query_output, results]
        )
        
        supplier_btn.click(None, None, None, js="window.open('/suppliers', '_blank')")
        project_btn.click(None, None, None, js="window.open('/projects', '_blank')")
        
        gr.Examples(
            examples=[
                "Show me all items for project Rabigh 2 (Mourjan)",
                "What are the terms for supplier الشركة المصرية",
                "List all POs for project MOC HQ at Diriyah-K0005",
                "Show all purchase orders with their terms",
                "Which item has the highest unit price in Ring Road project?",
                "How many items were received for that project?",  # Example follow-up question
                "What were the terms for the last PO you showed me?",  # Another follow-up example
            ],
            inputs=question_input
        )
        
    return interface

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import webbrowser

app = FastAPI()

def get_unique_list(column: str):
    return fetch_unique_list(column)

# Create the FastAPI app
app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return "<html><body><h1>Purchase Order Chatbot API</h1><p>API is running. Access the UI at <a href='/gradio'>/gradio</a></p></body></html>"

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

def is_port_in_use(port):
    """Check if a port is in use"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port, max_attempts=10):
    """Find an available port starting from start_port"""
    port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(port):
            return port
        port += 1
    return start_port + max_attempts  # Return a port even if we couldn't verify it's free

def main():
    # Check if Ollama is running and the model is available
    if not check_ollama_and_model():
        print("\nExiting due to Ollama or model availability issues.")
        print("Please ensure Ollama is running and the model is available before starting the application.")
        sys.exit(1)
    
    # Find an available port
    port = find_available_port(7873)
    
    print(f"\n[OK] Starting Purchase Order Chatbot with model: {OLLAMA_MODEL}")
    print(f"[OK] Server will be available at http://localhost:{port}")
    
    # Create the Gradio interface
    interface = create_interface()
    
    # Mount Gradio app to FastAPI
    app_with_gradio = gr.mount_gradio_app(app, interface, path="/gradio")
    
    # Open browser automatically
    webbrowser.open(f"http://localhost:{port}/gradio", new=2, autoraise=True)
    
    # Run the FastAPI app
    uvicorn.run(app_with_gradio, host="0.0.0.0", port=port)

# Run the app
if __name__ == "__main__":
    initialize_unique_lists()
    main()
