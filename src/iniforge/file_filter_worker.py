import os
import re
from PySide6.QtCore import QThread, Signal

class FileFilterWorker(QThread):
    signal = Signal(list)

    def __init__(self, folder_path, file_filter_text, filter_content_text, filter_lines, regex, extensions, regex_mode=False, include_blank_lines=False):
        super().__init__()
        self.folder_path = folder_path
        self.file_filter_text = file_filter_text  # Filename filter
        self.filter_content_text = filter_content_text  # Full content filter (with blank lines)
        self.filter_lines = filter_lines
        self.regex = regex
        self.extensions = extensions
        self.regex_mode = regex_mode
        self.include_blank_lines = include_blank_lines
        self._is_cancelled = False

    def run(self):
        filtered_files = []
        try:
            regex = re.compile(self.file_filter_text, re.IGNORECASE)
        except re.error:
            regex = re.compile('.*')

        # Compile regex pattern for content filtering if regex mode is enabled
        content_regex = None
        if self.regex_mode and self.regex:
            try:
                content_regex = re.compile(self.regex, re.IGNORECASE | re.DOTALL)
            except re.error:
                content_regex = None

        for root, _, files in os.walk(self.folder_path):
            if self._is_cancelled:
                break
            for file in files:
                if self._is_cancelled:
                    break
                if any(file.endswith(f'.{ext}') for ext in self.extensions):
                    file_path = os.path.join(root, file)
                    if regex.search(file):
                        # Filter by content based on mode
                        if self.regex_mode:
                            # Regex mode: use ONLY regex pattern
                            if content_regex:
                                with open(file_path, 'r') as f:
                                    content = f.read()
                                    if content_regex.search(content):
                                        filtered_files.append(file_path)
                        else:
                            # Non-regex mode: use ONLY content filter field
                            if self.filter_lines or self.filter_content_text:
                                with open(file_path, 'r') as f:
                                    content = f.read()
                                    
                                    if self.include_blank_lines:
                                        # Treat filter_content_text as a single string (keeps blank lines)
                                        if self.filter_content_text and self.filter_content_text in content:
                                            filtered_files.append(file_path)
                                    else:
                                        # Split by lines and check each line
                                        if self.filter_lines and all(line in content for line in self.filter_lines):
                                            filtered_files.append(file_path)
                            else:
                                # No filter specified, include all matching files
                                filtered_files.append(file_path)

        self.signal.emit(filtered_files)

    def cancel(self):
        self._is_cancelled = True