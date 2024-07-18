import os

# Get the current working directory
cwd = os.getcwd()

# Get a list of all the files in the current working directory
files = os.listdir(cwd)

# Open a text file for writing
with open("files.txt", "w") as f:

    # Write the list of files to the text file
    for file in files:
        f.write(file + "\n")

# Close the text file
f.close()