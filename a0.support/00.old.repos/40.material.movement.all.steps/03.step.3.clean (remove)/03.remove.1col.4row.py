import os
import pandas as pd

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