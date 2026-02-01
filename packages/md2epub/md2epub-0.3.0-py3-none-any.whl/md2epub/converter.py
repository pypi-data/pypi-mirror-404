
import markdown
import re

def md_to_html(md_content):
    """
    Convert Markdown content to HTML with specific formatting rules.
    """
    
    # Pre-processing for custom separators
    # "xxx" -> Scene Break
    # "***" -> Asterisk Break
    
    # We want these to be on their own line.
    # Regex to find lines that are exactly "xxx" or "***" (ignoring whitespace)
    
    lines = md_content.split('\n')
    processed_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped == "xxx":
            processed_lines.append('<div class="scene-break">xxx</div>')
        elif stripped == "***":
            processed_lines.append('<div class="asterisk-break">***</div>')
        else:
            processed_lines.append(line)
            
    content = '\n'.join(processed_lines)
    
    # Convert to HTML
    # We use 'fenced_code' for code blocks
    html = markdown.markdown(content, extensions=['fenced_code', 'nl2br'])
    
    # Post-processing if needed
    # Block quotes are handled by standard markdown (> -> blockquote)
    # Code blocks are handled by fenced_code (``` -> <pre><code>)
    
    return html
