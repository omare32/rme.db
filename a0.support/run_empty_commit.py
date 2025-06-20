import sys
import os

# Add the directory containing git_auto_commit.py to the Python path
sys.path.append('17.git')

# Import functions from git_auto_commit.py
from git_auto_commit import run_command, git_status, git_commit, git_push

# Check git status
print("=== Git Status ===")
status_result = git_status()
if status_result:
    print(status_result)

# Create empty commit
print("\n=== Creating Empty Commit ===")
commit_result = run_command('git commit --allow-empty -m "Empty commit to sync repository"')
if commit_result:
    print(commit_result)

# Push the commit
print("\n=== Pushing to Remote Repository ===")
push_result = git_push()
if push_result:
    print(push_result)

print("\nGit operations completed.")
