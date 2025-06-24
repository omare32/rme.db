"""
Database configuration settings.

This module contains the configuration settings for connecting to various databases.
It's recommended to use environment variables for sensitive information in production.
"""

# MySQL Configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'your_mysql_username',
    'password': 'your_mysql_password',
    'database': 'your_database_name',
    'raise_on_warnings': True
}

# Neo4j Configuration (should match your docker-compose.yml)
NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',
    'user': 'neo4j',
    'password': 'password',  # Default password from docker-compose.yml
    'database': 'neo4j'
}

# Qdrant Configuration (should match your docker-compose.yml)
QDRANT_CONFIG = {
    'url': 'http://localhost:6333',
    'collection_name': 'purchase_orders',
    'vector_size': 384  # Should match your embedding model's vector size
}

# Embedding Model Configuration
EMBEDDING_CONFIG = {
    'model_name': 'all-MiniLM-L6-v2',  # Default model used in the application
    'device': 'cpu'  # 'cuda' if GPU is available
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'format': '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    'file': 'data_migration.log'  # Log file name
}
