import os
import configparser

def get_config_sections(folder_path, extensions):
    all_sections = set()
    print(f"Reading available sections from {folder_path}...", end="", flush=True)
    for root, _, files in os.walk(folder_path):
        for file in files:
            if any(file.lower().endswith(f'.{ext}') for ext in extensions):
                file_path = os.path.join(root, file)
                config = configparser.ConfigParser()
                try:
                    config.read(file_path)
                    all_sections.update(config.sections())
                except Exception:
                    pass
    print("[OK]")
    return sorted(all_sections)

def get_section_line_index(content, section, add_at_start=False):
    start_of_section = None
    end_of_section = None

    for i, line in enumerate(content):
        if f"[{section}]" == line.strip():
            start_of_section = i + 1
            
            # Skip any comment lines at the start of the section
            while start_of_section < len(content) and content[start_of_section].strip().startswith(';'):
                start_of_section += 1
            
            if add_at_start:
                return start_of_section, True
            
            # Find the end of this section
            end_of_section = start_of_section
            while end_of_section < len(content):
                if content[end_of_section].strip().startswith('['):
                    break
                end_of_section += 1
            
            # If we found the end of the section, return the last line of the section
            if end_of_section > start_of_section:
                return end_of_section, True
            return start_of_section, True

    # If section not found, return the end of file
    return len(content), False

def process_insertion(file_path, section, config_lines, add_at_start):
    with open(file_path, 'r') as f:
        content = f.readlines()
    
    line_index, section_found = get_section_line_index(content, section, add_at_start)
    
    if not section_found:
        # Section doesn't exist, add it at the end of file
        # Add a newline before the section if file is not empty and doesn't end with newline
        if content and not content[-1].endswith('\n'):
            content.append('\n')
        # Add section header and content
        content.append(f"[{section}]\n")
        content.extend(config_lines)
    else:
        # Section exists, insert content at the appropriate position
        if line_index == len(content)-1:  # If at end of file
            content.append('\n')  # Add newline before content
        content[line_index:line_index] = config_lines  # Insert content at line_index
    
    with open(file_path, 'w') as f:
        f.writelines(content)

def process_replacement(file_path, filter_text, replace_text, include_blank):
    with open(file_path, 'r') as f:
        content = f.read()

    if include_blank:
        # Treat filter_text as single string including blank lines
        if filter_text in content:
            content = content.replace(filter_text, replace_text)
            with open(file_path, 'w') as f:
                f.write(content)
    else:
        # Split by lines
        filter_lines = filter_text.splitlines()
        replace_lines = replace_text.splitlines()
        filter_lines  = [l for l in filter_lines if l.strip()]
        
        if len(filter_lines) == 1:
            if all(line in content for line in filter_lines):
                for line in filter_lines:
                    if replace_lines:
                        content = content.replace(line, "\n".join(replace_lines))
                    else:
                        content = content.replace(line, '')
                with open(file_path, 'w') as f:
                    f.write(content)
        else:
            content = content.replace(filter_text, replace_text)
            with open(file_path, 'w') as f:
                f.write(content)

def process_removal(file_path, filter_text, include_blank):
    with open(file_path, 'r') as f:
        content = f.read()

    if include_blank:
        # Treat filter_text as single string including blank lines
        if filter_text in content:
            content = content.replace(filter_text, '')
            with open(file_path, 'w') as f:
                f.write(content)
    else:
        # Original behavior: split by lines
        filter_lines = filter_text.splitlines()
        filter_lines  = [l for l in filter_lines if l.strip()]
        
        if len(filter_lines) == 1:
            if all(line in content for line in filter_lines):
                for line in filter_lines:
                    content = content.replace(f"{line}\n", '')
                with open(file_path, 'w') as f:
                    f.write(content)
        else:
            content = content.replace(f"{filter_text}\n", '')
            with open(file_path, 'w') as f:
                f.write(content)