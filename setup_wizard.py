#!/usr/bin/env python3
"""
First-run setup wizard for Spotify Playlist Downloader
"""

import os
import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFileDialog, QMessageBox, QCheckBox, QTextEdit
)
from PyQt5.QtCore import Qt

class SetupWizard(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spotify Playlist Downloader - First Time Setup")
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
                font-size: 11pt;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
            QPushButton#primary {
                background-color: #1db954;
                color: white;
                font-weight: bold;
            }
            QPushButton#primary:hover {
                background-color: #1ed760;
            }
        """)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Welcome to Spotify Playlist Downloader")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("""
Please provide the following information to get started:
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Spotify credentials
        spotify_group = QVBoxLayout()
        spotify_group.addWidget(QLabel("Spotify API Credentials:"))
        spotify_group.addWidget(QLabel("Get these from: https://developer.spotify.com/dashboard/applications"))
        
        # Client ID
        client_id_layout = QHBoxLayout()
        client_id_layout.addWidget(QLabel("Client ID:"))
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("Enter your Spotify Client ID")
        client_id_layout.addWidget(self.client_id_input)
        spotify_group.addLayout(client_id_layout)
        
        # Client Secret
        client_secret_layout = QHBoxLayout()
        client_secret_layout.addWidget(QLabel("Client Secret:"))
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setEchoMode(QLineEdit.Password)
        self.client_secret_input.setPlaceholderText("Enter your Spotify Client Secret")
        client_secret_layout.addWidget(self.client_secret_input)
        spotify_group.addLayout(client_secret_layout)
        
        layout.addLayout(spotify_group)
        
        # Download directory
        download_group = QVBoxLayout()
        download_group.addWidget(QLabel("Download Directory:"))
        
        download_layout = QHBoxLayout()
        self.download_dir_input = QLineEdit()
        self.download_dir_input.setText(str(Path.home() / "Downloads" / "Spotify"))
        self.download_dir_input.setPlaceholderText("Choose where to save downloaded files")
        download_layout.addWidget(self.download_dir_input)
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_directory)
        download_layout.addWidget(browse_button)
        download_group.addLayout(download_layout)
        
        layout.addLayout(download_group)
        
        # Options
        options_group = QVBoxLayout()
        self.create_demo_checkbox = QCheckBox("Create demo playlist for testing")
        self.create_demo_checkbox.setChecked(True)
        options_group.addWidget(self.create_demo_checkbox)
        
        self.auto_open_folder = QCheckBox("Open download folder when complete")
        self.auto_open_folder.setChecked(True)
        options_group.addWidget(self.auto_open_folder)
        
        layout.addLayout(options_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        skip_button = QPushButton("Skip Setup")
        skip_button.clicked.connect(self.skip_setup)
        button_layout.addWidget(skip_button)
        
        save_button = QPushButton("Save & Continue")
        save_button.setObjectName("primary")
        save_button.clicked.connect(self.save_setup)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if directory:
            self.download_dir_input.setText(directory)
            
    def skip_setup(self):
        self.reject()
        
    def save_setup(self):
        # Validate inputs
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()
        download_dir = self.download_dir_input.text().strip()
        
        if not client_id or not client_secret:
            QMessageBox.warning(self, "Missing Information", 
                              "Please enter both Client ID and Client Secret.")
            return
            
        if not download_dir:
            QMessageBox.warning(self, "Missing Information", 
                              "Please select a download directory.")
            return
        
        # Create .env file
        env_content = f"""# Spotify API Credentials
SPOTIFY_CLIENT_ID={client_id}
SPOTIFY_CLIENT_SECRET={client_secret}

# Default download directory
DEFAULT_DOWNLOAD_DIR={download_dir}
"""
        
        try:
            with open('.env', 'w') as f:
                f.write(env_content)
            
            # Create download directory
            Path(download_dir).mkdir(parents=True, exist_ok=True)
            
            # Create demo playlist if requested
            if self.create_demo_checkbox.isChecked():
                demo_dir = Path(download_dir) / "demo"
                demo_dir.mkdir(exist_ok=True)
                
                # Create a simple demo playlist file
                demo_content = """# Demo Playlist
This folder contains demo tracks for testing the downloader.

To use demo mode:
1. Check "Use demo playlist" in the main app
2. Click "Start Download"
3. The app will download 2 sample tracks
"""
                with open(demo_dir / "README.txt", 'w') as f:
                    f.write(demo_content)
            
            QMessageBox.information(self, "Setup Complete", 
                                  f"Configuration saved successfully!\n\n"
                                  f"Download directory: {download_dir}\n"
                                  f"Demo mode: {'Enabled' if self.create_demo_checkbox.isChecked() else 'Disabled'}")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Setup Error", 
                               f"Failed to save configuration: {e}")

def check_first_run():
    """Check if this is the first run and show setup wizard if needed"""
    env_file = Path('.env')
    if not env_file.exists():
        return True
    
    # Check if .env file has the required data
    try:
        with open(env_file, 'r') as f:
            content = f.read()
            
        # Check for required Spotify credentials
        has_client_id = 'SPOTIFY_CLIENT_ID=' in content and 'your_client_id_here' not in content
        has_client_secret = 'SPOTIFY_CLIENT_SECRET=' in content and 'your_client_secret_here' not in content
        
        # If either credential is missing or still has placeholder values, show setup
        if not has_client_id or not has_client_secret:
            return True
            
    except Exception:
        # If we can't read the file, show setup
        return True
    
    return False

def run_setup_wizard():
    """Run the setup wizard"""
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    wizard = SetupWizard()
    result = wizard.exec_()
    
    # If user cancelled, ask if they want to exit
    if result != QDialog.Accepted:
        reply = QMessageBox.question(wizard, "Exit Setup", 
                                    "Setup was cancelled. Do you want to exit the application?",
                                    QMessageBox.Yes | QMessageBox.No, 
                                    QMessageBox.No)
        if reply == QMessageBox.Yes:
            return False
        else:
            # User chose to continue without setup
            return True
    
    return True

if __name__ == "__main__":
    run_setup_wizard()
