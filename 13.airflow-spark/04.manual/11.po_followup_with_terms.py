import mysql.connector as mysql
from mysql.connector import Error
import pandas as pd

# MySQL connection details
db_host = "10.10.11.242"
db_user = "omar2"
db_password = "Omar_54321"
db_name = "RME_TEST"

def main():
    try:
        print("🔄 Connecting to MySQL database...")
        mysql_connection = mysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        mysql_cursor = mysql_connection.cursor()
        if mysql_connection.is_connected():
            print("✅ Successfully connected to MySQL!")

        # Read po_followup_for_chatbot and po_terms into DataFrames
        po_followup_df = pd.read_sql("SELECT * FROM po_followup_for_chatbot", mysql_connection)
        po_terms_df = pd.read_sql("SELECT PO_NUMBER, LONG_TEXT FROM po_terms", mysql_connection)

        # Remove columns with nan as name
        po_followup_df = po_followup_df.loc[:, ~po_followup_df.columns.isna()]
        po_terms_df = po_terms_df.loc[:, ~po_terms_df.columns.isna()]

        # Merge on po_number (left join to keep all po_followup rows)
        merged_df = pd.merge(po_followup_df, po_terms_df, how='left', left_on='po_number', right_on='PO_NUMBER')
        merged_df.drop(columns=['PO_NUMBER'], inplace=True)
        merged_df = merged_df.loc[:, ~merged_df.columns.isna()]

        # Create new table
        table_name = "po_followup_with_terms"
        print(f"🗑️ Dropping and recreating table {table_name}...")
        mysql_cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        # Build CREATE TABLE statement dynamically
        create_cols = []
        for col, dtype in zip(po_followup_df.columns, po_followup_df.dtypes):
            if pd.isna(col):
                continue
            if dtype == 'int64':
                coltype = 'INT'
            elif dtype == 'float64':
                coltype = 'DECIMAL(18,2)'
            elif dtype == 'datetime64[ns]':
                coltype = 'DATE'
            elif dtype == 'object':
                coltype = 'VARCHAR(255)'
            else:
                coltype = 'VARCHAR(255)'
            if col == 'id':
                create_cols.append(f"{col} INT PRIMARY KEY AUTO_INCREMENT")
            else:
                create_cols.append(f"{col} {coltype}")
        create_cols.append("LONG_TEXT TEXT")
        create_stmt = f"CREATE TABLE {table_name} ({', '.join(create_cols)})"
        mysql_cursor.execute(create_stmt)
        mysql_connection.commit()

        # Insert data in batches
        insert_cols = [col for col in list(po_followup_df.columns) + ['LONG_TEXT'] if pd.notna(col)]
        placeholders = ', '.join(['%s'] * len(insert_cols))
        insert_query = f"INSERT INTO {table_name} ({', '.join(insert_cols)}) VALUES ({placeholders})"
        data_tuples = [tuple(row[col] for col in insert_cols) for _, row in merged_df.iterrows()]
        batch_size = 1000
        for start in range(0, len(data_tuples), batch_size):
            end = start + batch_size
            mysql_cursor.executemany(insert_query, data_tuples[start:end])
            mysql_connection.commit()

        # Print stats
        with_terms = merged_df['LONG_TEXT'].notnull().sum()
        without_terms = merged_df['LONG_TEXT'].isnull().sum()
        print(f"POs with terms: {with_terms}")
        print(f"POs without terms: {without_terms}")

        mysql_cursor.close()
        mysql_connection.close()
    except Error as e:
        print(f"❌ MySQL Error: {e}")

if __name__ == "__main__":
    main() 