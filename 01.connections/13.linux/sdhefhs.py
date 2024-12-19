import mysql.connector

mydb = mysql.connector.connect(
  host="10.10.11.242",
  user="omaressam",
  password="Omar@1234$"
)

print(mydb)