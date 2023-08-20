#!/usr/bin/env python
# coding: utf-8

# In[19]:


import psycopg2
import pandas as pd


# In[20]:


connection = psycopg2.connect(
    host="localhost",
    dbname="rme",
    user="postgres",
    password="omar_321"
)
cursor = connection.cursor()


# In[21]:


cursor.execute("""
    SELECT *
    FROM cost_dist
    WHERE project_no = '152';
""")
records = cursor.fetchall()
column_names = [desc[0] for desc in cursor.description]

df = pd.DataFrame(records, columns=column_names)
df.to_excel("cost_dist_152_all.xlsx", index=False)

connection.close()

