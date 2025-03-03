import os
import openpyxl

for file in os.listdir():
    if file.endswith(".xlsx"):
        workbook = openpyxl.load_workbook(file)
        sheet = workbook.active
        sheet.delete_rows(1, 6)
        sheet.delete_cols(1)
        workbook.save(file)