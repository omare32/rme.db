from flask import Flask, render_template, request
import pandas as pd
import os
import webbrowser
from threading import Timer

def open_browser():
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open_new('http://127.0.0.1:5000/')

# Define a list to store project data (alternative to file system)
projects = {}

excel_folder = "excel_files"
project_names = []

for filename in os.listdir(excel_folder):
    if filename.endswith(".xlsx"):  # Check for Excel files
        project_name = os.path.splitext(filename)[0]  # Extract name
        project_names.append(project_name)

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html", project_names=project_names)

@app.route("/project", methods=["POST"])
def show_project():
    if 'project' in request.form:
        selected_project = request.form["project"]
        print(selected_project)  # Debug: Print selected project name

        if selected_project in projects:
            project_table = projects[selected_project]  # Get project data
            return render_template("forms.html", project_table=project_table.to_html())
        else:
            print(projects.keys())  # Debug: Print project keys in dictionary
            return render_template("forms.html", message="Project not found!")
    else:
        return render_template("forms.html", message="Please select a project.")

  
if __name__ == "__main__":
  excel_folder = "excel_files"  # Adjust if needed
  projects = {}

  for filename in os.listdir(excel_folder):
    if filename.endswith(".xlsx"):  # Check for Excel files
      project_name = filename.split(".")[0]
      file_path = os.path.join(excel_folder, filename)  # Construct full path
      try:
        projects[project_name] = pd.read_excel(file_path)
      except FileNotFoundError:
        print(f"Warning: Excel file not found for project: {project_name}")

  Timer(1, open_browser).start()
  app.run(debug=True)