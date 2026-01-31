import os
import re
import httpx

# Path to the file.md
file_path = 'file.md'

# Read the content of file.md
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Parse the groups
groups = []
current_title = None
current_links = []

for line in lines:
    line = line.strip()
    if line.startswith('## '):
        if current_title:
            groups.append((current_title, current_links))
        current_title = line[3:].strip()
        current_links = []
    elif line.startswith('- [') and current_title:
        # Extract url from - [text](url)
        match = re.search(r'\]\(([^)]+)\)', line)
        if match:
            url = match.group(1)
            if url.endswith('.md'):
                current_links.append(url)

if current_title:
    groups.append((current_title, current_links))

# Base URL
base_url = 'https://ai.pydantic.dev/'

# Loop over groups
for title, urls in groups:
    # Create directory for the group
    group_dir = title.replace(' ', '_').replace('/', '_')  # Sanitize title for dir name
    os.makedirs(group_dir, exist_ok=True)
    
    for url in urls:
        if url.startswith(base_url):
            # Get the relative path
            relative_path = url[len(base_url):]
            full_path = os.path.join(group_dir, relative_path)
            # Create directories if needed
            dir_path = os.path.dirname(full_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            # Download the content
            try:
                response = httpx.get(url)
                response.raise_for_status()
                # Save to file
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"Downloaded: {full_path}")
            except httpx.RequestError as e:
                print(f"Failed to download {url}: {e}")