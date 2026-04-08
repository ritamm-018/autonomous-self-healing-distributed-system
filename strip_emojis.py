import os
import emoji

# Some emojis/symbols might not be covered by the basic emoji package, so we also remove some common ones manually if needed.
# The emoji package is very thorough though.
def strip_emojis(text):
    res = emoji.replace_emoji(text, replace='')
    # Also remove some leftover variation selectors and common symbol remnants
    res = res.replace('\ufe0f', '').replace('\u200d', '')
    return res

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = strip_emojis(content)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Cleaned: {filepath}")
    except UnicodeDecodeError:
        pass
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

allowed_extensions = {
    '.md', '.txt', '.java', '.html', '.css', '.js', '.ts', '.yaml', 
    '.yml', '.sh', '.py', '.json', '.xml', '.properties'
}

exclude_dirs = {'.git', '.gemini', '.venv', 'venv', 'node_modules', 'target', 'build', 'dist'}

for root, dirs, files in os.walk('.'):
    # Modify dirs in-place to avoid traversing excluded directories
    dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
    for file in files:
        if file.startswith('.'):
            continue
        ext = os.path.splitext(file)[1].lower()
        if ext in allowed_extensions or 'Dockerfile' in file:
            process_file(os.path.join(root, file))

print("Done stripping emojis.")
