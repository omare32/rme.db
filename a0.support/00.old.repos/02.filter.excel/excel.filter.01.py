import pandas as pd

# Import the Excel file
df = pd.read_excel("input.xlsx")

# Filter the data by the specified column
filtered_df = df[df["Column Name"] == "Value"]

# Save the filtered data to a new Excel file
filtered_df.to_excel("output.xlsx")