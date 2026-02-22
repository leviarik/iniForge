from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QScrollArea
from PySide6.QtCore import Qt
import pkg_resources

import_succeded = True
try:
    import iniforge
except:
    import_succeded = False

class QAboutDialog(QDialog):
    def __init__(self, parent=None):
        super(QAboutDialog, self).__init__(parent)
        global import_succeded
        self.setWindowTitle("iniForge About")
        self.leftLabelWidth = 80
        # Define the layout
        layout = QVBoxLayout()
        self.version = pkg_resources.get_distribution("iniforge").version if import_succeded else "Not Available"
        
        # Application name and version
        app_name_label = QLabel(f"<h3>iniForge: Bulk Settings Precision</h3>")
        layout.addWidget(app_name_label)
        
        data_pairs = {
            "Version": self.version,
            "Author" : "Arik Levi"
        }

        for p in data_pairs:
            hbox = QHBoxLayout()
            label = QLabel(p)
            label.setFixedWidth(self.leftLabelWidth)
            value = QLabel(data_pairs[p])
            hbox.addWidget(label)
            hbox.addWidget(value)
            layout.addLayout(hbox)
        
        # Online User Manual Link
        manual_hbox = QHBoxLayout()
        label = QLabel("User Manual")
        label.setFixedWidth(self.leftLabelWidth)
        user_manual_label = QLabel()
        user_manual_label.setText('<a href="https://link_to_online_manual">Online User Manual</a>')
        user_manual_label.setOpenExternalLinks(True)
        manual_hbox.addWidget(label)
        manual_hbox.addWidget(user_manual_label)
        layout.addLayout(manual_hbox)

        # Description
        label = QLabel("Description")
        label.setFixedWidth(self.leftLabelWidth)
        description_text  = "iniForge application offers a rich set of features to ensure"
        description_text += "you have full control and visibility over bulk changes made"
        description_text += "on multiple configuration files, enhancing efficiency and"
        description_text += "productivity in various configration modifications."
        description_label = QLabel(description_text)
        description_label.setWordWrap(True)

        scroll_area = QScrollArea()
        scroll_area.setWidget(description_label)
        scroll_area.setWidgetResizable(True)

        layout.addWidget(label)
        layout.addWidget(scroll_area)

        # Close button
        button_layout = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        # Set the layout for the dialog
        self.setLayout(layout)
        
        # Set fixed size
        self.setFixedSize(450, 230)
