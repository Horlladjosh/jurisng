import subprocess

print("=" * 80)
print("CHECKING GIT STATUS & HISTORY")
print("=" * 80)

# Check git status
status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
print("Git Status Changes:")
print(status.stdout if status.stdout else "No uncommitted changes detected by git.")

# Check recent commit history
log = subprocess.run(["git", "log", "-n", "5", "--oneline"], capture_output=True, text=True)
print("\nRecent Git Commits:")
print(log.stdout)

print("=" * 80)
