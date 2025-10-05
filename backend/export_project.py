import os

# --- Configuration ---
# Add any other directories or files you want to ignore
EXCLUDED_DIRS = {".git", "__pycache__", "node_modules", "instance", ".vscode"}
EXCLUDED_FILES = {".DS_Store", "timetable.db"}
# -------------------

def generate_project_text(start_path="."):
    """
    Walks through a directory and generates a single text representation
    of the project structure and file contents.
    """
    output = []
    for root, dirs, files in os.walk(start_path, topdown=True):
        # Exclude specified directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        
        # Sort files and directories for consistent output
        dirs.sort()
        files.sort()
        
        # Get the current directory relative to the start path
        relative_path = os.path.relpath(root, start_path)
        if relative_path == ".":
            level = 0
        else:
            level = len(relative_path.split(os.sep))
            
        # Add directory structure to output
        if level == 0:
            output.append(f"\n--- Project Root: {os.path.basename(os.path.abspath(start_path))} ---\n")
        else:
            indent = "    " * (level - 1) + "|-- "
            output.append(f"{indent}{os.path.basename(root)}/")

        # Add file contents to output
        file_indent = "    " * level + "|-- "
        for filename in files:
            if filename in EXCLUDED_FILES:
                continue
            
            output.append(f"{file_indent}{filename}")
            try:
                with open(os.path.join(root, filename), "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    output.append("```")
                    output.append(content)
                    output.append("```\n")
            except Exception as e:
                output.append(f"```\n[Error reading file: {e}]\n```\n")

    return "\n".join(output)

if __name__ == "__main__":
    project_path = os.getcwd()
    project_text = generate_project_text(project_path)
    
    # Save to a file
    output_filename = f"{os.path.basename(project_path)}_code.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(project_text)
        
    print(f"Project code has been exported to: {output_filename}")