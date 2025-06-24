import psycopg2

# Connect to the database
try:
    conn = psycopg2.connect(
        host='localhost',
        user='postgres',
        password='PMO@1234',
        database='postgres'
    )
    
    cursor = conn.cursor()
    
    # Execute query to get unique supplier names
    cursor.execute('SELECT DISTINCT "VENDOR_NAME" FROM public.po_followup_rev19 WHERE "VENDOR_NAME" IS NOT NULL ORDER BY "VENDOR_NAME"')
    
    # Fetch all results
    results = cursor.fetchall()
    
    # Print the results in a format that can be copied into the code
    print('UNIQUE_SUPPLIERS = [')
    for row in results:
        print(f'    "{row[0]}",')
    print(']')
    
    # Close the connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {str(e)}")
