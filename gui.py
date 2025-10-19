import os
import threading
import subprocess
import sys  # <-- Add this import
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTextEdit,
    QLabel, QFileDialog, QCheckBox, QSlider
)
from PyQt5.QtCore import Qt
from downloader import process_demo_playlist, process_spotify_playlist, signals
from config import DEFAULT_DOWNLOAD_DIR

class DownloaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spotify to MP3 Downloader")
        self.setGeometry(300, 200, 700, 500)
        self.setStyleSheet(self.style_sheet())
        
        self.download_dir = DEFAULT_DOWNLOAD_DIR
        self.quality = "320"  # Default quality

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Input frame
        input_frame = QWidget()
        input_frame_layout = QVBoxLayout()
        input_frame_layout.setSpacing(15)
        
        # Playlist input
        input_frame_layout.addWidget(QLabel("Spotify Playlist URL:"))
        self.url_input = QLineEdit()
        self.url_input.setFixedHeight(35)
        
        # Demo mode checkbox
        self.demo_checkbox = QCheckBox("Use demo playlist (testing only)")
        self.demo_checkbox.setChecked(False)
        
        # Quality selector
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Audio Quality:"))
        
        # Replace dropdown with slider
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(128)
        self.quality_slider.setMaximum(320)
        self.quality_slider.setValue(320)
        self.quality_slider.setTickInterval(64)  # Show ticks at 128, 192, 256, 320
        self.quality_slider.setSingleStep(64)
        self.quality_slider.setPageStep(64)
        self.quality_slider.valueChanged.connect(self.update_quality)
        
        self.quality_label = QLabel("320 kbps")
        
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_label)
        
        input_frame_layout.addWidget(self.url_input)
        input_frame_layout.addLayout(quality_layout)
        input_frame_layout.addWidget(self.demo_checkbox)
        input_frame.setLayout(input_frame_layout)
        
        main_layout.addWidget(input_frame)

        # Folder selector
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Download Folder:"))
        self.folder_path_display = QLineEdit(self.download_dir)
        self.folder_path_display.setFixedHeight(35)
        self.folder_button = QPushButton("Browse")
        self.folder_button.setFixedHeight(40)
        self.folder_button.clicked.connect(self.choose_folder)
        # Add open folder button
        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.setFixedHeight(40)
        self.open_folder_button.clicked.connect(self.open_download_folder)
        folder_layout.addWidget(self.folder_path_display)
        folder_layout.addWidget(self.folder_button)
        folder_layout.addWidget(self.open_folder_button)
        main_layout.addLayout(folder_layout)

        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.start_button = QPushButton("Start Download")
        self.start_button.setFixedHeight(40)
        self.start_button.clicked.connect(self.start_download)
        self.clear_button = QPushButton("Clear Log")
        self.clear_button.setFixedHeight(40)
        self.clear_button.clicked.connect(self.clear_log)
        # Add export log button
        self.export_log_button = QPushButton("Export Log")
        self.export_log_button.setFixedHeight(40)
        self.export_log_button.clicked.connect(self.export_log)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.export_log_button)
        
        main_layout.addLayout(button_layout)

        # Log frame
        log_frame = QWidget()
        log_frame_layout = QVBoxLayout()
        log_frame_layout.setContentsMargins(0, 0, 0, 0)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_frame_layout.addWidget(self.log_output)
        log_frame.setLayout(log_frame_layout)
        
        main_layout.addWidget(log_frame)

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

    def on_done(self):
        self.start_button.setEnabled(True)
        self.append_log("Download complete!")

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

        if self.demo_checkbox.isChecked():
            thread = threading.Thread(target=process_demo_playlist, args=(self.quality, self.download_dir))
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

            thread = threading.Thread(target=process_spotify_playlist, args=(playlist_url, self.quality, self.download_dir))

        thread.daemon = True  # Make thread daemon so it closes with the app
        thread.start()

    def open_download_folder(self):
        folder = self.folder_path_display.text()
        if os.path.exists(folder):
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        else:
            self.append_log("❗ Download folder does not exist.")

    def export_log(self):
        log_text = self.log_output.toPlainText()
        if not log_text.strip():
            self.append_log("❗ Log is empty, nothing to export.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Log", "download_log.txt", "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(log_text)
                self.append_log(f"✅ Log exported to {file_path}")
            except Exception as e:
                self.append_log(f"❌ Failed to export log: {e}")