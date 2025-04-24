y mimport subprocess
import argparse

def run_git_command(command_list):
    """Run a git command using subprocess and return the output"""
    try:
        # Using subprocess with shell=False for better cross-platform compatibility
        # and to avoid PowerShell issues
        result = subprocess.run(
            command_list,
            shell=False,
            check=False,  # Don't raise exception on non-zero exit
            text=True,
            capture_output=True
        )
        
        # Print both stdout and stderr for debugging
        if result.stdout:
            print("STDOUT:", result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
            
        print(f"Return code: {result.returncode}")
        
        return result.returncode == 0
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Simple git operations")
    parser.add_argument(
        "--action", 
        choices=["status", "add", "commit", "push"], 
        default="status",
        help="Git action to perform"
    )
    parser.add_argument(
        "--files", 
        default=".", 
        help="Files to add (default: all)"
    )
    parser.add_argument(
        "--message", 
        default="Auto commit", 
        help="Commit message"
    )
    
    args = parser.parse_args()
    
    # Get the current working directory for debugging
    print(f"Current working directory: {subprocess.run(['pwd'], shell=False, capture_output=True, text=True).stdout}")
    
    # Test git version to verify git is accessible
    print("\n=== Testing Git Installation ===")
    run_git_command(["git", "--version"])
    
    if args.action == "status":
        print("\n=== Git Status ===")
        run_git_command(["git", "status"])
    
    elif args.action == "add":
        print(f"\n=== Adding files: {args.files} ===")
        if args.files == ".":
            run_git_command(["git", "add", "."])
        else:
            # Split multiple files by space
            files = args.files.split()
            command = ["git", "add"] + files
            run_git_command(command)
    
    elif args.action == "commit":
        print(f"\n=== Committing with message: {args.message} ===")
        run_git_command(["git", "commit", "-m", args.message])
    
    elif args.action == "push":
        print("\n=== Pushing to remote repository ===")
        run_git_command(["git", "push"])

if __name__ == "__main__":
    main()