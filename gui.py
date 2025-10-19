import os
import threading
import subprocess
import sys
import platform
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTextEdit,
    QLabel, QFileDialog, QCheckBox, QSlider, QProgressBar, QGroupBox,
    QMessageBox, QSplitter
)
from PyQt5.QtCore import Qt, QTimer
from downloader import process_demo_playlist, process_spotify_playlist, signals
from config import DEFAULT_DOWNLOAD_DIR
from setup_wizard import check_first_run, run_setup_wizard

class DownloaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spotify Playlist Downloader")
        self.setGeometry(300, 200, 700, 500)
        self.setStyleSheet(self.style_sheet())
        
        self.download_dir = DEFAULT_DOWNLOAD_DIR
        self.quality = "320"  # Default quality
        self.is_downloading = False
        
        # Check for first run and show setup wizard
        if check_first_run():
            if not run_setup_wizard():
                sys.exit(0)  # User cancelled setup

        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # URL input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Spotify URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste playlist or album URL here...")
        url_layout.addWidget(self.url_input)
        main_layout.addLayout(url_layout)
        
        # Options row
        options_layout = QHBoxLayout()
        
        # Demo checkbox
        self.demo_checkbox = QCheckBox("Demo mode")
        options_layout.addWidget(self.demo_checkbox)
        
        # Quality selector
        options_layout.addWidget(QLabel("Quality:"))
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(128)
        self.quality_slider.setMaximum(320)
        self.quality_slider.setValue(320)
        self.quality_slider.setTickInterval(64)
        self.quality_slider.setSingleStep(64)
        self.quality_slider.setPageStep(64)
        self.quality_slider.valueChanged.connect(self.update_quality)
        self.quality_slider.setMaximumWidth(150)
        
        self.quality_label = QLabel("320 kbps")
        self.quality_label.setMinimumWidth(80)
        
        options_layout.addWidget(self.quality_slider)
        options_layout.addWidget(self.quality_label)
        options_layout.addStretch()
        
        main_layout.addLayout(options_layout)
        
        # Folder selection
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Save to:"))
        self.folder_path_display = QLineEdit(self.download_dir)
        self.folder_button = QPushButton("Browse")
        self.folder_button.clicked.connect(self.choose_folder)
        folder_layout.addWidget(self.folder_path_display)
        folder_layout.addWidget(self.folder_button)
        main_layout.addLayout(folder_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Download")
        self.start_button.setFixedHeight(40)
        self.start_button.clicked.connect(self.start_download)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #1db954;
                color: white;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #1ed760;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.setFixedHeight(35)
        self.clear_button.clicked.connect(self.clear_log)
        
        self.setup_button = QPushButton("Setup")
        self.setup_button.setFixedHeight(35)
        self.setup_button.clicked.connect(self.run_setup)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.setup_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(200)
        main_layout.addWidget(self.log_output)
        
        self.setLayout(main_layout)

        # Connect signals
        signals.log_signal.connect(self.append_log)
        signals.done_signal.connect(self.on_done)
        
        # Initialize UI
        self.start_button.setEnabled(True)
        self.clear_button.setEnabled(True)

    def style_sheet(self):
        return """
            QWidget {
                background-color: #f5f5f5;
                color: #333;
            }
            
            QLineEdit, QComboBox {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 12pt;
            }
            
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #0078d4;
                outline: none;
            }
            
            QPushButton {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 12pt;
            }
            
            QPushButton:hover {
                background-color: #0078d4;
                color: white;
            }
            
            QPushButton:pressed {
                background-color: #006cbd;
            }
            
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-size: 10pt;
                min-height: 150px;
            }
            
            QLabel {
                font-size: 12pt;
                color: #333;
            }
            
            QCheckBox {
                font-size: 12pt;
                color: #333;
            }
            
            QCheckBox:hover {
                color: #0078d4;
            }
        """

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.download_dir = folder
            self.folder_path_display.setText(folder)

    def append_log(self, text):
        self.log_output.append(text)

    def clear_log(self):
        self.log_output.clear()
    
    def run_setup(self):
        """Run the setup wizard"""
        from setup_wizard import run_setup_wizard
        if run_setup_wizard():
            self.append_log("Setup completed. You may need to restart the application.")
        else:
            self.append_log("Setup cancelled.")

    def on_done(self):
        self.start_button.setEnabled(True)
        self.is_downloading = False
        self.progress_bar.setVisible(False)
        self.append_log("Download complete!")
        
        # Show completion message
        QMessageBox.information(self, "Download Complete", 
                               "All tracks have been downloaded successfully!\n\n"
                               f"Files saved to: {self.download_dir}")

    def update_quality(self, value):
        # Snap to nearest 64 interval (128, 192, 256, 320)
        snapped = min(max(128, round(value / 64) * 64), 320)
        if snapped != value:
            self.quality_slider.blockSignals(True)
            self.quality_slider.setValue(snapped)
            self.quality_slider.blockSignals(False)
        self.quality = str(snapped)
        self.quality_label.setText(f"{snapped} kbps")

    def start_download(self):
        self.clear_log()
        self.start_button.setEnabled(False)
        self.is_downloading = True
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        # Validate and create download directory
        self.download_dir = self.folder_path_display.text()
        if not os.path.exists(self.download_dir):
            try:
                os.makedirs(self.download_dir)
                self.append_log(f"Created download directory: {self.download_dir}")
            except Exception as e:
                self.append_log(f"Error creating download directory: {e}")
                self.start_button.setEnabled(True)
                self.is_downloading = False
                self.progress_bar.setVisible(False)
                return

        playlist_url = self.url_input.text().strip()

        if self.demo_checkbox.isChecked():
            self.append_log("Starting demo download...")
            thread = threading.Thread(target=process_demo_playlist, args=(self.quality, self.download_dir))
        else:
            # Validate Spotify URL
            if not playlist_url:
                self.append_log("Please enter a Spotify playlist URL.")
                self.start_button.setEnabled(True)
                self.is_downloading = False
                self.progress_bar.setVisible(False)
                return
            
            if not ('spotify.com/playlist/' in playlist_url or 'spotify.com/album/' in playlist_url):
                self.append_log("Invalid Spotify URL. Please enter a valid playlist or album URL.")
                self.start_button.setEnabled(True)
                self.is_downloading = False
                self.progress_bar.setVisible(False)
                return

            self.append_log("Starting Spotify download...")
            thread = threading.Thread(target=process_spotify_playlist, args=(playlist_url, self.quality, self.download_dir))

        thread.daemon = True  # Make thread daemon so it closes with the app
        thread.start()
