import pandas as pd
import os

# Get a list of all Excel files in the current directory
excel_files = []
for file in os.listdir():
    if file.endswith(".xlsx"):
        excel_files.append(file)

# Loop through each Excel file
for excel_file in excel_files:
    # Read the Excel file into a Pandas DataFrame
    df = pd.read_excel(excel_file)

    # Remove duplicates from column B
    df = df.drop_duplicates(subset=["B"])

    # Create a new sheet
    new_sheet = df.copy()

    # Set column A to the new list without duplicates
    new_sheet["A"] = new_sheet["B"].unique()

    # Save the new sheet
    new_sheet.to_excel(excel_file + "_new.xlsx")

# Check if the new Excel files were created
for excel_file in excel_files:
    if os.path.exists(excel_file + "_new.xlsx"):
        print("The new Excel file was created successfully")
    else:
        print("The new Excel file was not created")