import mysql.connector as mysql
import pandas as pd

# Connection details
host = "10.10.11.242"
user = "omar2"
password = "Omar_54321"
database = "RME_TEST"

# Connect to the database
connection = mysql.connect(
    host=host,
    user=user,
    password=password,
    database=database
)

# Create a cursor object
cursor = connection.cursor()

# Query to fetch data
query = "SELECT * FROM RME_Projects_Cost_Dist_Line_Report LIMIT 100"
cursor.execute(query)

# Fetch the data
data = cursor.fetchall()

# Get column names
column_names = [i[0] for i in cursor.description]

# Create a DataFrame
df = pd.DataFrame(data, columns=column_names)

# Close the connection
cursor.close()
connection.close()

# Display the DataFrame
print(df.head()) 