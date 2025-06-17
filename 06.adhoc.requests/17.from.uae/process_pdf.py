import pdfplumber
import pandas as pd
import re
import os

# Define input and output file paths
input_pdf = r"d:\OneDrive2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db\06.adhoc.requests\17.from.uae\ADWEA_APPROVED_CONTRACTORS_LIST.pdf"
output_excel = r"d:\OneDrive2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db\06.adhoc.requests\17.from.uae\ADWEA_APPROVED_CONTRACTORS_LIST.xlsx"

# Function to extract Work Group and Criteria from page text
def extract_headers(page_text):
    work_group_match = re.search(r'Work Group:\s*(.*?)(?:\n|Criteria)', page_text)
    criteria_match = re.search(r'Criteria :\s*(.*?)(?:\n|Company ID)', page_text)
    
    work_group = work_group_match.group(1).strip() if work_group_match else ""
    criteria = criteria_match.group(1).strip() if criteria_match else ""
    
    return work_group, criteria

# Initialize list to store all dataframes
all_tables = []

print("Processing PDF file...")

# Open the PDF file
with pdfplumber.open(input_pdf) as pdf:
    # Loop through each page
    for page_num, page in enumerate(pdf.pages):
        print(f"Processing page {page_num + 1} of {len(pdf.pages)}...")
        
        # Extract text for header information
        text = page.extract_text()
        
        # Extract Work Group and Criteria
        work_group, criteria = extract_headers(text)
        
        # Extract tables from the page
        tables = page.extract_tables()
        
        for table in tables:
            if not table or len(table) < 2:  # Skip empty tables or tables with just headers
                continue
            
            header_row_idx = None
            for i, row in enumerate(table):
                # Use a more robust check for the header
                if any(col and 'Company ID' in str(col) for col in row):
                    header_row_idx = i
                    break
            
            if header_row_idx is None:
                continue
            
            headers = table[header_row_idx]
            # Clean up headers
            headers = [str(h).replace('\n', ' ').strip() if h else f'Unnamed: {i}' for i, h in enumerate(headers)]
            data_rows = table[header_row_idx + 1:]
            
            data_rows = [row for row in data_rows if any(cell and str(cell).strip() for cell in row)]
            
            if data_rows:
                df = pd.DataFrame(data_rows, columns=headers)
                
                df['Work Group'] = work_group
                df['Criteria'] = criteria
                
                all_tables.append(df)

if all_tables:
    combined_df = pd.concat(all_tables, ignore_index=True)
    
    # Reorder columns to have Work Group and Criteria first
    cols = combined_df.columns.tolist()
    if 'Work Group' in cols and 'Criteria' in cols:
        cols.insert(0, cols.pop(cols.index('Criteria')))
        cols.insert(0, cols.pop(cols.index('Work Group')))
        combined_df = combined_df[cols]

    # Clean up dataframe
    combined_df = combined_df.dropna(axis=1, how='all')
    combined_df = combined_df.dropna(how='all')
    
    print(f"Saving data to Excel file: {output_excel}")
    combined_df.to_excel(output_excel, index=False)
    print(f"Successfully extracted {len(combined_df)} contractor records.")
    print(f"Excel file saved at: {os.path.abspath(output_excel)}")
else:
    print("No valid contractor tables found in the PDF.")
