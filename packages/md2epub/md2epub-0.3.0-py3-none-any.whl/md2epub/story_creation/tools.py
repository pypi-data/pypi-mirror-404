import os

def write_markdown_file(filename: str, content: str, output_dir: str = "output"):
    """Writes content to a markdown file in the specified directory."""
    # Ensure story-elements subdirectory if not already in path
    if not output_dir.endswith("story-elements"):
        final_output_dir = os.path.join(output_dir, "story-elements")
    else:
        final_output_dir = output_dir
        
    os.makedirs(final_output_dir, exist_ok=True)
    filepath = os.path.join(final_output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Successfully wrote to {filepath}"

def read_markdown_file(filename: str, input_dir: str = "output"):
    """Reads content from a markdown file."""
    filepath = os.path.join(input_dir, filename)
    if not os.path.exists(filepath):
        return f"File {filename} not found."
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()
