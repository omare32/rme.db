import pandas as pd
import os
import glob

excel_files = glob.glob("*.xlsx")

for excel_file in excel_files:
    excel = pd.read_excel(excel_file, sheet_name=None)
    df = pd.DataFrame()
    for sheet_name, sheet_data in excel_file.items():
        if '    تصفيه عهده' in sheet_data.columns[1]:
            sheet_data.columns = sheet_data.loc[4]
            sheet_data = sheet_data[6:]
            keep = []
            for index, value in sheet_data.iloc[:,1].iteritems():
                if pd.isna(value):
                    break
                else:
                    keep.append(index)
            sheet_data = sheet_data[sheet_data.index.isin(keep)]
            df = df.append(sheet_data, ignore_index=True)
            new_file_name = excel_file + "_new"
            df.to_excel(new_file_name)