"""
Hogwarts Legacy Save Manager
A modern GUI application to manage, backup, and edit Hogwarts Legacy save files.

Entry point for the application.
"""

import multiprocessing
from tkinter import messagebox


def main():
    """Main entry point for the application."""
    multiprocessing.freeze_support()
    try:
        from src.app import App
        app = App()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    main()
