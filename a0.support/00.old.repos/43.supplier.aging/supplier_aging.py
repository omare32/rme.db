import pandas as pd
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from tqdm import tqdm
import os

def file_prompt(msg):
    # Prompt user to select Excel file
    root = Tk()
    root.withdraw()
    ini_file_path = os.getcwd()
    excel_file_path = askopenfilename(title=msg, filetypes=[("Excel Files", "*.xls*")], initialdir=ini_file_path)
    root.destroy()
    return excel_file_path

def reordering(dataframe, pos, name):
    column_moved = dataframe[name]
    dataframe.pop(name)
    dataframe.insert(pos, name, column_moved)

path = file_prompt('Choose your Excel file')
df = pd.read_excel(path)

df.columns = df.loc[38]
cutoff = df['Project Name'][4] # extract cutoff date
df = df[35:]
df = df.reset_index(drop=True)

# Initiation
pos_proj_name = df['User INV Type'][0].find(':') + 2
proj_name = df['User INV Type'][0][pos_proj_name:]
df.loc[0, 'Project Name'] = proj_name

pos_s_num = df['User INV Type'][1].find(':') + 2
supplier_num = df['User INV Type'][1][pos_s_num:]
df.loc[0, 'Supplier Number'] = supplier_num

pos_s_name = df['User INV Type'][2].find(':') + 2
supplier_name = df['User INV Type'][2][pos_s_name:]
df.loc[0, 'Supplier Name'] = supplier_name

# Process DataFrame
total_rows = len(df)
for index, row in tqdm(df.iterrows(), total=total_rows):
    inv_type = df.loc[index, 'User INV Type']
    if isinstance(inv_type, str):
        if inv_type[:12] == "Project Name":
            pos_proj_name = inv_type.find(':') + 2
            proj_name = inv_type[pos_proj_name:]
            df.loc[index, 'Project Name'] = 'No Name' if proj_name == '' else proj_name

            supplier_num = df.loc[index + 1, 'User INV Type'][pos_s_num:]
            df.loc[index, 'Supplier Number'] = supplier_num

            supplier_name = df.loc[index + 2, 'User INV Type'][pos_s_name:]
            df.loc[index, 'Supplier Name'] = supplier_name
        else:
            df.loc[index, 'Project Name'] = proj_name
            df.loc[index, 'Supplier Number'] = supplier_num
            df.loc[index, 'Supplier Name'] = supplier_name
    else:
        df.loc[index, 'Project Name'] = proj_name
        df.loc[index, 'Supplier Number'] = supplier_num
        df.loc[index, 'Supplier Name'] = supplier_name

# Removing excess rows
df = df[pd.to_numeric(df['User INV Type'], errors='coerce').notna()]
df.reset_index(drop=True, inplace=True)

# Reordering
reordering(df, 2, 'Supplier Number')
reordering(df, 3, 'Supplier Name')

df.to_csv('SWD Fixed.csv', index=False, encoding='utf-8-sig')
