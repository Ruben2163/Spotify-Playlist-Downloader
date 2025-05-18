import os
import threading
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTextEdit,
    QLabel, QFileDialog, QCheckBox, QComboBox
)
from downloader import process_demo_playlist, process_spotify_playlist, signals
from config import DEFAULT_DOWNLOAD_DIR

class DownloaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spotify to MP3 Downloader")
        self.setGeometry(300, 200, 700, 500)

        self.download_dir = DEFAULT_DOWNLOAD_DIR

        layout = QVBoxLayout()

        # Playlist input
        layout.addWidget(QLabel("Spotify Playlist URL:"))
        self.url_input = QLineEdit()
        layout.addWidget(self.url_input)

        # Demo mode checkbox
        self.demo_checkbox = QCheckBox("Use demo playlist(testing only 20 tracks)")
        self.demo_checkbox.setChecked(False)
        layout.addWidget(self.demo_checkbox)

        # Quality selector
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Audio Quality:"))
        self.quality_dropdown = QComboBox()
        self.quality_dropdown.addItems(["128", "192", "320"])
        self.quality_dropdown.setCurrentText("320")
        quality_layout.addWidget(self.quality_dropdown)
        layout.addLayout(quality_layout)

        # Folder selector
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Download Folder:"))
        self.folder_path_display = QLineEdit(self.download_dir)
        self.folder_button = QPushButton("Browse")
        self.folder_button.clicked.connect(self.choose_folder)
        folder_layout.addWidget(self.folder_path_display)
        folder_layout.addWidget(self.folder_button)
        layout.addLayout(folder_layout)

        # Control buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Download")
        self.start_button.clicked.connect(self.start_download)
        self.clear_button = QPushButton("Clear Log")
        self.clear_button.clicked.connect(self.clear_log)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.clear_button)
        layout.addLayout(button_layout)

        # Log display
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

        # Connect signals
        signals.log_signal.connect(self.append_log)
        signals.done_signal.connect(self.on_done)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.download_dir = folder
            self.folder_path_display.setText(folder)

    def append_log(self, text):
        self.log_output.append(text)

    def clear_log(self):
        self.log_output.clear()

    def on_done(self):
        self.start_button.setEnabled(True)
        self.append_log("Download complete!")

    def start_download(self):
        self.clear_log()
        self.start_button.setEnabled(False)

        # Validate and create download directory
        self.download_dir = self.folder_path_display.text()
        if not os.path.exists(self.download_dir):
            try:
                os.makedirs(self.download_dir)
                self.append_log(f"Created download directory: {self.download_dir}")
            except Exception as e:
                self.append_log(f"❌ Error creating download directory: {e}")
                self.start_button.setEnabled(True)
                return

        playlist_url = self.url_input.text().strip()
        quality = self.quality_dropdown.currentText()

        if self.demo_checkbox.isChecked():
            thread = threading.Thread(target=process_demo_playlist, args=(quality, self.download_dir))
        else:
            # Validate Spotify URL
            if not playlist_url:
                self.append_log("❗ Please enter a Spotify playlist URL.")
                self.start_button.setEnabled(True)
                return
            
            if not ('spotify.com/playlist/' in playlist_url or 'spotify.com/album/' in playlist_url):
                self.append_log("❗ Invalid Spotify URL. Please enter a valid playlist or album URL.")
                self.start_button.setEnabled(True)
                return

            thread = threading.Thread(target=process_spotify_playlist, args=(playlist_url, quality, self.download_dir))

        thread.daemon = True  # Make thread daemon so it closes with the app
        thread.start()
