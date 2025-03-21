#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import psycopg2
import pandas as pd
import tkinter as tk
from tkinter import simpledialog
from tkinter import PhotoImage


# In[ ]:


# Database connection parameters
db_params = {
    "host": "localhost",
    "dbname": "rme",
    "user": "postgres",
    "password": "omar_321"
}

# Connect to the PostgreSQL server
connection = psycopg2.connect(**db_params)
cursor = connection.cursor()


# In[ ]:


# Create a Tkinter root window
root = tk.Tk()
root.title("RME : Export Cost Distribution Line")

# Load and display your company logo (assuming your logo file is named "logo.gif")
logo_image = PhotoImage(file="logo.gif")
logo_label = tk.Label(root, image=logo_image)
logo_label.grid(row=0, column=0, columnspan=2)  # Place logo at row 0, column 0


# In[ ]:


# Prompt the user to enter the project number using a dialog box
project_no_value = simpledialog.askstring("Project Number", "Please enter the project number:")


# In[ ]:


# SQL query to select data from the table where project_no matches user input
query = "SELECT * FROM cost_dist WHERE project_no = %s"
cursor.execute(query, (project_no_value,))

# Fetch all rows
rows = cursor.fetchall()

# Create a pandas DataFrame from the fetched data
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])


# In[ ]:


# Export the data to an Excel file
excel_filename = f"cost_dist_{project_no_value}.xlsx"
df.to_excel(excel_filename, index=False)

result_text = f"Data exported to '{excel_filename}' successfully!"
tk.Label(root, text=result_text).grid(row=2, column=0, columnspan=2)  # Display result message


# In[ ]:


# Close the database connection
cursor.close()
connection.close()

# Start the Tkinter event loop
root.mainloop()

