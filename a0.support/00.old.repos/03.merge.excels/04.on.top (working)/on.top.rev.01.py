import pandas as pd
import glob

# Get the list of all Excel files in the current directory
filenames = glob.glob("*.xlsx")

# Initialize an empty DataFrame to store the merged data
final_excel_sheet = pd.DataFrame()

# Iterate through the Excel files and append their data to the DataFrame
for filename in filenames:
    df = pd.read_excel(filename)
    final_excel_sheet = pd.concat([final_excel_sheet, df], ignore_index=True)

# Save the merged DataFrame to a new Excel file
final_excel_sheet.to_excel('merged_excel_sheets.xlsx')