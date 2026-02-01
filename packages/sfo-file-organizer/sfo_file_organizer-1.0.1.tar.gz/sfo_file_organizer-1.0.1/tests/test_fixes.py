
import pytest
from rules import classify_file
from unittest.mock import MagicMock, patch
import tkinter as tk
from gui import SFOFileOrganizerGUI

def test_txt_classification_with_keywords():
    """Test that .txt files go to Documents even with image keywords."""
    assert classify_file("my_logo.txt", ".txt") == "Documents"
    assert classify_file("photo_notes.txt", ".txt") == "Documents"
    assert classify_file("invoice.txt", ".txt") == "Documents"

def test_undo_disabled_in_watch_mode():
    """Test that Undo is disabled when Watch Mode is active."""
    root = tk.Tk()
    app = SFOFileOrganizerGUI(root)
    
    # Enable Watch Mode
    app.watch_mode.set(True)
    
    # Mock messagebox to verify error call
    with patch('tkinter.messagebox.showerror') as mock_error:
        app.start_undo()
        mock_error.assert_called_once()
        args, _ = mock_error.call_args
        assert "Cannot Undo" in args[0]
        assert "Watch Mode is active" in args[1]
    
    root.destroy()
