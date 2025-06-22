import subprocess

def run_command(command):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Error message: {e.stderr}")
        return None

# Check git status
print("=== Git Status ===")
status_result = run_command("git status")
if status_result:
    print(status_result)

# Create empty commit
print("\n=== Creating Empty Commit ===")
commit_result = run_command('git commit --allow-empty -m "Empty commit to sync repository"')
if commit_result:
    print(commit_result)

# Push the commit
print("\n=== Pushing to Remote Repository ===")
push_result = run_command("git push")
if push_result:
    print(push_result)

print("\nGit operations completed.")
