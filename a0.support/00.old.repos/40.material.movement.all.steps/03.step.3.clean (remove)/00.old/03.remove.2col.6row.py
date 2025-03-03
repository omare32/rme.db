import os
import pandas as pd

def remove_first_two_columns_and_five_rows(file_path):
    """
    Remove the first 2 columns and first 5 rows from an Excel file without saving the index row and number index.

    Args:
        file_path (str): The path to the Excel file.
    """

    df = pd.read_excel(file_path)
    df = df.iloc[5:, 2:]
    df = df.reset_index(drop=True)
    df = df.drop([1], axis=0)
    df.to_excel(file_path, index=False, header=None)


for file in os.listdir():
    if file.endswith(".xlsx"):
        file_path = os.path.join(os.getcwd(), file)
        remove_first_two_columns_and_five_rows(file_path)