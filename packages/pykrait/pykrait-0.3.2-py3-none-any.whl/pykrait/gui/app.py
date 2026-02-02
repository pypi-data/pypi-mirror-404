import sys
import os
import warnings
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from pykrait.gui.fileselection import FileSelectionWindow
from pykrait.gui.mainwindow import MainWindow
from pykrait.io.files import get_pykrait_version

def warning_no_source_line(message, category, filename, lineno, file=None, line=None):
    return f"{filename}:{lineno}: {category.__name__}: {message}\n"

class AppController:
    def __init__(self):

        # format warnings to not print the source line every time
        warnings.formatwarning = warning_no_source_line
        
        self.app = QApplication(sys.argv)

        # Loading icon from resources
        appIcon = QIcon()
        try:
            from importlib.resources import files

            icon_path = files("pykrait.gui.resources").joinpath("logo.png")
            os.path.exists(icon_path)
        except Exception:
            icon_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "pykrait/gui/resources",
                    "logo.png",
                )
            )
            os.path.exists(icon_path)
        if os.path.exists(icon_path):
            appIcon.addFile(str(icon_path), QSize(16, 16))
            appIcon.addFile(str(icon_path), QSize(24, 24))
            appIcon.addFile(str(icon_path), QSize(32, 32))
            appIcon.addFile(str(icon_path), QSize(48, 48))
            appIcon.addFile(str(icon_path), QSize(64, 64))
            appIcon.addFile(str(icon_path), QSize(256, 256))
            self.app.setWindowIcon(appIcon)
        else:
            print(f"Warning: Icon file not found at {icon_path}")

        # Set application name and version
        self.app.setApplicationName("pyKrait")
        version = get_pykrait_version()
        if version is not None:
            self.app.setApplicationVersion(version)
        self.file_selection = FileSelectionWindow()
        self.file_selection.analysis_complete.connect(self.on_analysis_complete)
        self.file_selection.show()
        
        #updating the style
        self.app.setStyle("Fusion")
        light_palette = self.app.style().standardPalette()
        self.app.setPalette(light_palette)

        # Keep references to windows
        self.main_window = None

    def on_analysis_complete(self, results):
        # Called when analysis is done in FileSelectionWindow
        # Hide file selection window
        self.file_selection.close()
        # Launch main window, keep reference
        self.main_window = MainWindow(
            frames=results["frames"],
            mask=results["masks"],
            rois=results["rois"],
            mean_intensities=results["mean_intensities"],
            analysis_output=results["analysis_output"],
            analysis_params=results["analysis_parameters"],
            app_controller=self,
        )
        self.main_window.show()

    def run(self):
        sys.exit(self.app.exec())

    def restart(self):
        if self.main_window:
            self.main_window.close()
            self.main_window = None

        self.file_selection = FileSelectionWindow()
        self.file_selection.analysis_complete.connect(self.on_analysis_complete)
        self.file_selection.show()
