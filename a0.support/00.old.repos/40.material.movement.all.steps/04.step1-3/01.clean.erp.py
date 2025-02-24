import os
import pandas as pd
from bs4 import BeautifulSoup
import xlsxwriter

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
        soup = BeautifulSoup(f, "html.parser")

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
    df.to_excel(html_file[:-5] + ".xlsx", engine="xlsxwriter")

# Delete all HTML files in the current directory
for file in os.listdir():
    if file.endswith(".html"):
        os.remove(file)

def remove_first_one_column_and_four_rows(file_path):
    """
    Remove the first 1 column and first 4 rows from an Excel file without saving the index row and number index.

    Args:
        file_path (str): The path to the Excel file.
    """

    df = pd.read_excel(file_path)
    df = df.iloc[5:, 1:]
    df = df.reset_index(drop=True)
    df.to_excel(file_path, index=False, header=None)

for file in os.listdir():
    if file.endswith(".xlsx"):
        file_path = os.path.join(os.getcwd(), file)
        remove_first_one_column_and_four_rows(file_path)