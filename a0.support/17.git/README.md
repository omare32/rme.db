# Git Commands Reference

## Running Git Commands Directly in Terminal

Instead of using Python scripts, you can run git commands directly in your terminal:

```powershell
# Check git status
git status

# Add all files to staging
git add .

# Add specific files
git add file1.py file2.py

# Commit changes
git commit -m "Your commit message here"

# Push changes to remote repository
git push

# Pull changes from remote repository
git pull
```

## Common Git Workflows

### Updating .gitignore and committing changes

```powershell
# Edit .gitignore file to add patterns for files you want to ignore
# Then run:
git add .gitignore
git commit -m "Update .gitignore with sensitive file patterns"
git push
```

### Creating a new branch

```powershell
git checkout -b new-branch-name
```

### Switching branches

```powershell
git checkout branch-name
```

### Merging branches

```powershell
git checkout main
git merge branch-name
```

This approach keeps your repository clean without Python script files in the root directory.