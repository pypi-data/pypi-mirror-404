"""
SFO File Organizer - Desktop GUI

A user-friendly graphical interface for the SFO File Organizer.
Designed for both technical and non-technical users.

Run with: python gui.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import scheduler
from pathlib import Path
from datetime import datetime
import sys
import os
try:
    import winreg
except ImportError:
    winreg = None

# Add parent directory to path for imports
# sys.path.insert(0, str(Path(__file__).parent))

from app_config import DEFAULT_SOURCE_DIR, FILE_CATEGORIES, get_resource_path, DATA_DIR
from organizer import organize_files, WATCHDOG_AVAILABLE, flatten_directory
from history import undo_last_session, get_history_summary, get_last_session


class ToolTip:
    """
    Creates a tooltip for a given widget as the mouse hovers above it.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None
        self.x = self.y = 0
        self._id1 = self.widget.bind("<Enter>", self.enter)
        self._id2 = self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                       background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                       font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


class GradientTheme:
    """Professional Dark Aesthetic Colors."""
    
    # Backgrounds
    BG_PRIMARY = "#121212"   # Deep Background
    BG_SECONDARY = "#252525" # Card Background (Slightly Lighter for Lift)
    BG_TERTIARY = "#303030"  # Input/Button Background
    
    # Text
    TEXT_PRIMARY = "#E0E0E0" # High Contrast Text
    TEXT_SECONDARY = "#B0B0B0" # Secondary Text
    
    # Section Colors (Subtle but Colorful Backgrounds/Borders)
    # Source: Subtle Green Tint
    SECTION_SOURCE = "#1E261E" # Very dark green-grey
    ACCENT_SOURCE_BORDER = "#2E7D32" # Dark Green
    
    # Actions: Subtle Orange/Amber Tint
    SECTION_ACTIONS = "#26221E" # Very dark orange-grey
    ACCENT_ACTIONS_BORDER = "#EF6C00" # Dark Orange
    
    # Logs: Subtle Blue Tint
    SECTION_LOGS = "#1E2226"   # Very dark blue-grey
    ACCENT_LOGS_BORDER = "#1565C0"    # Dark Blue
    
    # Functional Accents
    ACCENT = "#2196F3"       # Primary Blue
    
    # Status
    SUCCESS = "#81C784"      # Muted Green
    DANGER = "#E57373"       # Muted Red
    WARNING = "#FFB74D"      # Muted Orange
    
    BORDER = "#424242"       # Default Border


class RoundedButton(tk.Canvas):
    """
    A custom button widget with rounded corners and hover effects.
    Uses Canvas to draw a smooth rounded rectangle and text.
    """
    def __init__(self, parent, text, command=None, width=120, height=40, radius=20, 
                 bg_color="#1F1F1F", fg_color="#E0E0E0", 
                 btn_color="#2D2D2D", btn_hover_color="#424242",
                 font=("Segoe UI", 10, "bold")):
        
        super().__init__(parent, width=width, height=height, 
                         bg=bg_color, highlightthickness=0, bd=0, cursor="hand2")
        
        self.command = command
        self.text = text
        self.radius = radius
        self.bg_color = bg_color # Parent background (for corners)
        self.base_btn_color = btn_color
        self.current_btn_color = btn_color
        self.hover_color = btn_hover_color
        self.fg_color = fg_color
        self.font = font
        
        # State
        self.pressed = False
        
        # Bindings
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", self._on_hover)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Configure>", self._resize)
        
        # Initial draw
        self._draw()

    def _draw(self):
        self.delete("all")
        
        # Get dimensions
        w = self.winfo_width()
        h = self.winfo_height()
        
        # If dimensions are 1 (initial pack), use requested width/height
        if w <= 1: w = int(self["width"])
        if h <= 1: h = int(self["height"])
        
        # Draw Rounded Rectangle
        # We use a polygon or arcs/rectangles. 
        # A simpler robust way for variable width:
        r = self.radius
        c = self.current_btn_color
        
        # Ensure radius isn't too big for height
        if r * 2 > h: r = h // 2
        if r * 2 > w: r = w // 2
        
        # Create shape (smooth polygon approx or simpler shapes)
        # Using 2 circles and a rect for pill shape, or proper rounded rect
        
        # Top-Left
        self.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=c, outline=c, tags="bg")
        # Top-Right
        self.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=c, outline=c, tags="bg")
        # Bottom-Left
        self.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=c, outline=c, tags="bg")
        # Bottom-Right
        self.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=c, outline=c, tags="bg")
        
        # Center Rects
        self.create_rectangle(r, 0, w-r, h, fill=c, outline=c, tags="bg")
        self.create_rectangle(0, r, w, h-r, fill=c, outline=c, tags="bg")
        
        # Text
        self.create_text(w/2, h/2, text=self.text, fill=self.fg_color, font=self.font, tags="text")

    def _resize(self, event):
        self._draw()

    def _on_press(self, event):
        self.pressed = True
        # Darken slightly
        # self.current_btn_color = ... (could calc darken)
        self.configure(relief="sunken") # Canvas doesn't support relief like this visual change easily on content
        # We just keep color same or slighty shift
        self._draw()

    def _on_release(self, event):
        if self.pressed:
            self.pressed = False
            if self.command:
                self.command()
            self._draw()

    def _on_hover(self, event):
        self.current_btn_color = self.hover_color
        self._draw()

    def _on_leave(self, event):
        self.current_btn_color = self.base_btn_color
        self.pressed = False
        self._draw()
    
    def configure_color(self, btn_color=None, hover_color=None):
        if btn_color:
            self.base_btn_color = btn_color
            self.current_btn_color = btn_color
        if hover_color:
            self.hover_color = hover_color
        self._draw()


    def configure_color(self, btn_color=None, hover_color=None):
        if btn_color:
            self.base_btn_color = btn_color
            self.current_btn_color = btn_color
        if hover_color:
            self.hover_color = hover_color
        self._draw()


class RoundedEntry(tk.Canvas):
    """
    A custom entry widget with rounded corners.
    Wraps a standard ttk.Entry inside a Canvas.
    """
    def __init__(self, parent, textvariable=None, width=200, height=40, radius=20,
                 bg_color="#1F1F1F", border_color="#333333", fg_color="#E0E0E0",
                 font=("Segoe UI", 10), justify="left"):
        
        super().__init__(parent, width=width, height=height, 
                         bg=bg_color, highlightthickness=0, bd=0)
        
        self.radius = radius
        self.bg_color = bg_color
        self.border_color = border_color
        
        # Create the actual entry widget
        # specific style to match dark mode, removed border
        self.entry = tk.Entry(
            self, 
            textvariable=textvariable,
            font=font,
            bg=bg_color,
            fg=fg_color,
            bd=0,
            highlightthickness=0,
            justify=justify,
            insertbackground=fg_color # Cursor color
        )
        
        # We need to place the entry widget using create_window
        # Adjust dimensions safely
        entry_width = width - radius # leave padding
        self.window_item = self.create_window(
            width/2, height/2, 
            window=self.entry, 
            width=entry_width,
            height=height-10 # padding top/bottom
        )
        
        self.bind("<Configure>", self._draw)
        
        # Focus bindings to highlight border
        self.entry.bind("<FocusIn>", self._on_focus)
        self.entry.bind("<FocusOut>", self._on_unfocus)
        
        self._draw()

    def _draw(self, event=None):
        super().delete("bg")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1: w = int(self["width"])
        if h <= 1: h = int(self["height"])
        
        r = self.radius
        c = self.bg_color
        b = self.border_color
        
        # Draw Rounded Border (using arcs and lines/rects)
        # Top-Left
        self.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, style="arc", outline=b, width=2, tags="bg")
        # Top-Right
        self.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, style="arc", outline=b, width=2, tags="bg")
        # Bottom-Left
        self.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, style="arc", outline=b, width=2, tags="bg")
        # Bottom-Right
        self.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, style="arc", outline=b, width=2, tags="bg")
        
        # Lines
        self.create_line(r, 0, w-r, 0, fill=b, width=2, tags="bg") # Top
        self.create_line(r, h, w-r, h, fill=b, width=2, tags="bg") # Bottom
        self.create_line(0, r, 0, h-r, fill=b, width=2, tags="bg") # Left
        self.create_line(w, r, w, h-r, fill=b, width=2, tags="bg") # Right
        
        self.tag_lower("bg")

    def _on_focus(self, event):
        self.border_color = GradientTheme.ACCENT # Highlight color
        self._draw()

    def _on_unfocus(self, event):
        self.border_color = "#333333" # Reset
        self._draw()
    
    # Proxy entry methods
    def get(self): return self.entry.get()
    def insert(self, *args): return self.entry.insert(*args)
    def delete(self, *args): return self.entry.delete(*args)


class ScrollableFrame(ttk.Frame):
    """
    A scrollable frame using Canvas.
    """
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # Canvas and Scrollbar
        self.canvas = tk.Canvas(self, borderwidth=0, background=GradientTheme.BG_PRIMARY, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Scrollable Frame inside Canvas
        self.scrollable_frame = ttk.Frame(self.canvas, style="TFrame")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create Window in Canvas
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configuration
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Resize Logic: Force Width to match Canvas
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Mousewheel
        self.bind_mousewheel(self.scrollable_frame)
        self.bind_mousewheel(self.canvas)

    def _on_canvas_configure(self, event):
        # Resize the inner frame to match the canvas width
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def bind_mousewheel(self, widget):
        if sys.platform.startswith('win'):
            widget.bind("<MouseWheel>", self._on_mousewheel)
        else:
            widget.bind("<Button-4>", self._on_mousewheel)
            widget.bind("<Button-5>", self._on_mousewheel)
            
        for child in widget.winfo_children():
            self.bind_mousewheel(child)

    def _on_mousewheel(self, event):
        if sys.platform.startswith('win'):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        else:
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            else:
                self.canvas.yview_scroll(1, "units")


class SFOFileOrganizerGUI:
    """Main GUI application class."""
    
    def set_icon(self, window):
        """Set the best available icon for a window."""
        try:
            # 1. Set the Window Icon (ICO) - good for title bar and default
            ico_path = get_resource_path("app_icon.ico")
            if os.path.exists(ico_path):
                window.iconbitmap(ico_path)
                
            # 2. Set the Taskbar Icon (PNG) - critical for high-res sharpness
            # We prefer the PNG source if available
            png_path = get_resource_path("app_icon.png")
            if os.path.exists(png_path):
                img = tk.PhotoImage(file=png_path)
                # Keep a reference to prevent garbage collection if needed, though usually not for root
                if not hasattr(self, '_icon_img'):
                    self._icon_img = img
                window.iconphoto(True, img)
        except Exception:
            pass
            
    def detect_system_theme(self):
        """Detect if Windows is using Dark Mode."""
        try:
            if winreg:
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return value == 0
        except Exception:
            pass
        return True # Default to Dark Mode if check fails or on other OS

    def __init__(self, root):
        self.root = root
        self.set_icon(self.root)
        
        self.root.title("SFO File Organizer")
        self.root.geometry("800x700")
        self.root.minsize(600, 500)
        
        # Dark Title Bar (Windows 10/11)
        try:
            import ctypes
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            # Need to wait for window to have a handle, but root usually has one.
            # We can also call this via `update_idletasks` or just try here for root.
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            # For root, sometimes GetParent returns 0, try winfo_id directly if so or check behaviour.
            # Actually, Tk root wrapper... let's try calling Update first.
            self.root.update()
            hwnd = ctypes.windll.user32.GetForegroundWindow() # Naive but often works for active startup
            # Better: use winfo_id
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
        except Exception:
            pass
        
        # Theme
        self.colors = GradientTheme
        
        # Configure theme
        self.setup_theme()
        
        # Queue for thread communication
        self.message_queue = queue.Queue()
        
        # State
        self.source_dir = tk.StringVar(value=DEFAULT_SOURCE_DIR)
        self.watch_mode = tk.BooleanVar(value=False)
        self.is_running = False
        self.observer = None
        
        # Build UI
        self.create_widgets()
        
        # Global Bindings
        # 1. Clear Focus when clicking background
        self.root.bind("<Button-1>", self._on_global_click)
        
        # 2. Mousewheel Scrolling (Global)
        self.root.bind_all("<MouseWheel>", self._on_global_mousewheel)
        
        # Start message processing
        self.process_messages()
    
    def _on_global_click(self, event):
        """Clear focus from Entry/Combobox when clicking outside."""
        widget = event.widget
        # Check if the clicked widget is NOT an entry type
        if not isinstance(widget, (ttk.Entry, ttk.Combobox, tk.Text, tk.Entry)):
            self.root.focus_set()
            
    def _on_global_mousewheel(self, event):
        """Scroll the main view with mousewheel, unless scrolling a dropdown."""
        try:
            widget = event.widget
            # Standard Listbox/Text check
            if isinstance(widget, (tk.Listbox, tk.Text)):
                return
            
            # Check if a Combobox has focus (active interaction)
            focused = self.root.focus_get()
            if isinstance(focused, ttk.Combobox):
                 # If user is hovering the combobox popdown, standard event processing might capture it,
                 # but if we are here, it means the event bubbled to root.
                 # We should be careful. If the combobox is open, we shouldn't scroll page.
                 # Simple heuristic: If focus is on combobox, disable page scroll? 
                 # Or better: check if mouse is strictly over the main scroll area?
                 pass

            # Aggressive Check: If widget class matches Combobox popdown
            if "popdown" in str(widget).lower() or "combobox" in str(widget).lower():
                return

            if hasattr(self, 'main_scroll'):
                self.main_scroll._on_mousewheel(event)
        except Exception:
            pass

    def setup_theme(self):
        """Configure the theme for ttk widgets."""
        style = ttk.Style()
        style.theme_use('clam')
        
        c = self.colors
        
        # Defaults
        style.configure(".",
            background=c.BG_PRIMARY,
            foreground=c.TEXT_PRIMARY,
            fieldbackground=c.BG_TERTIARY,
            troughcolor=c.BG_TERTIARY,
            bordercolor=c.BORDER,
            font=("Segoe UI", 10)
        )
        
        # Main Frame Background
        style.configure("TFrame", background=c.BG_PRIMARY)
        
        # --- Section Card Styles ---
        # Source Card (Green)
        # Source Card (Green)
        style.configure("Source.TFrame", background=c.SECTION_SOURCE, relief="flat")
        style.configure("Source.TLabel", background=c.SECTION_SOURCE, foreground=c.ACCENT_SOURCE_BORDER)
        style.configure("SourceTitle.TLabel", background=c.SECTION_SOURCE, foreground=c.ACCENT_SOURCE_BORDER, font=("Segoe UI", 14, "bold"))
        style.configure("Source.TCheckbutton", background=c.SECTION_SOURCE, foreground=c.ACCENT_SOURCE_BORDER)
        style.map("Source.TCheckbutton", 
            background=[("active", c.SECTION_SOURCE)],
            indicatorcolor=[("selected", c.ACCENT), ("pressed", c.ACCENT)],
            indicatorbackground=[("selected", c.ACCENT), ("pressed", c.ACCENT)] # High contrast tick bg
        )

        # Actions Card (Orange)
        style.configure("Actions.TFrame", background=c.SECTION_ACTIONS, relief="flat")
        style.configure("Actions.TLabel", background=c.SECTION_ACTIONS, foreground=c.ACCENT_ACTIONS_BORDER)
        style.configure("ActionsTitle.TLabel", background=c.SECTION_ACTIONS, foreground=c.ACCENT_ACTIONS_BORDER, font=("Segoe UI", 14, "bold"))
        
        # Logs Card (Blue)
        style.configure("Logs.TFrame", background=c.SECTION_LOGS, relief="flat")
        style.configure("Logs.TLabel", background=c.SECTION_LOGS, foreground=c.ACCENT_LOGS_BORDER)
        style.configure("LogsTitle.TLabel", background=c.SECTION_LOGS, foreground=c.ACCENT_LOGS_BORDER, font=("Segoe UI", 14, "bold"))
        
        # Standard Labels
        style.configure("Header.TLabel", font=("Segoe UI", 24, "bold"), foreground=c.TEXT_PRIMARY, background=c.BG_PRIMARY)
        style.configure("Subtitle.TLabel", font=("Segoe UI", 11), foreground=c.TEXT_SECONDARY, background=c.BG_PRIMARY)
        
        # Buttons (Modern Rounded look simulated with padding)
        style.configure("TButton", 
            font=("Segoe UI", 9, "bold"), 
            padding=(10, 8), 
            borderwidth=0,
            background=c.BG_SECONDARY,
            foreground=c.TEXT_PRIMARY
        )
        style.map("TButton", 
            background=[("active", c.BG_TERTIARY), ("pressed", c.BG_SECONDARY)],
            foreground=[("active", "white")]
        )
        
        # Primary Action (Blue)
        style.configure("Green.TButton", background=c.ACCENT, foreground="white")
        style.map("Green.TButton", background=[("active", "#1976D2"), ("pressed", c.ACCENT)])
        
        # Secondary Action (Dark Grey/Outline feel)
        style.configure("Orange.TButton", background=c.BG_TERTIARY, foreground="white")
        style.map("Orange.TButton", background=[("active", "#424242"), ("pressed", c.BG_TERTIARY)])
        
        # Tertiary Action (Dark Grey)
        style.configure("Blue.TButton", background=c.BG_TERTIARY, foreground="white")
        style.map("Blue.TButton", background=[("active", "#424242"), ("pressed", c.BG_TERTIARY)])

        # Entry
        style.configure("TEntry", 
            fieldbackground=c.BG_TERTIARY,
            foreground=c.TEXT_PRIMARY,
            borderwidth=0,
            relief="flat",
            padding=5,
            insertcolor=c.TEXT_PRIMARY
        )
        
        # Progress
        style.configure("TProgressbar", background=c.ACCENT, troughcolor=c.BG_TERTIARY, bordercolor=c.BG_PRIMARY)
        
        # Combobox
        style.configure("TCombobox",
            fieldbackground=c.BG_TERTIARY,
            background=c.SECTION_ACTIONS, # Arrow button bg
            foreground=c.TEXT_PRIMARY,
            bordercolor=c.SECTION_ACTIONS,
            darkcolor=c.SECTION_ACTIONS,
            lightcolor=c.SECTION_ACTIONS,
            arrowcolor=c.TEXT_PRIMARY,
            padding=5,
            relief="flat"
        )
        style.map("TCombobox",
            fieldbackground=[("readonly", c.BG_TERTIARY)],
            background=[("active", c.BG_SECONDARY)], # Hover arrow
            arrowcolor=[("active", c.ACCENT)]
        )
        
        # Dropdown Listbox Colors (Global for the app)
        self.root.option_add('*TCombobox*Listbox.background', c.BG_SECONDARY)
        self.root.option_add('*TCombobox*Listbox.foreground', c.TEXT_PRIMARY)
        self.root.option_add('*TCombobox*Listbox.selectBackground', c.ACCENT)
        self.root.option_add('*TCombobox*Listbox.selectForeground', 'white')
        self.root.option_add('*TCombobox*Listbox.font', ("Segoe UI", 10))
        
        self.root.configure(bg=c.BG_PRIMARY)
    
    def create_widgets(self):
        """Create the main UI with a vertical gradient card layout."""
        
        # Use Scrollable Frame to prevent cutoff in small windows
        self.main_scroll = ScrollableFrame(self.root)
        self.main_scroll.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Main Container (inside scrollable area)
        main_container = self.main_scroll.scrollable_frame
        
        # Add padding to the inner container
        content_frame = ttk.Frame(main_container, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # --- Header ---
        header_frame = ttk.Frame(content_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Icon (if we can load it separately or just text)
        # ttk.Label(header_frame, image=self.icon_img).pack(side=tk.LEFT, padx=(0, 10)) 
        
        title_box = ttk.Frame(header_frame)
        title_box.pack(side=tk.LEFT)
        
        ttk.Label(title_box, text="SFO File Organizer", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(title_box, text="Automatically organize your files into categorized folders", style="Subtitle.TLabel").pack(anchor=tk.W)

        # --- Card 1: Source (Green) ---
        self.create_source_card(content_frame) # Pass inner frame

        # --- Card 2: Actions (Orange) ---
        self.create_actions_card(content_frame)
        
        # --- Card 3: Automation (Orange/Extensions) ---
        self.create_automation_card(content_frame)

        # --- Progress Section ---
        self.create_progress_section(content_frame)

        # --- Card 4: Logs (Blue) ---
        self.create_logs_card(content_frame)

    def create_source_card(self, parent):
        """Create the Source Folder section (Green Tint)."""
        # Card Frame with colorful border (using highlightthickness/highlightbackground or frame trick)
        # Ttk frames don't support colored borders easily. We can simulate it by wrapping in a Frame with background.
        
        # Wrapper for Border
        border_frame = tk.Frame(parent, bg=self.colors.ACCENT_SOURCE_BORDER, bd=1)
        border_frame.pack(fill=tk.X, pady=(0, 15))
        
        card = tk.Frame(border_frame, bg=self.colors.SECTION_SOURCE, padx=20, pady=20)
        card.pack(fill=tk.BOTH, padx=1, pady=1) # 1px internal padding shows parent bg as border
        
        # Header
        # We need custom labels for tk.Frame background
        tk.Label(card, text="📂 Source Folder", font=("Segoe UI", 12, "bold"), 
                 bg=self.colors.SECTION_SOURCE, fg=self.colors.ACCENT_SOURCE_BORDER).pack(anchor=tk.W, pady=(0, 5))
        
        tk.Label(card, text="Select the folder you want to organize", font=("Segoe UI", 10),
                 bg=self.colors.SECTION_SOURCE, fg=self.colors.TEXT_SECONDARY).pack(anchor=tk.W, pady=(0, 15))
        
        # Input Row
        input_row = tk.Frame(card, bg=self.colors.SECTION_SOURCE)
        input_row.pack(fill=tk.X)
        
        # Rounded Entry for Source
        self.source_entry_widget = RoundedEntry(
            input_row, 
            textvariable=self.source_dir, 
            width=300, 
            height=40,
            bg_color=self.colors.SECTION_SOURCE, 
            border_color="#424242",
            fg_color=self.colors.TEXT_PRIMARY
        )
        self.source_entry_widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Browse Button (Rounded)
        RoundedButton(
            input_row, text="Browse...", command=self.browse_folder,
            bg_color=self.colors.SECTION_SOURCE, 
            btn_color=self.colors.BG_TERTIARY, btn_hover_color="#424242",
            width=100, height=40
        ).pack(side=tk.RIGHT)
        
        # Options Row
        options_row = tk.Frame(card, bg=self.colors.SECTION_SOURCE)
        options_row.pack(fill=tk.X, pady=(15, 0))
        
        self.watch_mode = tk.BooleanVar(value=False)
        self.smart_context = tk.BooleanVar(value=True)
        
        # Custom Checkbuttons for tk Frame
        # Using ttk.Checkbutton requires style matching, simple tk checkbutton might be easier for bg match
        # sticking to ttk checkbutton with specific style or trick?
        # Let's use ttk with a style configured for this section.
        
        s = ttk.Style()
        s.configure("Source.TCheckbutton", background=self.colors.SECTION_SOURCE, foreground=self.colors.TEXT_PRIMARY, font=("Segoe UI", 10))
        
        watch_check = ttk.Checkbutton(options_row, text="Watch Mode (Real-time)", variable=self.watch_mode, 
                       command=self.toggle_watch_mode, style="Source.TCheckbutton")
        watch_check.pack(side=tk.LEFT, padx=(0, 20))
        ToolTip(watch_check, "Automatically organize new files as they appear.")
                       
        smart_check = ttk.Checkbutton(options_row, text="Smart Context (Auto-Detect)", variable=self.smart_context,
                       style="Source.TCheckbutton")
        smart_check.pack(side=tk.LEFT)
        ToolTip(smart_check, "Adapt organization based on folder content (e.g. Sort images by Year).")

    def create_actions_card(self, parent):
        """Create the Actions section (Orange/Amber Tint)."""
        # Wrapper for Border
        border_frame = tk.Frame(parent, bg=self.colors.ACCENT_ACTIONS_BORDER, bd=1)
        border_frame.pack(fill=tk.X, pady=(0, 15))
        
        card = tk.Frame(border_frame, bg=self.colors.SECTION_ACTIONS, padx=15, pady=15)
        card.pack(fill=tk.BOTH, padx=1, pady=1)
        
        # Header
        tk.Label(card, text="⚡ Actions", font=("Segoe UI", 12, "bold"),
                 bg=self.colors.SECTION_ACTIONS, fg=self.colors.ACCENT_ACTIONS_BORDER).pack(anchor=tk.W, pady=(0, 5))
        
        tk.Label(card, text="Choose an action to perform", font=("Segoe UI", 10),
                 bg=self.colors.SECTION_ACTIONS, fg=self.colors.TEXT_SECONDARY).pack(anchor=tk.W, pady=(0, 10))
        
        # Grid layout for buttons
        # tk.Frame doesn't support 'style', just bg
        btn_grid = tk.Frame(card, bg=self.colors.SECTION_ACTIONS)
        btn_grid.pack(fill=tk.X)
        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)
        
        # Row 1
        r1 = tk.Frame(btn_grid, bg=self.colors.SECTION_ACTIONS)
        r1.pack(fill=tk.X, pady=(0, 10))
        
        # Organize (Primary Blue)
        self.organize_btn = RoundedButton(
            r1, text="🚀 Organize Now", command=self.start_organize, 
            bg_color=self.colors.SECTION_ACTIONS, btn_color=self.colors.ACCENT, btn_hover_color="#1976D2",
            width=200, height=45
        )
        self.organize_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Preview (Secondary)
        self.preview_btn = RoundedButton(
            r1, text="👁️ Preview", command=self.start_preview,
            bg_color=self.colors.SECTION_ACTIONS, btn_color=self.colors.BG_TERTIARY, btn_hover_color="#424242",
            width=120, height=45
        )
        self.preview_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Row 2
        r2 = tk.Frame(btn_grid, bg=self.colors.SECTION_ACTIONS)
        r2.pack(fill=tk.X)
        
        # Undo
        self.undo_btn = RoundedButton(
            r2, text="↩️ Undo", command=self.start_undo,
            bg_color=self.colors.SECTION_ACTIONS, btn_color=self.colors.BG_TERTIARY, btn_hover_color="#424242",
            height=40
        )
        self.undo_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Flatten
        flatten_btn = RoundedButton(
            r2, text="🧹 Flatten", command=self.start_flatten,
            bg_color=self.colors.SECTION_ACTIONS, 
            btn_color="#C62828", # Muted Red
            btn_hover_color="#B71C1C", # Darker Red
            height=40
        )
        flatten_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ToolTip(flatten_btn, "Undo organization by moving files out of subfolders.")
        
        # History
        self.history_btn = RoundedButton(
            r2, text="📜 History", command=self.show_history,
            bg_color=self.colors.SECTION_ACTIONS, btn_color=self.colors.BG_TERTIARY, btn_hover_color="#424242",
            height=40
        )
        self.history_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

    def create_automation_card(self, parent):
        """Create the Automation section."""
        # Using the Actions theme for Automation to group them as "Tools"
        border_frame = tk.Frame(parent, bg=self.colors.ACCENT_ACTIONS_BORDER, bd=1)
        border_frame.pack(fill=tk.X, pady=(0, 15))
        
        card = tk.Frame(border_frame, bg=self.colors.SECTION_ACTIONS, padx=15, pady=15)
        card.pack(fill=tk.BOTH, padx=1, pady=1)
        
        tk.Label(card, text="⏰ Automation", font=("Segoe UI", 12, "bold"),
                 bg=self.colors.SECTION_ACTIONS, fg=self.colors.ACCENT_ACTIONS_BORDER).pack(anchor=tk.W, pady=(0, 5))
        
        tk.Label(card, text="Schedule daily organization", font=("Segoe UI", 10),
                 bg=self.colors.SECTION_ACTIONS, fg=self.colors.TEXT_SECONDARY).pack(anchor=tk.W, pady=(0, 10))
        
        # Scheduler Controls
        sched_row = tk.Frame(card, bg=self.colors.SECTION_ACTIONS)
        sched_row.pack(fill=tk.X)
        
        self.sched_time = tk.StringVar(value="09:00")
        
        # Generate time options (every 30 mins)
        times = []
        for h in range(24):
            times.append(f"{h:02d}:00")
            times.append(f"{h:02d}:30")
        
        time_entry = ttk.Combobox(sched_row, textvariable=self.sched_time, values=times, width=10, font=("Segoe UI", 10), justify="center")
        time_entry.pack(side=tk.LEFT, padx=(0, 15))
        ToolTip(time_entry, "Select or type time (HH:MM).")
        
        # Un-focus when clicking away (Global binding helper)
        def clear_focus(event):
             if event.widget != time_entry:
                 self.root.focus_set()
        
        # Fixed Width for Full Visibility
        self.sched_btn = RoundedButton(
            sched_row,
            text="ENABLE SCHEDULE",
            command=self.toggle_schedule,
            bg_color=self.colors.SECTION_ACTIONS,
            btn_color=self.colors.ACCENT, 
            btn_hover_color="#1976D2",
            width=200, height=35  # Increased Width to 200
        )
        self.sched_btn.pack(side=tk.LEFT)
        ToolTip(self.sched_btn, "Run sorting automatically every day at this time.")

    def create_logs_card(self, parent):
        """Create the Logs section (Blue Tint)."""
        border_frame = tk.Frame(parent, bg=self.colors.ACCENT_LOGS_BORDER, bd=1)
        border_frame.pack(fill=tk.BOTH, expand=True)
        
        card = tk.Frame(border_frame, bg=self.colors.SECTION_LOGS, padx=15, pady=15)
        card.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Header
        head = tk.Frame(card, bg=self.colors.SECTION_LOGS)
        head.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(head, text="📝 Activity Log", font=("Segoe UI", 12, "bold"),
                 bg=self.colors.SECTION_LOGS, fg=self.colors.ACCENT_LOGS_BORDER).pack(side=tk.LEFT)
                 
        tk.Button(head, text="Clear", command=self.clear_log, 
                  bg=self.colors.BG_TERTIARY, fg=self.colors.TEXT_PRIMARY, bd=0).pack(side=tk.RIGHT)
        
        # Text Area
        # We need a frame for the text+scrollbar
        log_container = tk.Frame(card, bg=self.colors.SECTION_LOGS)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(
            log_container,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="white",
            fg="#212529",
            relief=tk.FLAT,
            padx=10,
            pady=10,
            height=8
        )
        scrollbar = ttk.Scrollbar(log_container, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Tags with updated colors
        self.log_text.tag_configure("info", foreground="#212529")
        self.log_text.tag_configure("success", foreground=self.colors.SUCCESS)
        self.log_text.tag_configure("warning", foreground=self.colors.WARNING)
        self.log_text.tag_configure("error", foreground=self.colors.DANGER)
        self.log_text.tag_configure("header", foreground=self.colors.ACCENT_LOGS_BORDER, font=("Consolas", 9, "bold"))
        
        self.log("Welcome to SFO File Organizer!", "header")
        self.log(f"Default source: {self.source_dir.get()}", "info")
        
    def create_progress_section(self, parent):
        """Create the progress bar section."""
        self.progress_frame = ttk.Frame(parent)
        self.progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate', length=400)
        self.status_label = ttk.Label(self.progress_frame, text="", style="Subtitle.TLabel")
    
    def browse_folder(self):
        """Open folder browser dialog."""
        folder = filedialog.askdirectory(
            initialdir=self.source_dir.get(),
            title="Select folder to organize"
        )
        if folder:
            self.source_dir.set(folder)
            self.log(f"Selected folder: {folder}", "info")
    
    def log(self, message, tag="info"):
        """Add a message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """Clear the log output."""
        self.log_text.delete(1.0, tk.END)
    
    def set_running(self, running):
        """Set the running state and update UI accordingly."""
        self.is_running = running
        state = tk.DISABLED if running else tk.NORMAL
        
        self.organize_btn.configure(state=state)
        self.preview_btn.configure(state=state)
        self.undo_btn.configure(state=state)
        self.history_btn.configure(state=state)
        
        if running:
            self.progress_bar.pack(fill=tk.X)
            self.status_label.pack(anchor=tk.W, pady=(5, 0))
            self.progress_bar.start(10)
        else:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.status_label.pack_forget()
    
    def start_organize(self):
        """Start the organization process."""
        source = self.source_dir.get()
        
        if not Path(source).exists():
            messagebox.showerror("Error", f"Folder not found: {source}")
            return
        
        self.log(f"\n{'='*50}", "header")
        self.log("Starting file organization...", "header")
        self.log(f"Source: {source}", "info")
        
        self.set_running(True)
        self.status_label.configure(text="Organizing files...")
        
        # Run in thread
        thread = threading.Thread(
            target=self._run_organize,
            args=(source, False),
            daemon=True
        )
        thread.start()
        
    
    def toggle_watch_mode(self):
        """Start or stop the real-time file watcher."""
        if self.watch_mode.get():
            source = self.source_dir.get()
            if not Path(source).exists():
                messagebox.showerror("Error", f"Folder not found: {source}")
                self.watch_mode.set(False)
                return
            
            if not WATCHDOG_AVAILABLE:
                messagebox.showerror("Error", "Watch Mode requires 'watchdog' library.\nInstall with: pip install watchdog")
                self.watch_mode.set(False)
                return
                
            self.log(f"\n{'='*50}", "header")
            self.log(f"WATCH MODE ENABLED: Monitoring {source}", "header")
            self.status_label.configure(text="Watching for changes...")
            self.root.title("SFO File Organizer (WATCHING)")
            
            # Start watcher in separate thread
            self._start_watcher(source)
        else:
            self._stop_watcher()
            self.log("WATCH MODE DISABLED", "warning")
            self.status_label.configure(text="")
            self.root.title("SFO File Organizer")

    def _start_watcher(self, source):
        """Initialize and start the watchdog observer."""
        from organizer import OrganizerHandler
        from watchdog.observers import Observer
        
        self.observer = Observer()
        handler = OrganizerHandler(source, source, use_ai=False, smart_context=self.smart_context.get())
        
        # Intercept handler logging to UI
        # We'll rely on the handler calling organize_files which logs
        
        self.observer.schedule(handler, source, recursive=False)
        self.observer.start()

    def _stop_watcher(self):
        """Stop the watchdog observer."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
    
    def start_preview(self):
        """Start the preview (dry-run) process."""
        source = self.source_dir.get()
        
        if not Path(source).exists():
            messagebox.showerror("Error", f"Folder not found: {source}")
            return
        
        self.log(f"\n{'='*50}", "header")
        self.log("Previewing changes (dry run)...", "header")
        self.log(f"Source: {source}", "info")
        
        self.set_running(True)
        self.status_label.configure(text="Analyzing files...")
        
        # Run in thread
        thread = threading.Thread(
            target=self._run_organize,
            args=(source, True),
            daemon=True
        )
        thread.start()
    
    def _run_organize(self, source, dry_run):
        """Run organization in a separate thread."""
        try:
            stats = organize_files(
                source_dir=source,
                dest_dir=source,  # In-place organization
                dry_run=dry_run,
                use_ai=False,
                smart_context=self.smart_context.get()
            )
            
            self.message_queue.put(("organize_complete", stats, dry_run))
            
        except Exception as e:
            self.message_queue.put(("error", str(e), None))
    
    def start_undo(self):
        """Start the undo process."""
        if self.watch_mode.get():
            messagebox.showerror(
                "Cannot Undo",
                "Cannot undo while Watch Mode is active.\n\n"
                "Please disable Watch Mode first to prevent immediate re-organization of restored files."
            )
            return

        last_session = get_last_session()
        
        if not last_session:
            messagebox.showinfo("No History", "No organization sessions to undo.")
            return
        
        # Confirm undo
        files_count = len(last_session.get("movements", []))
        timestamp = last_session.get("timestamp", "Unknown")
        
        if not messagebox.askyesno(
            "Confirm Undo",
            f"Undo the last organization?\n\n"
            f"Session: {timestamp}\n"
            f"Files to restore: {files_count}"
        ):
            return
        
        self.log(f"\n{'='*50}", "header")
        self.log("Undoing last organization...", "header")
        
        self.set_running(True)
        self.status_label.configure(text="Restoring files...")
        
        # Run in thread
        thread = threading.Thread(target=self._run_undo, daemon=True)
        thread.start()
    
    def _run_undo(self):
        """Run undo in a separate thread."""
        try:
            stats = undo_last_session()
            self.message_queue.put(("undo_complete", stats, None))
        except Exception as e:
            self.message_queue.put(("error", str(e), None))
    
    def start_flatten(self):
        """Start the flatten (reset) process."""
        source = self.source_dir.get()
        
        if not Path(source).exists():
            messagebox.showerror("Error", f"Folder not found: {source}")
            return
            
        if not messagebox.askyesno(
            "Confirm Reset (Flatten)",
            "Are you sure you want to flatten this folder?\n\n"
            "This will move all files from subfolders back to the root and delete empty subfolders.\n\n"
            "This action CAN be undone via 'Undo Last'."
        ):
            return
        
        self.log(f"\n{'='*50}", "header")
        self.log("Starting Folder Reset (Flatten)...", "header")
        self.log(f"Target: {source}", "info")
        
        self.set_running(True)
        self.status_label.configure(text="Resetting folder structure...")
        
        # Run in thread
        thread = threading.Thread(
            target=self._run_flatten,
            args=(source,),
            daemon=True
        )
        thread.start()

    def _run_flatten(self, source):
        """Run flatten in a separate thread."""
        try:
            stats = flatten_directory(source)
            self.message_queue.put(("flatten_complete", stats, None))
        except Exception as e:
            self.message_queue.put(("error", str(e), None))

    def _handle_flatten_complete(self, stats):
        """Handle flatten completion."""
        self.set_running(False)
        
        if stats.get('moved', 0) == 0 and stats.get('removed_dirs', 0) == 0:
            self.log("No organizer-created folders found to flatten.", "warning")
            messagebox.showinfo(
                "Nothing to Flatten", 
                "No organizer-created folders found.\n\n"
                "Only folders created by the organizer can be flattened."
            )
            return
        
        self.log("Reset complete!", "success")
        self.log(f"  Files moved to root: {stats.get('moved', 0)}", "success")
        self.log(f"  Subfolders removed: {stats.get('removed_dirs', 0)}", "success")
        if stats.get('skipped_dirs', 0) > 0:
            self.log(f"  Pre-existing folders preserved: {stats.get('skipped_dirs', 0)}", "info")
        
        msg = f"Folder has been flattened.\n\nFiles moved: {stats.get('moved', 0)}\nFolders removed: {stats.get('removed_dirs', 0)}"
        if stats.get('skipped_dirs', 0) > 0:
            msg += f"\nPre-existing folders preserved: {stats.get('skipped_dirs', 0)}"
        
        messagebox.showinfo("Reset Complete", msg)

    def toggle_schedule(self):
        """Enable or disable the daily schedule."""
        time_str = self.sched_time.get()
        source = self.source_dir.get()
        
        # Simple validation
        try:
            # Check format
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            messagebox.showerror("Invalid Time", "Please enter time in HH:MM format (24-hour).")
            return
            
        # Try to schedule
        success, msg = scheduler.create_scheduled_task(time_str, source)
        
        if success:
            messagebox.showinfo("Schedule Enabled", msg)
            self.log(f"Schedule ENABLED: Daily at {time_str}", "success")
        else:
            messagebox.showerror("Schedule Data", msg)
            self.log(f"Schedule Error: {msg}", "error")

    def show_history(self):
        """Show the history dialog."""
        history = get_history_summary()
        
        if not history:
            messagebox.showinfo("History", "No organization records found.")
            return
        
        # Create history window
        history_win = tk.Toplevel(self.root)
        self.set_icon(history_win)
        
        # Dark Title Bar for History Window
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(history_win.winfo_id())
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
        except Exception:
            pass
            
        history_win.title("SYSTEM ARCHIVES")
        history_win.geometry("600x500")
        history_win.configure(bg=self.colors.BG_PRIMARY)
        
        # Header
        ttk.Label(
            history_win,
            text="Organization History",
            style="Header.TLabel"
        ).pack(pady=(20, 10))
        
        # History list
        list_frame = ttk.Frame(history_win)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        history_text = tk.Text(
            list_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=self.colors.BG_SECONDARY,
            fg=self.colors.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=15,
            pady=15
        )
        history_text.pack(fill=tk.BOTH, expand=True)
        
        # Populate history
        for i, session in enumerate(reversed(history)):
            status = "[EXEC]" if not session.get("undone") else "[REVERTED]"
            if session.get("dry_run"):
                status = "[SIMULATION]"
            
            # Format timestamp
            ts = session.get('timestamp', 'Unknown')
            
            history_text.insert(tk.END, f"Session {len(history)-i}: {ts}\n")
            history_text.insert(tk.END, f"Status: {status}\n")
            history_text.insert(tk.END, f"Source: {session.get('source_dir')}\n")
            history_text.insert(tk.END, f"Files Moved: {session.get('files_moved')}\n")
            history_text.insert(tk.END, "-"*40 + "\n\n")
            
        history_text.configure(state=tk.DISABLED)
    
    def process_messages(self):
        """Process messages from worker threads."""
        try:
            while True:
                msg_type, data, extra = self.message_queue.get_nowait()
                
                if msg_type == "organize_complete":
                    self._handle_organize_complete(data, extra)
                elif msg_type == "undo_complete":
                    self._handle_undo_complete(data)
                elif msg_type == "flatten_complete":
                    self._handle_flatten_complete(data)
                elif msg_type == "error":
                    self._handle_error(data)
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_messages)
    
    def _handle_organize_complete(self, stats, dry_run):
        """Handle organization completion."""
        self.set_running(False)
        
        mode = "Preview" if dry_run else "Organization"
        # organize_files returns {"moved": X, "skipped": Y, "errors": Z}
        total = stats.get("moved", 0) if stats else 0
        
        self.log(f"\n{mode} complete!", "success")
        self.log(f"  Files organized: {total}", "success")
        
        if stats.get("skipped", 0) > 0:
            self.log(f"  Skipped (directories): {stats.get('skipped', 0)}", "info")
        if stats.get("errors", 0) > 0:
            self.log(f"  Errors: {stats.get('errors', 0)}", "warning")
        
        if not dry_run and total > 0:
            messagebox.showinfo(
                "Success",
                f"Organization complete!\n\n{total} files organized."
            )
    
    def _handle_undo_complete(self, stats):
        """Handle undo completion."""
        self.set_running(False)
        
        if stats.get("success"):
            restored = stats.get('restored', 0)
            if restored > 0:
                self.log("Undo complete!", "success")
                self.log(f"  Files restored: {restored}", "success")
                if stats.get("errors", 0) > 0:
                    self.log(f"  Errors: {stats.get('errors', 0)}", "warning")
                
                messagebox.showinfo(
                    "Undo Complete",
                    f"Successfully restored {restored} files."
                )
            else:
                self.log("Undo complete - no files needed restoring.", "info")
                messagebox.showinfo(
                    "Undo Complete",
                    "No files needed to be restored.\n\nThe files may have already been moved or deleted."
                )
        else:
            msg = stats.get('message', 'Unknown error')
            if "No session to undo" in msg:
                self.log("No previous sessions to undo.", "info")
                messagebox.showinfo("No History", "No previous organization sessions to undo.")
            else:
                self.log(f"Undo failed: {msg}", "error")
                messagebox.showerror("Undo Failed", msg)
    


    def _handle_error(self, error_msg):
        """Handle errors from worker threads."""
        self.set_running(False)
        self.log(f"Error: {error_msg}", "error")
        messagebox.showerror("Error", error_msg)


def main():
    """Main entry point."""
    # Set explicit AppUserModelID for Windows to ensure correct taskbar icon
    try:
        import ctypes
        myappid = 'pjames.smart_file_organizer.gui.1.0' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
        # High-DPI Awareness (Fixes blurry GUI)
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
            
    except Exception:
        pass

    root = tk.Tk()
    
    # Set icon if available
    # The icon setting logic is now handled by the set_icon method within the class.
    
    app = SFOFileOrganizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
