import os
import argparse
import iniforge
import pyperclip
import platform
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit,
    QListWidget, QPushButton, QFileDialog, QLabel, QSplitter, QListWidgetItem,
    QPlainTextEdit, QScrollArea, QMessageBox, QDialog, QCheckBox, QComboBox, QTabWidget
)
from PySide6.QtCore import Qt, QSize, Signal, QSettings, QTimer, QThread, QThreadPool
from PySide6.QtGui import (QIcon, QFont, QTextOption, QTextBlockFormat, QFontMetrics, QTextCursor, QTextDocument, QTextCharFormat)
from .Logger import Logger
from .widgets.QSqrdSwitchButton import QSqrdSwitchButton
from .widgets.QAboutDialog import QAboutDialog
from .widgets.QExtensionsDialog import QExtensionsDialog
from .meld import Meld
from .file_filter_worker import FileFilterWorker
from . import core

# Set Windows App User Model ID for proper taskbar icon display
if platform.system() == "Windows":
    try:
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID("iniForge.iniForge")
    except Exception:
        pass

os.environ['IFORGE_LOG_LEVEL'] = 'info'
parser = argparse.ArgumentParser(description="iniForge: Bulk ini Files Manager")
parser.add_argument('-b', '--debug', action='store_true', default=False, help='Run tool in debug mode')
args = parser.parse_args()
if args.debug:
    print("####### DEBUG MODE ACTIVATED #######")
    os.environ['IFORGE_LOG_LEVEL'] = 'debug'

class GUI(QWidget):
    def __init__(self):
        super().__init__()
        self.app_path = os.path.dirname(os.path.abspath(__file__))
        self.log = Logger()
        self.log.propagate = True
        self.file_selected = False
        self.selected_file = None
        self.extensions = ['ini']
        
        # Check meld availability
        self.meld_path = Meld.get_path()
        self.meld_available = self.meld_path is not None

        self.setWindowTitle("iniForge: Bulk Settings Precision")
        self.setGeometry(100, 100, 1200, 600)
        icon_path = os.path.join(self.app_path, "images", "icon.ico")
        print
        self.setWindowIcon(QIcon(icon_path))

        self.settings = QSettings(f"{self.app_path}/config.ini", QSettings.IniFormat)
        self.thread_pool = QThreadPool()
        self.filter_timer = QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.filter_files)

        self.main_layout = QVBoxLayout()

        # Top layout for working directory selection
        top_layout = QHBoxLayout()
        self.working_dir_line_edit = QLineEdit()
        self.working_dir_line_edit.setClearButtonEnabled(True)
        self.working_dir_line_edit.setToolTip("Enter or paste the folder path containing the configuration files\n(Press Enter to load files from this directory)")
        # Cross-platform: Linux uses USER, Windows uses USERNAME
        self.user = os.environ.get('USER') or os.environ.get('USERNAME') or 'default'
        self.log.info(f"Loading git repository for user: {self.user}")
        self.user_repo_dir = self.settings.value(f"{self.user}/working_directory", os.getcwd())
        self.getExtension()
        self.working_dir_line_edit.setText(self.user_repo_dir)

        # Connect the returnPressed signal to the navigate_to_directory slot
        self.working_dir_line_edit.returnPressed.connect(self.navigate_to_directory)

        # Paste button
        paste_button = QPushButton()
        self.set_button_icon(paste_button, 'paste.png')
        paste_button.clicked.connect(self.paste_directory)
        paste_button.setToolTip("Paste folder path from clipboard\n(Copy a folder path, then click to paste it here)")

        # Enter button
        reload_button = QPushButton()
        self.set_button_icon(reload_button, 'refresh.png')
        reload_button.clicked.connect(lambda: self.reload_files(self.working_dir_line_edit.text()))
        reload_button.setToolTip("Reload files from current directory\n(Refresh the file list to see changes)")
        
        browse_button = QPushButton()
        self.set_button_icon(browse_button, 'openfile.png')
        browse_button.setToolTip("Browse for folder containing the configuration files\n(Opens a folder selection dialog)")
        browse_button.clicked.connect(self.browse_folder)
        
        meld_button = QPushButton()
        self.set_button_icon(meld_button, 'meld.png')
        meld_button.setToolTip("Click to open meld" if self.meld_available else "Meld is not installed")
        meld_button.setEnabled(self.meld_available)
        meld_button.clicked.connect(self.open_meld)
        
        about_button = QPushButton()
        self.set_button_icon(about_button, 'about.png')
        about_button.setToolTip("About this application")
        about_button.clicked.connect(self.open_about)
        
        help_button = QPushButton()
        self.set_button_icon(help_button, 'user_manual.png')  # You can use a different help.png icon
        help_button.setToolTip("Show help guide and keyboard shortcuts")
        help_button.clicked.connect(self.show_help_guide)

        # Create theme switch
        self.theme_switch = QSqrdSwitchButton(self)
        self.theme_switch.setFixedHeight(16)
        self.theme_switch.setToolTip("Click to switch between light and dark theme")
        self.theme_switch.clicked.connect(lambda: self.toggle_theme(self.theme_switch.isChecked()))

        top_layout.addWidget(QLabel("Working Directory"))
        top_layout.addWidget(self.working_dir_line_edit)
        top_layout.addWidget(paste_button)
        top_layout.addWidget(reload_button)
        top_layout.addWidget(browse_button)
        top_layout.addWidget(meld_button)
        top_layout.addWidget(help_button)
        top_layout.addWidget(about_button)

        self.main_layout.addLayout(top_layout)

        # Main horizontal splitter for File Directory and other sections
        main_splitter = QSplitter(Qt.Horizontal)

        # Create the file list (File Directory)
        file_directory_widget = self.create_file_directory()
        main_splitter.addWidget(file_directory_widget)

        # Create vertical splitter for Replacer Mode and File Viewer Mode
        right_splitter = QSplitter(Qt.Vertical)

        # Create Replacer Mode section
        forge_mode = self.create_forge_mode()
        right_splitter.addWidget(forge_mode)

        # Create File Viewer Mode section
        file_viewer_mode = self.create_file_viewer_mode()
        right_splitter.addWidget(file_viewer_mode)

        # Set initial sizes for the vertical sections (30% for Replacer Mode, 70% for File Viewer Mode)
        right_splitter.setSizes([int(0.3 * 600), int(0.7 * 600)])

        # Add right splitter to main splitter
        main_splitter.addWidget(right_splitter)

        # Set initial sizes for the main sections
        main_splitter.setSizes([200, 1000])

        self.main_layout.addWidget(main_splitter)

        footer_hlayout = QHBoxLayout()
        footer_hlayout.addWidget(self.theme_switch)
        footer_hlayout.setAlignment(Qt.AlignRight)
        
        self.main_layout.addLayout(footer_hlayout)
        self.setLayout(self.main_layout)

        self.load_files()

    def getExtension(self):
        ext = self.settings.value("Base/filtered_extensions", defaultValue="ini")
        ext = ext.strip()
        if ext=="":
            self.extensions = ["ini"]
        elif ',' in ext:
            self.extensions = [ext.strip() for ext in ext.split(',')]
        elif ' ' in ext:
            self.extensions = [ext.strip() for ext in ext.split(',')]
        elif isinstance(ext, str):
            self.extensions = [ext.strip()]

    def show_extensions_dialog(self):
        """Show dialog to configure file extensions."""
        dialog = QExtensionsDialog(self, self.extensions)
        
        if dialog.exec() == QDialog.Accepted:
            new_extensions = dialog.get_extensions()
            if new_extensions:
                self.extensions = new_extensions
                # Save to settings
                self.settings.setValue("Base/filtered_extensions", ",".join(new_extensions))
                # Reload files with new extensions
                self.load_files()

    def open_about(self):
        about_dialog = QAboutDialog(self)
        about_dialog.exec()

    def show_help_guide(self):
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("ConfigReplacer Help Guide")
        help_dialog.setModal(True)
        help_dialog.resize(600, 500)
        
        layout = QVBoxLayout()
        help_dialog.setLayout(layout)
        
        # Create scrollable text area for help content
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        
        # Load help content from external file
        help_content = self.load_help_content()
        help_text.setHtml(help_content)
        layout.addWidget(help_text)
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(help_dialog.close)
        layout.addWidget(close_button)
        
        help_dialog.exec()

    def load_help_content(self):
        """Load help content from external HTML file"""
        help_file_path = os.path.join(self.app_path, "help_content.html")
        
        try:
            with open(help_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Convert relative image paths to absolute file:// URLs
            content = self.convert_image_paths_to_absolute(content)
            return content
            
        except FileNotFoundError:
            return self.get_fallback_help_content()
        except Exception as e:
            self.log.warning(f"Error loading help file: {e}")
            return self.get_fallback_help_content()
    
    def convert_image_paths_to_absolute(self, html_content):
        """Convert relative image paths in HTML to absolute file:// URLs"""
        import re
        
        # Pattern to find img src attributes with relative paths
        pattern = r'src="images/help/([^"]+)"'
        
        def replace_path(match):
            image_filename = match.group(1)
            absolute_path = os.path.join(self.app_path, "images", "help", image_filename)
            # Convert to file:// URL format, handling Windows paths
            if os.name == 'nt':  # Windows
                file_url = f"file:///{absolute_path.replace(os.sep, '/')}"
            else:  # Unix/Linux/Mac
                file_url = f"file://{absolute_path}"
            return f'src="{file_url}"'
        
        return re.sub(pattern, replace_path, html_content)
    
    def get_fallback_help_content(self):
        """Provide fallback help content if file cannot be loaded"""
        return """
        <h2>📖 iniForge Help</h2>
        <p><b>Help file not found!</b></p>
        <p>The help content file (help_content.html) could not be loaded.</p>
        <h3>Quick Tips:</h3>
        • Set working directory to folder containing .ini files<br>
        • Use the tabs to perform different operations<br>
        • Hover over buttons for tooltips<br>
        • Always backup files before bulk operations<br>
        """

    def handle_clear_shortcut(self, event, text_edit):
        # Handle Ctrl+Delete to clear text edit content
        if event.key() == Qt.Key_Delete and event.modifiers() == Qt.ControlModifier:
            text_edit.clear()
            event.accept()
        else:
            # Call the original keyPressEvent
            QTextEdit.keyPressEvent(text_edit, event)

    def clear_text_edit(self, text_edit):
        """Clear the content of a QTextEdit widget"""
        text_edit.clear()

    def update_clear_button_state(self, text_edit, clear_button):
        """Enable/disable clear button based on text content"""
        has_text = len(text_edit.toPlainText().strip()) > 0
        clear_button.setEnabled(has_text)

    def set_button_icon(self, btn, image):
        icon = QIcon(f"{os.path.dirname(os.path.abspath(__file__))}/images/{image}")
        btn.setIcon(icon)
        btn.setIconSize(QSize(14, 14))
        btn.setFixedSize(36, 24)

    def navigate_to_directory(self):
        folder_path = self.working_dir_line_edit.text()
        if os.path.isdir(folder_path):
            self.settings.setValue(f"{self.user}/working_directory", folder_path)
            self.load_files()
        else:
            QMessageBox.warning(self, "Invalid Directory", "Specified directory does not exist.")

    def create_file_directory(self):
        files_filter_layout = QVBoxLayout()
        
        # Filename filter with configure button
        filename_filter_layout = QHBoxLayout()
        self.file_filter_line_edit = QLineEdit()
        self.file_filter_line_edit.setClearButtonEnabled(True)
        self.file_filter_line_edit.setPlaceholderText("Filter by filename (regex supported)")
        self.file_filter_line_edit.setToolTip("Filter files by name using text or regex patterns")
        self.file_filter_line_edit.textChanged.connect(self.start_filter_timer)
        
        # Configure extensions button
        configure_extensions_button = QPushButton()
        self.set_button_icon(configure_extensions_button, 'settings.png')
        configure_extensions_button.setToolTip("Configure file extensions to filter")
        configure_extensions_button.clicked.connect(self.show_extensions_dialog)
        
        filename_filter_layout.addWidget(self.file_filter_line_edit)
        filename_filter_layout.addWidget(configure_extensions_button)

        self.file_list_widget = QListWidget()
        self.file_list_widget.itemDoubleClicked.connect(self.open_file_in_meld)
        self.file_list_widget.itemClicked.connect(self.display_file_content)

        files_filter_footer_layout = QHBoxLayout()
        # Filtered file count label
        self.filtered_file_count_label = QLabel("Filtered files: 0")
        # copy list of files button
        files_copy_button = QPushButton()
        self.set_button_icon(files_copy_button, 'copy.png')
        files_copy_button.setFixedSize(24, 24)
        files_copy_button.clicked.connect(self.copy_files_list)
        files_copy_button.setToolTip("Click to copy files list to clipboard")
        files_filter_footer_layout.addWidget(self.filtered_file_count_label)
        files_filter_footer_layout.addWidget(files_copy_button)

        files_filter_layout.addLayout(filename_filter_layout)
        files_filter_layout.addWidget(self.file_list_widget)
        files_filter_layout.addLayout(files_filter_footer_layout)

        files_filter_widget = QWidget()
        files_filter_widget.setLayout(files_filter_layout)

        return files_filter_widget

    def create_forge_mode(self):
        forge_mode = QWidget()
        forge_layout = QVBoxLayout()  # Use QVBoxLayout for main layout

        # Create a horizontal layout for the text boxes
        text_boxes_layout = QHBoxLayout()

        # Filter by content
        self.filter_text_edit = QTextEdit()
        self.filter_text_edit.textChanged.connect(self.start_filter_timer)
        # Add Ctrl+Delete shortcut to clear content
        self.filter_text_edit.setToolTip("Use Ctrl+Delete to clear content")
        self.filter_text_edit.keyPressEvent = lambda event: self.handle_clear_shortcut(event, self.filter_text_edit)
        
        # Add clear button for filter text
        self.filter_clear_button = QPushButton()
        self.set_button_icon(self.filter_clear_button, 'clear_text.png')
        self.filter_clear_button.clicked.connect(lambda: self.clear_text_edit(self.filter_text_edit))
        self.filter_clear_button.setToolTip("Clear filter content")
        self.filter_clear_button.setEnabled(False)
        self.filter_text_edit.textChanged.connect(lambda: self.update_clear_button_state(self.filter_text_edit, self.filter_clear_button))
        
        # Regex toggle button
        self.regex_toggle_button = QPushButton(".*")
        self.regex_toggle_button.setCheckable(True)
        self.regex_toggle_button.setChecked(False)
        self.regex_toggle_button.setFixedSize(36, 24)
        self.regex_toggle_button.setToolTip("Toggle regex mode for content filtering\n(When enabled, each line in filter text is treated as a regex pattern)")
        self.regex_toggle_button.clicked.connect(self.toggle_regex_mode)
        
        self.regex_expression = QLineEdit()
        self.regex_expression.setPlaceholderText("Enter regex patterns (oneliner)")
        self.regex_expression.setClearButtonEnabled(True)
        self.regex_expression.setToolTip("Enter regex pattern for content filtering (oneliner format)")
        self.regex_expression.setEnabled(False)  # Disabled by default, only show when regex mode is enabled
        # Add Ctrl+Delete shortcut to clear content
        self.regex_expression.setToolTip("Use Ctrl+Delete to clear content")
        
        # Include blank lines checkbox
        self.include_blank_lines_checkbox = QCheckBox("Include blank lines")
        self.include_blank_lines_checkbox.setChecked(False)
        self.include_blank_lines_checkbox.setToolTip("When enabled, filter text is treated as a single string including blank lines\n(Useful for patterns with empty lines between parameters)")

        filter_layout = QVBoxLayout()
        filter_header_layout = QHBoxLayout()
        filter_header_layout.addWidget(QLabel("Filter by content"))
        filter_header_layout.addWidget(self.filter_clear_button)
        filter_header_layout.setAlignment(self.filter_clear_button, Qt.AlignRight)
        filter_regex_layout = QHBoxLayout()
        filter_regex_layout.addWidget(self.regex_toggle_button)
        filter_regex_layout.addWidget(self.regex_expression)
        filter_regex_layout.addStretch()
        filter_layout.addLayout(filter_header_layout)
        filter_layout.addLayout(filter_regex_layout)
        filter_layout.addWidget(self.filter_text_edit)

        filter_layout.addWidget(self.include_blank_lines_checkbox)

        filter_widget = QWidget()
        filter_widget.setLayout(filter_layout)

        # Create tab widget
        tab_widget = QTabWidget()

        # Tab 1: Replace Content
        replace_widget = self.create_replace_tab()
        tab_widget.addTab(replace_widget, "Replace Content")

        # Tab 2: Add Configuration
        config_widget = self.create_config_tab()
        tab_widget.addTab(config_widget, "Add Configuration")

        # Tab 3: Remove Configuration
        remove_widget = self.create_remove_tab()
        tab_widget.addTab(remove_widget, "Remove Configuration")

        # Add both text boxes to the horizontal layout
        text_boxes_layout.addWidget(filter_widget)
        text_boxes_layout.addWidget(tab_widget)

        # Add the text boxes layout to the main vertical layout
        forge_layout.addLayout(text_boxes_layout)

        forge_mode.setLayout(forge_layout)

        return forge_mode

    def create_replace_tab(self):
        # Replace content with
        self.replace_text_edit = QTextEdit()
        # Add Ctrl+Delete shortcut to clear content
        self.replace_text_edit.setToolTip("Use Ctrl+Delete to clear content")
        self.replace_text_edit.keyPressEvent = lambda event: self.handle_clear_shortcut(event, self.replace_text_edit)
        
        # Add clear button for replace text
        self.replace_clear_button = QPushButton()
        self.set_button_icon(self.replace_clear_button, 'clear_text.png')
        self.replace_clear_button.clicked.connect(lambda: self.clear_text_edit(self.replace_text_edit))
        self.replace_clear_button.setToolTip("Clear replace content")
        self.replace_clear_button.setEnabled(False)
        self.replace_text_edit.textChanged.connect(lambda: self.update_clear_button_state(self.replace_text_edit, self.replace_clear_button))
        
        # Apply button
        apply_button = QPushButton("Apply Content Replacements")
        apply_button.clicked.connect(self.confirm_and_apply_replacement)

        # Layout for Replace Tab
        replace_layout = QVBoxLayout()
        replace_header_layout = QHBoxLayout()
        replace_header_layout.addWidget(QLabel("Replace content with"))
        replace_header_layout.addWidget(self.replace_clear_button)
        replace_header_layout.setAlignment(self.replace_clear_button, Qt.AlignRight)
        replace_layout.addLayout(replace_header_layout)
        replace_layout.addWidget(self.replace_text_edit)
        replace_layout.addWidget(apply_button)

        replace_widget = QWidget()
        replace_widget.setLayout(replace_layout)
        return replace_widget

    def create_config_tab(self):
        # Select field
        self.section_field = QComboBox()
        self.section_field.addItems([])

        # Checkbox
        self.add_at_start_checkbox = QCheckBox("Add at section start")

        # Multiline text edit
        self.config_text_edit = QTextEdit()
        self.config_text_edit.setPlaceholderText("Enter configuration lines here...")
        # Add Ctrl+Delete shortcut to clear content
        self.config_text_edit.setToolTip("Use Ctrl+Delete to clear content")
        self.config_text_edit.keyPressEvent = lambda event: self.handle_clear_shortcut(event, self.config_text_edit)

        # Add clear button for config text
        self.config_clear_button = QPushButton()
        self.set_button_icon(self.config_clear_button, 'clear_text.png')
        self.config_clear_button.clicked.connect(lambda: self.clear_text_edit(self.config_text_edit))
        self.config_clear_button.setToolTip("Clear configuration content")
        self.config_clear_button.setEnabled(False)
        self.config_text_edit.textChanged.connect(lambda: self.update_clear_button_state(self.config_text_edit, self.config_clear_button))

        # Add configuration button
        add_config_button = QPushButton("Add Configuration")
        add_config_button.clicked.connect(self.confirm_and_add_configuration)

        # Layout for Config Tab
        section_layout = QHBoxLayout()
        section_layout.addWidget(QLabel("Select Section"))
        section_layout.addWidget(self.section_field)
        section_layout.addWidget(self.add_at_start_checkbox)
        config_layout = QVBoxLayout()
        config_layout.addLayout(section_layout)
        config_header_layout = QHBoxLayout()
        config_header_layout.addWidget(QLabel("Configuration Lines"))
        config_header_layout.addWidget(self.config_clear_button)
        config_header_layout.setAlignment(self.config_clear_button, Qt.AlignRight)
        config_layout.addLayout(config_header_layout)
        config_layout.addWidget(self.config_text_edit)
        config_layout.addWidget(add_config_button)

        config_widget = QWidget()
        config_widget.setLayout(config_layout)
        return config_widget
    
    def create_remove_tab(self):
        # Remove configuration button
        remove_config_button = QPushButton("Remove Configuration")
        remove_config_button.clicked.connect(self.confirm_and_remove_configuration)

        # Layout for Remove Tab
        remove_layout = QVBoxLayout()
        remove_textedit = QLabel("Configuration Removal, Please use this option with caution.")
        remove_textedit.setAlignment(Qt.AlignTop)
        
        remove_layout.addWidget(remove_textedit)
        remove_layout.addWidget(remove_config_button)

        remove_widget = QWidget()
        remove_widget.setLayout(remove_layout)
        return remove_widget
    
    def create_file_viewer_mode(self):
        file_viewer_mode = QWidget()
        file_viewer_layout = QVBoxLayout()

        self.splitter_file_viewer = QSplitter(Qt.Horizontal)

        # Set monospace font for both QTextEdit widgets
        monospace_font = QFont("Courier New", 10)
        
        # Set consistent line height (adjust to match font size)
        font_metrics = QFontMetrics(monospace_font)
        line_height = font_metrics.height()
        block_format = QTextBlockFormat()
        block_format.setLineHeight(line_height, QTextBlockFormat.FixedHeight)

        self.line_numbers_text_edit = QPlainTextEdit()
        self.line_numbers_text_edit.setReadOnly(True)
        self.line_numbers_text_edit.setFixedWidth(40)
        self.line_numbers_text_edit.setFont(monospace_font)
        self.line_numbers_text_edit.setWordWrapMode(QTextOption.NoWrap) # Disable word wrapping to avoid line break differences
        self.line_numbers_text_edit.document().setDocumentMargin(0) # Set consistent document margins
        text_format = self.line_numbers_text_edit.textCursor().blockFormat() # Set the same line spacing (leading)
        text_format.setLineHeight(100, QTextBlockFormat.FixedHeight)  # 100% of the font size
        self.line_numbers_text_edit.textCursor().setBlockFormat(text_format)
        self.line_numbers_text_edit.setStyleSheet("background-color: ivory;")

        self.file_content_text_edit = QTextEdit()
        self.file_content_text_edit.setFont(monospace_font)
        self.file_content_text_edit.setWordWrapMode(QTextOption.NoWrap) # Disable word wrapping to avoid line break differences
        self.file_content_text_edit.document().setDocumentMargin(0) # Set consistent document margins
        self.file_content_text_edit.textCursor().setBlockFormat(text_format) # Set the same line spacing (leading)
        # self.file_content_text_edit.setReadOnly(True)
        
        self.line_numbers_text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        file_content_scrollbar = self.file_content_text_edit.verticalScrollBar()
        # Connect the scrollbar's valueChanged signal to scroll both QTextEdit widgets
        file_content_scrollbar.valueChanged.connect(self.sync_scroll)
        self.line_numbers_text_edit.verticalScrollBar().valueChanged.connect(lambda value: self.sync_scroll(value, numsscroll=True))
        
        self.set_line_height(self.line_numbers_text_edit, block_format)
        self.set_line_height(self.file_content_text_edit, block_format)

        # Set consistent document margins and padding
        self.line_numbers_text_edit.setContentsMargins(0, 0, 0, 0)
        self.file_content_text_edit.setContentsMargins(0, 0, 0, 0)

        editor_menubar_layout = QHBoxLayout()
        search_label = QLabel("Editor Search")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search query")
        self.search_input.setToolTip("Search for text in the current file\n(Press Enter to search, use navigation buttons to jump between matches)")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.returnPressed.connect(self.search_text)  # Enter key to searchself.search_button = QPushButton("Search")
        self.search_button = QPushButton()
        self.set_button_icon(self.search_button, 'search.png')
        self.search_button.setToolTip("Search")
        self.search_button.clicked.connect(self.search_text)
        self.case_sensitive_button = QPushButton()
        self.case_sensitive_button.setCheckable(True)
        self.set_button_icon(self.case_sensitive_button, 'cs.png')
        self.case_sensitive_button.setToolTip("Toggle Case Sensitive Search")
        self.clear_search_button = QPushButton()
        self.set_button_icon(self.clear_search_button, 'clear.png')
        self.clear_search_button.clicked.connect(self.clear_highlights)
        self.clear_search_button.setToolTip("Clear search highlights")
        
        # Navigation buttons for search matches
        self.prev_match_button = QPushButton("◀")
        self.prev_match_button.clicked.connect(self.go_to_previous_match)
        self.prev_match_button.setToolTip("Go to previous match")
        self.prev_match_button.setEnabled(False)
        self.prev_match_button.setFixedWidth(30)
        
        self.next_match_button = QPushButton("▶")
        self.next_match_button.clicked.connect(self.go_to_next_match)
        self.next_match_button.setToolTip("Go to next match")
        self.next_match_button.setEnabled(False)
        self.next_match_button.setFixedWidth(30)
        
        self.match_info_label = QLabel("")
        self.match_info_label.setFixedWidth(80)
        
        
        # Initialize search match tracking
        self.search_matches = []
        self.current_match_index = -1
        self.save_button = QPushButton()
        self.set_button_icon(self.save_button, 'save.png')
        self.save_button.setToolTip("Save changes made on file editor")
        self.save_button.clicked.connect(self.save_changes)
        self.save_button.setEnabled(False)
        editor_menubar_layout.addWidget(search_label)
        editor_menubar_layout.addWidget(self.search_input)
        editor_menubar_layout.addWidget(self.search_button)
        editor_menubar_layout.addWidget(self.case_sensitive_button)
        editor_menubar_layout.addWidget(self.clear_search_button)
        editor_menubar_layout.addWidget(self.prev_match_button)
        editor_menubar_layout.addWidget(self.next_match_button)
        editor_menubar_layout.addWidget(self.match_info_label)
        editor_menubar_layout.addWidget(self.save_button, alignment=Qt.AlignRight)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_layout = QHBoxLayout()
        content_layout.addWidget(self.line_numbers_text_edit)
        content_layout.addWidget(self.file_content_text_edit)

        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)

        self.splitter_file_viewer.addWidget(scroll_area)

        file_viewer_layout.addLayout(editor_menubar_layout)
        file_viewer_layout.addWidget(self.splitter_file_viewer)
        file_viewer_mode.setLayout(file_viewer_layout)

        return file_viewer_mode

    def search_text(self):
        query = self.search_input.text()
        case_sensitive = self.case_sensitive_button.isChecked()

        # Implement search and highlight
        if query:
            self.highlight_search_results(query, case_sensitive)

    def highlight_search_results(self, query, case_sensitive):
        # Clear previous highlights first
        self.clear_highlights()
        
        # Reset search matches - they're already cleared in clear_highlights()
        # but reset here for safety
        self.search_matches = []
        self.current_match_index = -1
        
        cursor = self.file_content_text_edit.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        # Use find with case-sensitivity option
        flags = QTextDocument.FindFlags()
        if case_sensitive:  # Fixed: was backwards
            flags |= QTextDocument.FindCaseSensitively

        # Search for the query in the document with limit to prevent freezing
        match_count = 0
        max_matches = 1000  # Prevent too many highlights from freezing the app
        first_match_cursor = None
        
        while match_count < max_matches:
            found_cursor = self.file_content_text_edit.document().find(query, cursor, flags)
            if found_cursor.isNull():
                break
            
            # Store the first match to navigate to it later
            if match_count == 0:
                first_match_cursor = QTextCursor(found_cursor)
                
            # Store match position for navigation
            match_cursor = QTextCursor(found_cursor)  # Create a copy
            self.search_matches.append({
                'start': found_cursor.selectionStart(),
                'end': found_cursor.selectionEnd(),
                'cursor': match_cursor
            })
                
            # Highlight the found text - make sure selection is correct
            if found_cursor.hasSelection():
                found_cursor.mergeCharFormat(self.get_highlight_format())
            
            # Move cursor past the found text to avoid infinite loop
            cursor = found_cursor
            cursor.movePosition(QTextCursor.NextCharacter)
            match_count += 1
            
        # Update match info and navigation buttons
        if match_count > 0:
            self.current_match_index = 0
            self.update_match_info()
            self.enable_navigation_buttons(True)
            
            # Navigate to first match
            if first_match_cursor:
                self.file_content_text_edit.setTextCursor(first_match_cursor)
                self.file_content_text_edit.ensureCursorVisible()
        else:
            self.match_info_label.setText("No matches")
            self.enable_navigation_buttons(False)
            
        if match_count >= max_matches:
            QMessageBox.information(self, "Search Results", f"Search limited to first {max_matches} matches to prevent performance issues.")
    
    def clear_highlights(self):
        # Clear all highlights by resetting the entire document formatting
        if self.search_matches:
            # Store current cursor position
            current_cursor = self.file_content_text_edit.textCursor()
            current_position = current_cursor.position()
            
            # Select all text and clear formatting
            cursor = self.file_content_text_edit.textCursor()
            cursor.select(QTextCursor.Document)
            
            # Create a clean format and apply it
            clean_format = QTextCharFormat()
            clean_format.setBackground(Qt.transparent)
            cursor.setCharFormat(clean_format)
            
            # Clear selection and restore cursor position
            cursor.clearSelection()
            cursor.setPosition(min(current_position, len(self.file_content_text_edit.toPlainText())))
            self.file_content_text_edit.setTextCursor(cursor)
        
        # Clear search matches and update UI
        self.search_matches = []
        self.current_match_index = -1
        self.match_info_label.setText("")
        self.enable_navigation_buttons(False)
    
    def update_match_info(self):
        if self.search_matches:
            total_matches = len(self.search_matches)
            current_pos = self.current_match_index + 1
            self.match_info_label.setText(f"{current_pos}/{total_matches}")
        else:
            self.match_info_label.setText("")
    
    def enable_navigation_buttons(self, enabled):
        self.prev_match_button.setEnabled(enabled)
        self.next_match_button.setEnabled(enabled)
    
    def go_to_previous_match(self):
        if not self.search_matches:
            return
            
        self.current_match_index = (self.current_match_index - 1) % len(self.search_matches)
        self.navigate_to_current_match()
    
    def go_to_next_match(self):
        if not self.search_matches:
            return
            
        self.current_match_index = (self.current_match_index + 1) % len(self.search_matches)
        self.navigate_to_current_match()
    
    def navigate_to_current_match(self):
        if 0 <= self.current_match_index < len(self.search_matches):
            match = self.search_matches[self.current_match_index]
            cursor = QTextCursor(match['cursor'])
            self.file_content_text_edit.setTextCursor(cursor)
            self.file_content_text_edit.ensureCursorVisible()
            self.update_match_info()

    def get_highlight_format(self):
        format = QTextCharFormat()
        format.setBackground(Qt.yellow)  # Set highlight color to yellow
        # Ensure we don't affect other formatting
        format.setForeground(Qt.black)  # Ensure text remains readable
        return format

    def update_save_button_position(self, event):
        # Adjust button's position to the top-right of the textedit widget
        self.save_button.move(self.file_content_text_edit.width() - self.save_button.width() - 6, 6)
    
    def sync_scroll(self, value, numsscroll=False):
        # Calculate the scroll ratio of the right QTextEdit
        max_scroll_right = self.file_content_text_edit.verticalScrollBar().maximum()
        max_scroll_left = self.line_numbers_text_edit.verticalScrollBar().maximum()

        if numsscroll and max_scroll_left > 0:
            # Calculate the corresponding value for the right QTextEdit
            scroll_ratio = value / max_scroll_left
            right_value = round(scroll_ratio * max_scroll_right)
            self.file_content_text_edit.verticalScrollBar().setValue(right_value)

        elif max_scroll_right > 0:
            # Calculate the corresponding value for the left QTextEdit
            scroll_ratio = value / max_scroll_right
            left_value = round(scroll_ratio * max_scroll_left)
            self.line_numbers_text_edit.verticalScrollBar().setValue(left_value)

    def save_changes(self):
        prs_content = self.file_content_text_edit.toPlainText()
        if self.selected_file:
            with open(self.selected_file, 'w+') as file:
                file.write(prs_content)
                self.save_button.setEnabled(False)
        
    def set_line_height(self, text_edit, block_format):
        cursor = text_edit.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.mergeBlockFormat(block_format)
        cursor.clearSelection()
        text_edit.setTextCursor(cursor)
        
    def display_file_content(self, item):
        self.file_selected = True
        self.selected_file = item.data(Qt.UserRole)
        with open(self.selected_file, 'r') as file:
            content = file.read()

        lines = content.splitlines()
        line_numbers = "\n".join(str(i + 1).zfill(4) for i in range(len(lines)+1))  # Start from 1, with leading zeros
        formatted_lines = "\n".join(self.format_line(line) for line in lines)
        
        self.line_numbers_text_edit.setPlainText(line_numbers)
        self.file_content_text_edit.setPlainText(formatted_lines)

        # Ensure both editors are scrolled to the top when content is loaded
        self.file_content_text_edit.verticalScrollBar().setValue(0)
        self.line_numbers_text_edit.verticalScrollBar().setValue(0)

        # Enable save button on editor content change
        self.file_content_text_edit.textChanged.connect(lambda: self.save_button.setEnabled(True))
        self.save_button.setEnabled(False)

    def reload_files(self, folder_path):
        self.save_button.setEnabled(False)
        if folder_path and os.path.isdir(folder_path):
            self.working_dir_line_edit.setText(folder_path)
            self.settings.setValue(f"{self.user}/working_directory", folder_path)
            self.load_files()

    def paste_directory(self):
        clipboard = QApplication.clipboard()
        folder_path = clipboard.text()
        self.reload_files(folder_path)

    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Working Directory")
        self.reload_files(folder_path)

    def open_meld(self):
        folder_path = self.working_dir_line_edit.text()
        if os.path.isdir(folder_path) and self.meld_available:
            self.meld_thread = Meld(self.meld_path, folder_path)
            self.meld_thread.start()

    def toggle_theme(self, state):
        text_editors = [self.file_content_text_edit, self.working_dir_line_edit, 
                        self.file_list_widget, self.filter_text_edit, self.replace_text_edit]
        if state: # dark theme
            self.setStyleSheet("QWidget { background-color: #2e2e2e; color: #ffffff; }")
            self.line_numbers_text_edit.setStyleSheet("background-color: dimgray;")
            for txtedit in text_editors: 
                txtedit.setStyleSheet("background-color: slategray;")
            return
        self.setStyleSheet("")  # Reset to default (bright theme)
        self.line_numbers_text_edit.setStyleSheet("background-color: ivory;")
        for txtedit in text_editors: 
            txtedit.setStyleSheet("")

    def copy_files_list(self):
        list_of_files = ""
        files_list = [self.file_list_widget.item(i).text() for i in range(self.file_list_widget.count())]
        for filename in files_list:
            list_of_files += f"{filename}\n"
        if list_of_files:
            pyperclip.copy(list_of_files)
    
    def load_files(self):
        folder_path = self.working_dir_line_edit.text()
        self.file_list_widget.clear()
        if os.path.isdir(folder_path):
            self.log.info(f"Reading folder content: {folder_path}")
            try:
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        if any(file.lower().endswith(f'.{ext}') for ext in self.extensions):
                            file_path = os.path.join(root, file)
                            self.add_file_to_list_widget(file_path)

            except Exception as e:
                print(f"Error loading files: {e}")
        self.filter_files()
        self.update_sections()
        
    def update_sections(self):
        self.section_field.clear()
        self.section_field.addItems(self.getConfigSections())
    
    def start_filter_timer(self):
        if self.filter_timer.isActive():
            self.filter_timer.stop()
        self.filter_timer.start(1000)

    def show_filtering_popup(self):
        self.filter_dialog = QDialog(self)
        self.filter_dialog.setWindowTitle("Initializing")
        self.filter_dialog.setModal(True)
        
        layout = QVBoxLayout()
        self.filter_dialog.setLayout(layout)

        self.filter_progress_label = QLabel("Processing configuration files, please wait...")
        layout.addWidget(self.filter_progress_label)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.cancel_filtering)
        layout.addWidget(cancel_button)

        self.filter_dialog.show()
        QApplication.processEvents()

    def cancel_filtering(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.cancel()
        self.filter_dialog.close()

    def filter_files(self):
        self.filter_timer.stop()
        file_filter_text = self.file_filter_line_edit.text()
        filter_content_text = self.filter_text_edit.toPlainText()  # Full content with blank lines
        include_blank = self.include_blank_lines_checkbox.isChecked()
        filter_lines = filter_content_text.splitlines() if filter_content_text else []
        regex_mode = self.regex_toggle_button.isChecked()
        regexpr = self.regex_expression.text() if regex_mode else None
        folder_path = self.working_dir_line_edit.text()

        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait()

        self.show_filtering_popup()

        self.worker = FileFilterWorker(folder_path, file_filter_text, filter_content_text, filter_lines, regexpr, self.extensions, regex_mode, include_blank)
        self.worker.signal.connect(self.update_file_list)
        self.worker.start()
        
    def getConfigSections(self):
        folder = self.working_dir_line_edit.text()
        return core.get_config_sections(folder, self.extensions)
    
    def update_file_list(self, filtered_files):
        self.save_button.setEnabled(False)
        self.file_list_widget.clear()
        for file_path in filtered_files:
            item = QListWidgetItem(os.path.basename(file_path))
            item.setData(Qt.UserRole, file_path)
            self.file_list_widget.addItem(item)

        # Update filtered file count label
        self.filtered_file_count_label.setText(f"Filtered files: {len(filtered_files)}")

        self.filter_dialog.close()  # Close the popup after filtering is complete

    def confirm_and_remove_configuration(self):
        filter_text = self.filter_text_edit.toPlainText()
        message = (f"<p>Are you sure you want to remove the following configuration?</p>"
                   f"<p><b>Configuration to remove:</b> {filter_text.strip()}</p>")
        
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.apply_removal()

    def confirm_and_add_configuration(self):
        section = self.section_field.currentText()
        configuration = self.config_text_edit.toPlainText()

        if not section or not configuration:
            QMessageBox.warning(self, "Warning", "Both 'Section' and 'Configuration' must be filled.")
            return

        message = (f"<p>Are you sure you want to add the following content?</p>"
                   f"<p><b>On section:</b> {section.strip()}</p>"
                   f"<p><b>Add content:</b><br><pre>{configuration}</pre></p>")

        reply = QMessageBox.question(
            self,
            "Confirm New Insertion",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.apply_insertion()

    def confirm_and_apply_replacement(self):
        filter_text = self.filter_text_edit.toPlainText()
        replace_text = self.replace_text_edit.toPlainText()

        if not filter_text or not replace_text:
            QMessageBox.warning(self, "Warning", "Both 'Filter by content' and 'Replace content with' must be filled.")
            return

        message = (f"<p>Are you sure you want to replace the following content?</p>"
                   f"<p><b>Filter by content:</b><br><pre>{filter_text}</pre></p>"
                   f"<p><b>Replace content with:</b><br><pre>{replace_text}</pre></p>")

        reply = QMessageBox.question(
            self,
            "Confirm Replacement",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.apply_replacement()

    def apply_insertion(self):
        section = self.section_field.currentText()
        configuration = self.config_text_edit.toPlainText()
        config_lines = configuration.splitlines()
        config_lines = [l for l in config_lines if l.strip()]

        if not config_lines or not section:
            return
        
        # Add newline to each line if not present
        config_lines = [f"{line}\n" if not line.endswith("\n") else line for line in config_lines]
        add_at_start = self.add_at_start_checkbox.isChecked()
        
        for index in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(index)
            file_path = item.data(Qt.UserRole)
            core.process_insertion(file_path, section, config_lines, add_at_start)

    def apply_replacement(self):
        filter_text = self.filter_text_edit.toPlainText()
        replace_text = self.replace_text_edit.toPlainText()
        include_blank = self.include_blank_lines_checkbox.isChecked()

        if not filter_text:
            return

        for index in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(index)
            file_path = item.data(Qt.UserRole)
            core.process_replacement(file_path, filter_text, replace_text, include_blank)

    def apply_removal(self):
        filter_text = self.filter_text_edit.toPlainText()
        include_blank = self.include_blank_lines_checkbox.isChecked()
        
        if not filter_text:
            return

        for index in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(index)
            file_path = item.data(Qt.UserRole)
            core.process_removal(file_path, filter_text, include_blank)

    def open_file_in_meld(self, item):
        if not self.meld_available:
            return
        file_path = item.data(Qt.UserRole)
        self.meld_thread = Meld(self.meld_path, file_path)
        self.meld_thread.start()

    def format_line(self, line):
        if '=' in line:
            key, value = line.split('=', 1)
            return f'{key}={value}'
        else:
            return line

    def add_file_to_list_widget(self, file_path):
        item = QListWidgetItem(os.path.basename(file_path))
        item.setData(Qt.UserRole, file_path)
        self.file_list_widget.addItem(item)

    def toggle_regex_mode(self):
        self.start_filter_timer() # Re-trigger filtering with new regex mode
        self.regex_expression.setEnabled(not self.regex_expression.isEnabled())

def main():
    app = QApplication([])
    app.setApplicationName("iniForge")
    app.setOrganizationName("Arik Levi - Software Solutions, LLC")
    
    # Set application icon for taskbar
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = GUI()
    window.show()
    app.exec()
