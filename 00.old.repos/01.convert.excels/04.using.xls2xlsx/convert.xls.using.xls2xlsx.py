import os
import xls2xlsx

current_directory = os.getcwd()
for xls_file in os.listdir(current_directory):
    if xls_file.endswith(".xls"):
        xls2xlsx.convert(xls_file)