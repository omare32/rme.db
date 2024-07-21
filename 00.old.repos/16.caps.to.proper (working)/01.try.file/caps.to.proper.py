import openpyxl

# Get the workbook and sheet
wb = openpyxl.load_workbook("Koumassi Flyover BOQ English.xlsx")
sheet = wb.active

# Loop through the rows in the sheet
for row in sheet.iter_rows():
    # Loop through the cells in the row
    for cell in row:
        # Check if the cell contains a value
        if cell.value is not None:
            # Check if the value is a string
            if isinstance(cell.value, str):
                # Check if the value is all caps
                if cell.value.isupper():
                    # Convert the text to proper case
                    cell.value = cell.value.title()
            else:
                # The value is not a string, so do nothing
                pass

# Save the workbook
wb.save("Koumassi Flyover BOQ English Proper.xlsx")