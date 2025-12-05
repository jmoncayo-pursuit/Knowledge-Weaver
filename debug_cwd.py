import os
with open("/Users/jmoncayopursuit.org/Desktop/kiro-dev-2025/Knowledge-Weaver/cwd_log.txt", "w") as f:
    f.write(f"Current working directory: {os.getcwd()}\n")
    f.write(f"Files: {os.listdir('.')}\n")

