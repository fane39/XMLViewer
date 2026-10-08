"""
Main entry point for Light XML Viewer & WYSIWYG Editor.
"""

import sys
import tkinter as tk
from gui import XMLViewerApp


def main():
    root = tk.Tk()
    
    # Enable DPI awareness on Windows if available
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = XMLViewerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
