import platform
import subprocess
from pathlib import Path
from PySide6.QtCore import QThread

class Meld(QThread):
    """Cross-platform Meld text diff viewer integration."""
    
    @staticmethod
    def get_path():
        """Get the path to meld executable based on OS, or None if not installed."""
        system = platform.system()
        
        if system == "Windows":
            # Check common Windows installation paths
            windows_paths = [
                Path("C:\\Program Files\\Meld\\Meld.exe"),
                Path("C:\\Program Files (x86)\\Meld\\Meld.exe"),
            ]
            for path in windows_paths:
                if path.exists():
                    return str(path)
        elif system in ["Linux", "Darwin"]:
            # For Linux/Mac, check if meld is in PATH
            result = subprocess.run(["which", "meld"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        
        return None
    
    def __init__(self, meld_path, target_path):
        super().__init__()
        self.meld_path = meld_path
        self.target_path = target_path

    def run(self):
        try:
            subprocess.run([self.meld_path, self.target_path])
        except Exception as e:
            print(f"Error opening meld: {e}")