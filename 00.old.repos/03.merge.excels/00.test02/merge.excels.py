import os
import pandas as pd

# Get the path to the folder containing the Excel files
folder_path = "D:/OneDrive/OneDrive - Rowad Modern Engineering/x004 Data Science/00.tests/01.merge.excels/test02"

# Get a list of all the Excel files in the folder
excel_files = os.listdir(folder_path)

# Create an empty DataFrame to store the merged data
merged_df = pd.DataFrame()

# Iterate over the Excel files
for excel_file in excel_files:

    # Read the Excel file into a DataFrame
    df = pd.read_excel(os.path.join(folder_path, excel_file))

    # Append the DataFrame to the merged DataFrame
    merged_df = merged_df.append(df)

# Write the merged DataFrame to a new Excel file
merged_df.to_excel("merged_excel_file.xlsx", index=False)