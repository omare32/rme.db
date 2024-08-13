import os
import pandas as pd
from bs4 import BeautifulSoup

# Get all .xls files in the current directory
xls_files = [file for file in os.listdir() if file.endswith(".xls")]

# Loop over the .xls files and rename them to .html files
for xls_file in xls_files:
    # Get the new file name
    new_file_name = xls_file[:-4] + ".html"

    # Rename the file
    os.rename(xls_file, new_file_name)
	
# Get all HTML files in the current directory
html_files = [file for file in os.listdir() if file.endswith(".html")]

# Loop over the HTML files
for html_file in html_files:
    # Read the HTML file
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f)

    # Get the data in the HTML file
    data = soup.find_all("table")

    # Create a list of lists to store the data
    data_list = []
    for table in data:
        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            data_list.append([col.text for col in cols])

    # Create a Pandas DataFrame from the data
    df = pd.DataFrame(data_list)

    # Save the DataFrame to an Excel file
    df.to_excel(html_file[:-5] + ".xlsx")
	
# Delete all HTML files in the current directory
for file in os.listdir():
    if file.endswith(".html"):
        os.remove(file)