#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import psycopg2
import pandas as pd


# In[ ]:


connection = psycopg2.connect(
    host="localhost",
    dbname="rme",
    user="postgres",
    password="omar_321"
)

cursor = connection.cursor()


# In[ ]:


cursor.execute("SELECT project_name, comment, supplier_name, amount FROM cost_dist ORDER BY amount DESC LIMIT 100;")
records = cursor.fetchall()

df = pd.DataFrame(records, columns=["project_name", "comment", "supplier_name", "amount"])
df.to_excel("top_100_cost_dist.xlsx", index=False)
print(df)

connection.close()


# In[ ]:




