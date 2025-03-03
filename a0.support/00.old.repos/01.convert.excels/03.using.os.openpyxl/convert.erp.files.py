import os
import openpyxl

def convert_xls_to_xlsx(xls_file):
    workbook = openpyxl.load_workbook(xls_file)
    workbook.save(os.path.join(os.getcwd(), xls_file[:-3] + "xlsx"))

current_directory = os.getcwd()
for xls_file in os.listdir(current_directory):
    if xls_file.endswith(".xls"):
        convert_xls_to_xlsx(xls_file)