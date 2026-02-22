from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox
)

class QExtensionsDialog(QDialog):
    """Dialog for configuring file extensions."""
    
    def __init__(self, parent=None, current_extensions=None, settings=None):
        super().__init__(parent)
        self.current_extensions = current_extensions or ["ini"]
        self.new_extensions = None
        self.settings = settings
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("iniForge Settings")
        self.setModal(True)
        
        main_layout = QVBoxLayout()
        
        tooltip = "Enter extensions without dots, separated by commas or space\nExample: ini, prs, cfg"
        
        # File Extensions field with label
        extensions_layout = QHBoxLayout()
        extensions_label = QLabel("File Extensions")
        extensions_label.setToolTip(tooltip)
        
        self.extensions_input = QLineEdit()
        self.extensions_input.setText(",".join(self.current_extensions))
        self.extensions_input.setClearButtonEnabled(True)
        self.extensions_input.setPlaceholderText("ini,prs,cfg")
        self.extensions_input.setToolTip(tooltip)
        self.extensions_input.textChanged.connect(self.on_input_changed)
        
        extensions_layout.addWidget(extensions_label)
        extensions_layout.addWidget(self.extensions_input)
        main_layout.addLayout(extensions_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Configuration")
        cancel_button = QPushButton("Cancel")
        
        self.save_button.clicked.connect(self.save_extensions)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.save_button)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # Check initial state
        self.on_input_changed()
    
    def on_input_changed(self):
        """Disable save button if input is empty or spaces-only."""
        ext_text = self.extensions_input.text().strip()
        self.save_button.setEnabled(bool(ext_text))
    
    def save_extensions(self):
        """Validate and save extensions."""
        ext_text = self.extensions_input.text().strip()
        if ext_text:
            # Parse extensions
            new_extensions = [ext.strip() for ext in ext_text.split(',') if ext.strip()]
            if new_extensions:
                self.new_extensions = new_extensions
                # Save to config.ini if settings object is provided
                if self.settings:
                    self.settings.setValue("Base/filtered_extensions", ",".join(new_extensions))
                self.accept()
            else:
                QMessageBox.warning(self, "Invalid Input", "Please enter at least one extension.")
        else:
            QMessageBox.warning(self, "Invalid Input", "Extensions field cannot be empty.")
    
    def get_extensions(self):
        """Return the new extensions list."""
        return self.new_extensions
