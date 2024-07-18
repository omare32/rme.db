import os
import xlsxwriter

# Get the current working directory
current_directory = os.getcwd()

# Create a workbook object
workbook = xlsxwriter.Workbook(os.path.join(current_directory, 'rme.xlsx'))

# Create a worksheet object
worksheet = workbook.add_worksheet()

# Write data to the worksheet
worksheet.write('A1', 'Bridges Sector')

# Save the workbook
workbook.close()