import sys
import os
import subprocess

def main():
    # Get the directory of the current file
    cmd_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(cmd_dir, "app.py")
    
    # Always use the current working directory
    repo_path = os.path.abspath(os.getcwd())
    
    # Run streamlit
    # We pass the repo_path as an argument to the streamlit script
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        app_path, 
        "--", repo_path
    ])

if __name__ == "__main__":
    main()
