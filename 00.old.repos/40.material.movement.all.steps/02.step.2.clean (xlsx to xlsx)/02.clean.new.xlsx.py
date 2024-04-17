import os
import pandas as pd

def read_and_save_excel_files(directory):
    """
    Read all Excel files in a directory and save them as DataFrames.

    Args:
        directory (str): The path to the directory containing the Excel files.
    """

    for file in os.listdir(directory):
        if file.endswith(".xlsx"):
            file_path = os.path.join(directory, file)
            df = pd.read_excel(file_path)
            df.to_excel(file_path.split(".")[0] + "_df.xlsx")

    # Create a new Excel file and save the DataFrame.
    new_file_path = os.path.join(directory, file.split(".")[0] + "_new.xlsx")
    df.to_excel(new_file_path)


if __name__ == "__main__":
    directory = os.getcwd()
    read_and_save_excel_files(directory)