import os
import glob
import pandas as pd
import openpyxl

excel_files = glob.glob("*.xlsx")

data_frames = []
for excel_file in excel_files:
    df = pd.read_excel(excel_file)
    data_frames.append(df)
	
filtered_df = pd.concat(data_frames)

# Filter the DataFrame on the column "Trx Type\n" for the strings "Move Order Issue on Project", "RME Issue ( On Project)", "RME Site Return"
filtered_df = filtered_df[filtered_df["Trx Type\n"].str.rstrip("\n").isin(["Move Order Issue on Project", "RME Issue ( On Project)", "RME Site Return"])]

# Get the name of the original Excel file from the current directory
original_excel_file = os.path.basename(excel_files[0])

# Append the filtered DataFrame to the original Excel file without deleting the original tab
with pd.ExcelWriter(original_excel_file, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name="Mat Mov", index=False)
    filtered_df.to_excel(writer, sheet_name="On Project", index=False)