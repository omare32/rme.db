import os
import subprocess
import argparse

def run_command(command):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Error message: {e.stderr}")
        return None

def git_status():
    """Check git status"""
    return run_command("git status")

def git_add(files="."):
    """Add files to git staging"""
    return run_command(f"git add {files}")

def git_commit(message):
    """Commit changes with a message"""
    return run_command(f'git commit -m "{message}"')

def git_push():
    """Push changes to remote repository"""
    return run_command("git push")

def main():
    parser = argparse.ArgumentParser(description="Automate git operations")
    parser.add_argument(
        "--action", 
        choices=["status", "add", "commit", "push", "all"], 
        default="all",
        help="Git action to perform"
    )
    parser.add_argument(
        "--files", 
        default=".", 
        help="Files to add (default: all)"
    )
    parser.add_argument(
        "--message", 
        default="Update .gitignore with sensitive file patterns", 
        help="Commit message"
    )
    
    args = parser.parse_args()
    
    if args.action == "status" or args.action == "all":
        print("\n=== Git Status ===")
        status = git_status()
        if status:
            print(status)
    
    if args.action == "add" or args.action == "all":
        print(f"\n=== Adding files: {args.files} ===")
        add_result = git_add(args.files)
        if add_result:
            print(add_result)
    
    if args.action == "commit" or args.action == "all":
        print(f"\n=== Committing with message: {args.message} ===")
        commit_result = git_commit(args.message)
        if commit_result:
            print(commit_result)
    
    if args.action == "push" or args.action == "all":
        print("\n=== Pushing to remote repository ===")
        push_result = git_push()
        if push_result:
            print(push_result)

if __name__ == "__main__":
    main()