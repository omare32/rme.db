import mysql.connector as mysql
from mysql.connector import Error
import pandas as pd

# MySQL connection details
db_host = "10.10.11.242"
db_user = "omar2"
db_password = "Omar_54321"
db_name = "RME_TEST"

def clean_columns(df):
    # Remove columns named nan (as string) or NaN (as float)
    return df.loc[:, [(col is not None) and (str(col).lower() != 'nan') for col in df.columns]]

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

        # Clean columns
        po_followup_df = clean_columns(po_followup_df)
        po_terms_df = clean_columns(po_terms_df)

        # Merge on po_number (left join to keep all po_followup rows)
        merged_df = pd.merge(po_followup_df, po_terms_df, how='left', left_on='po_number', right_on='PO_NUMBER')
        if 'PO_NUMBER' in merged_df.columns:
            merged_df.drop(columns=['PO_NUMBER'], inplace=True)
        merged_df = clean_columns(merged_df)

        # Create new table
        table_name = "po_followup_with_terms"
        print(f"🗑️ Dropping and recreating table {table_name}...")
        mysql_cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        # Build CREATE TABLE statement dynamically
        create_cols = []
        for col, dtype in zip(po_followup_df.columns, po_followup_df.dtypes):
            if (col is None) or (str(col).lower() == 'nan'):
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
        insert_cols = [col for col in list(po_followup_df.columns) + ['LONG_TEXT'] if (col is not None) and (str(col).lower() != 'nan')]
        print("Insert columns:", insert_cols)
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