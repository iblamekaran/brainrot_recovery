"""
Brainrot Recovery - Desktop Dashboard UI
A modern, purple-themed desktop application for tracking Core Java & JDBC progress.
"""

import os
import sys
import datetime
from pathlib import Path

# Expose Flask web app for WSGI servers (e.g. Render default 'gunicorn app:app')
from server import app

# Import database and export logic from tracker.py
import tracker

# Safe import for Tkinter (headless cloud environments like Render don't have _tkinter)
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    from PIL import Image, ImageTk
    HAS_TKINTER = True
except (ImportError, ModuleNotFoundError):
    HAS_TKINTER = False
    tk = None


class DarkTheme:
    """Dark Purple Workspace Theme."""
    NAME = "dark"
    BG_DARK = "#0F0E17"          # Deep obsidian background
    BG_TOP = "#161326"           # Header top bar background
    BG_CARD = "#1C1833"          # Card and container background
    BG_CARD_LIGHT = "#241F42"    # Slightly lighter container
    BG_INPUT = "#2B254E"         # Input fields & text areas
    BORDER = "#3B3466"           # Card and divider borders

    PURPLE_PRIMARY = "#7C3AED"   # Vibrant accent purple
    PURPLE_HOVER = "#6D28D9"     # Darker purple hover
    PURPLE_LIGHT = "#A78BFA"     # Lavender text accent
    PURPLE_GLOW = "#DDD6FE"      # Very light purple highlight

    COLOR_COVERED = "#10B981"    # Emerald green
    COLOR_IN_PROGRESS = "#F59E0B"# Amber / Orange
    COLOR_REVISION = "#EC4899"   # Rose / Magenta
    COLOR_NOT_STARTED = "#94A3B8"# Slate gray

    TEXT_WHITE = "#FFFFFF"       # Main crisp text
    TEXT_LIGHT = "#E2E8F0"       # Normal body text
    TEXT_MUTED = "#94A3B8"       # Subtle / placeholder text
    TEXT_LAVENDER = "#C4B5FD"    # Highlight label text

    FONT_FAMILY = "Segoe UI"


class LightTheme:
    """Clean Light Violet Workspace Theme."""
    NAME = "light"
    BG_DARK = "#F8FAFC"          # Clean light slate background
    BG_TOP = "#FFFFFF"           # Header top bar background
    BG_CARD = "#FFFFFF"          # Card and container background
    BG_CARD_LIGHT = "#EDE9FE"    # Soft lavender container
    BG_INPUT = "#F1F5F9"         # Input fields & text areas
    BORDER = "#CBD5E1"           # Light slate borders

    PURPLE_PRIMARY = "#7C3AED"   # Vibrant accent purple
    PURPLE_HOVER = "#6D28D9"     # Darker purple hover
    PURPLE_LIGHT = "#7C3AED"     # Purple text accent
    PURPLE_GLOW = "#6D28D9"      # Purple highlight

    COLOR_COVERED = "#059669"    # Emerald dark
    COLOR_IN_PROGRESS = "#D97706"# Amber dark
    COLOR_REVISION = "#DB2777"   # Rose dark
    COLOR_NOT_STARTED = "#64748B"# Slate dark

    TEXT_WHITE = "#0F172A"       # Main deep dark text
    TEXT_LIGHT = "#1E293B"       # Normal body text
    TEXT_MUTED = "#64748B"       # Subtle / placeholder text
    TEXT_LAVENDER = "#7C3AED"    # Highlight label text

    FONT_FAMILY = "Segoe UI"


class ActiveTheme:
    """Dynamic theme proxy that delegates attributes to DarkTheme or LightTheme."""
    _theme = DarkTheme

    @classmethod
    def set_theme(cls, theme_cls):
        cls._theme = theme_cls
        for attr in dir(theme_cls):
            if not attr.startswith("_"):
                setattr(cls, attr, getattr(theme_cls, attr))


ActiveTheme.set_theme(DarkTheme)
PurpleTheme = ActiveTheme


class BrainrotRecoveryDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Brainrot Recovery — Focus & Progress Tracker")
        self.root.geometry("1260x800")
        self.root.minsize(1040, 680)
        self.root.configure(bg=PurpleTheme.BG_DARK)

        # Initialize backend DB
        tracker.init_db()
        tracker.ensure_data_loaded()

        # Load Logo and Window Icon
        self._load_app_icon()

        # State variables
        self.current_topic_id = None
        self.search_var = tk.StringVar()
        self.status_filter_var = tk.StringVar(value="All Statuses")
        self.tech_filter_var = tk.StringVar(value="All Technologies")

        # Edit variables
        self.edit_status_var = tk.StringVar(value="Not Started")
        self.edit_date_var = tk.StringVar()

        self._configure_styles()
        self._build_ui()
        self._load_dashboard_metrics()
        self._populate_table()

        # Auto-select the first topic if available
        first_item = self.tree.get_children()
        if first_item:
            self.tree.selection_set(first_item[0])
            self.tree.focus(first_item[0])
            self._on_table_select(None)

    def _load_app_icon(self):
        """Loads and sets the Brainrot Recovery logo for window icon and header."""
        logo_path = Path("static/logo.png")
        self.header_logo_photo = None
        self.window_icon_photo = None

        if logo_path.exists():
            try:
                pil_img = Image.open(logo_path)
                # Window icon
                icon_img = pil_img.resize((64, 64), Image.Resampling.LANCZOS)
                self.window_icon_photo = ImageTk.PhotoImage(icon_img)
                self.root.iconphoto(False, self.window_icon_photo)

                # Header logo
                header_img = pil_img.resize((42, 42), Image.Resampling.LANCZOS)
                self.header_logo_photo = ImageTk.PhotoImage(header_img)
            except Exception as e:
                print(f"[!] Note: Could not load logo image: {e}")

    def _configure_styles(self):
        """Configures ttk styles for treeview, scrollbars, and comboboxes."""
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        # Treeview styling
        self.style.configure(
            "Custom.Treeview",
            background=PurpleTheme.BG_CARD,
            foreground=PurpleTheme.TEXT_LIGHT,
            fieldbackground=PurpleTheme.BG_CARD,
            rowheight=32,
            font=(PurpleTheme.FONT_FAMILY, 9),
            borderwidth=0
        )
        self.style.configure(
            "Custom.Treeview.Heading",
            background=PurpleTheme.BG_CARD_LIGHT,
            foreground=PurpleTheme.PURPLE_LIGHT,
            font=(PurpleTheme.FONT_FAMILY, 9, "bold"),
            relief="flat",
            padding=6
        )
        self.style.map(
            "Custom.Treeview",
            background=[("selected", PurpleTheme.PURPLE_PRIMARY)],
            foreground=[("selected", PurpleTheme.TEXT_WHITE)]
        )
        self.style.map(
            "Custom.Treeview.Heading",
            background=[("active", PurpleTheme.PURPLE_PRIMARY)]
        )

        # Combobox styling
        self.style.configure(
            "Purple.TCombobox",
            fieldbackground=PurpleTheme.BG_INPUT,
            background=PurpleTheme.BG_CARD_LIGHT,
            foreground=PurpleTheme.TEXT_WHITE,
            darkcolor=PurpleTheme.BORDER,
            lightcolor=PurpleTheme.BORDER,
            arrowcolor=PurpleTheme.PURPLE_LIGHT,
            font=(PurpleTheme.FONT_FAMILY, 9)
        )
        self.style.map(
            "Purple.TCombobox",
            fieldbackground=[("readonly", PurpleTheme.BG_INPUT)],
            foreground=[("readonly", PurpleTheme.TEXT_WHITE)],
            selectbackground=[("readonly", PurpleTheme.PURPLE_PRIMARY)],
            selectforeground=[("readonly", PurpleTheme.TEXT_WHITE)]
        )

        # Progress bar styling
        self.style.configure(
            "Purple.Horizontal.TProgressbar",
            troughcolor=PurpleTheme.BG_CARD_LIGHT,
            background=PurpleTheme.PURPLE_PRIMARY,
            bordercolor=PurpleTheme.BG_CARD_LIGHT,
            lightcolor=PurpleTheme.PURPLE_PRIMARY,
            darkcolor=PurpleTheme.PURPLE_PRIMARY,
            thickness=10
        )

    def _build_ui(self):
        """Constructs the layout: Header, Metric Cards, and Split Workspace."""
        # Top Bar Container
        self.top_frame = tk.Frame(self.root, bg=PurpleTheme.BG_TOP, height=75)
        self.top_frame.pack(fill=tk.X, side=tk.TOP)
        self.top_frame.pack_propagate(False)

        # App Brand Box with Logo + Title
        brand_box = tk.Frame(self.top_frame, bg=PurpleTheme.BG_TOP)
        brand_box.pack(side=tk.LEFT, padx=20, pady=12)

        # Display Logo Image if loaded
        if self.header_logo_photo:
            logo_lbl = tk.Label(brand_box, image=self.header_logo_photo, bg=PurpleTheme.BG_TOP)
            logo_lbl.pack(side=tk.LEFT, padx=(0, 12))

        title_text_box = tk.Frame(brand_box, bg=PurpleTheme.BG_TOP)
        title_text_box.pack(side=tk.LEFT)

        title_lbl = tk.Label(
            title_text_box,
            text="BRAINROT RECOVERY",
            font=(PurpleTheme.FONT_FAMILY, 15, "bold"),
            fg=PurpleTheme.TEXT_WHITE,
            bg=PurpleTheme.BG_TOP
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = tk.Label(
            title_text_box,
            text="Reclaim Your Focus · Core Java & JDBC Curriculum · SQLite & Excel Sync",
            font=(PurpleTheme.FONT_FAMILY, 9),
            fg=PurpleTheme.PURPLE_LIGHT,
            bg=PurpleTheme.BG_TOP
        )
        subtitle_lbl.pack(anchor=tk.W)

        # Top Right Controls: Theme Toggle & Progress
        self.top_right_frame = tk.Frame(self.top_frame, bg=PurpleTheme.BG_TOP)
        self.top_right_frame.pack(side=tk.RIGHT, padx=24, pady=10)

        top_right_header = tk.Frame(self.top_right_frame, bg=PurpleTheme.BG_TOP)
        top_right_header.pack(anchor=tk.E, pady=(0, 4))

        self.overall_pct_lbl = tk.Label(
            top_right_header,
            text="0.0% Completed",
            font=(PurpleTheme.FONT_FAMILY, 11, "bold"),
            fg=PurpleTheme.COLOR_COVERED,
            bg=PurpleTheme.BG_TOP
        )
        self.overall_pct_lbl.pack(side=tk.LEFT)

        theme_btn_text = "☀️ Light Mode" if ActiveTheme._theme == DarkTheme else "🌙 Dark Mode"
        self.btn_theme_toggle = tk.Button(
            top_right_header,
            text=theme_btn_text,
            bg=PurpleTheme.BG_INPUT,
            fg=PurpleTheme.PURPLE_LIGHT,
            activebackground=PurpleTheme.BORDER,
            activeforeground=PurpleTheme.TEXT_WHITE,
            font=(PurpleTheme.FONT_FAMILY, 8, "bold"),
            relief="flat",
            cursor="hand2",
            padx=9,
            pady=2,
            command=self.toggle_theme
        )
        self.btn_theme_toggle.pack(side=tk.LEFT, padx=(10, 0))

        self.top_progressbar = ttk.Progressbar(
            self.top_right_frame,
            style="Purple.Horizontal.TProgressbar",
            orient="horizontal",
            length=240,
            mode="determinate"
        )
        self.top_progressbar.pack(anchor=tk.E)

        # ----------------- FOUR METRIC CARDS -----------------
        self.cards_frame = tk.Frame(self.root, bg=PurpleTheme.BG_DARK)
        self.cards_frame.pack(fill=tk.X, padx=20, pady=(16, 12))

        for col_idx in range(4):
            self.cards_frame.columnconfigure(col_idx, weight=1, uniform="metric_cards")

        # 1. Total Topics
        self.card_total_val, self.card_total_sub = self._create_metric_card(
            self.cards_frame, 0, "TOTAL TOPICS", "65", "Curriculum Roadmap", PurpleTheme.PURPLE_LIGHT
        )
        # 2. Covered
        self.card_covered_val, self.card_covered_sub = self._create_metric_card(
            self.cards_frame, 1, "COVERED", "0", "0.0% of total", PurpleTheme.COLOR_COVERED
        )
        # 3. In Progress
        self.card_inprog_val, self.card_inprog_sub = self._create_metric_card(
            self.cards_frame, 2, "IN PROGRESS", "0", "Currently studying", PurpleTheme.COLOR_IN_PROGRESS
        )
        # 4. Needs Revision
        self.card_rev_val, self.card_rev_sub = self._create_metric_card(
            self.cards_frame, 3, "NEEDS REVISION", "0", "Topics to revisit", PurpleTheme.COLOR_REVISION
        )

        # ----------------- MAIN BODY (SPLIT PANELS) -----------------
        self.body_frame = tk.Frame(self.root, bg=PurpleTheme.BG_DARK)
        self.body_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 16))

        # Left Panel (Table + Search + Filters)
        self.left_panel = tk.Frame(self.body_frame, bg=PurpleTheme.BG_CARD, bd=1, relief="solid")
        self.left_panel.configure(highlightbackground=PurpleTheme.BORDER, highlightthickness=1)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Right Panel (Topic Details & Editor)
        self.right_panel = tk.Frame(self.body_frame, bg=PurpleTheme.BG_CARD, width=420, bd=1, relief="solid")
        self.right_panel.configure(highlightbackground=PurpleTheme.BORDER, highlightthickness=1)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(0, 0))
        self.right_panel.pack_propagate(False)

        self._build_left_panel()
        self._build_right_panel()

    def _create_metric_card(self, parent, col, title, value, subtitle, accent_color):
        """Creates a modern rounded card widget for metrics."""
        card = tk.Frame(
            parent,
            bg=PurpleTheme.BG_CARD,
            bd=0,
            highlightbackground=PurpleTheme.BORDER,
            highlightthickness=1
        )
        card.grid(row=0, column=col, padx=6, sticky="nsew")

        # Top accent color bar
        accent_bar = tk.Frame(card, bg=accent_color, height=4)
        accent_bar.pack(fill=tk.X, side=tk.TOP)

        content = tk.Frame(card, bg=PurpleTheme.BG_CARD, padx=14, pady=10)
        content.pack(fill=tk.BOTH, expand=True)

        lbl_title = tk.Label(
            content,
            text=title,
            font=(PurpleTheme.FONT_FAMILY, 8, "bold"),
            fg=PurpleTheme.TEXT_MUTED,
            bg=PurpleTheme.BG_CARD
        )
        lbl_title.pack(anchor=tk.W)

        lbl_value = tk.Label(
            content,
            text=value,
            font=(PurpleTheme.FONT_FAMILY, 18, "bold"),
            fg=PurpleTheme.TEXT_WHITE,
            bg=PurpleTheme.BG_CARD
        )
        lbl_value.pack(anchor=tk.W, pady=(2, 0))

        lbl_sub = tk.Label(
            content,
            text=subtitle,
            font=(PurpleTheme.FONT_FAMILY, 8),
            fg=accent_color,
            bg=PurpleTheme.BG_CARD
        )
        lbl_sub.pack(anchor=tk.W)

        return lbl_value, lbl_sub

    def _build_left_panel(self):
        """Constructs the search, filters, and topic treeview."""
        # Filter & Search Bar
        filter_bar = tk.Frame(self.left_panel, bg=PurpleTheme.BG_CARD_LIGHT, padx=12, pady=10)
        filter_bar.pack(fill=tk.X, side=tk.TOP)

        # Search Entry
        search_box = tk.Frame(filter_bar, bg=PurpleTheme.BG_INPUT, bd=1, relief="solid")
        search_box.configure(highlightbackground=PurpleTheme.BORDER, highlightthickness=1)
        search_box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        search_icon = tk.Label(
            search_box,
            text=" 🔍 ",
            bg=PurpleTheme.BG_INPUT,
            fg=PurpleTheme.PURPLE_LIGHT,
            font=(PurpleTheme.FONT_FAMILY, 9)
        )
        search_icon.pack(side=tk.LEFT)

        self.search_entry = tk.Entry(
            search_box,
            textvariable=self.search_var,
            bg=PurpleTheme.BG_INPUT,
            fg=PurpleTheme.TEXT_WHITE,
            insertbackground=PurpleTheme.TEXT_WHITE,
            relief="flat",
            font=(PurpleTheme.FONT_FAMILY, 9)
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.search_var.trace_add("write", lambda *args: self._populate_table())

        # Status Filter Combobox
        status_cb = ttk.Combobox(
            filter_bar,
            textvariable=self.status_filter_var,
            values=["All Statuses", "Not Started", "In Progress", "Covered", "Needs Revision"],
            state="readonly",
            style="Purple.TCombobox",
            width=14
        )
        status_cb.pack(side=tk.LEFT, padx=(0, 6))
        status_cb.bind("<<ComboboxSelected>>", lambda e: self._populate_table())

        # Technology Filter Combobox
        tech_cb = ttk.Combobox(
            filter_bar,
            textvariable=self.tech_filter_var,
            values=["All Technologies", "Core Java", "JDBC"],
            state="readonly",
            style="Purple.TCombobox",
            width=15
        )
        tech_cb.pack(side=tk.LEFT, padx=(0, 6))
        tech_cb.bind("<<ComboboxSelected>>", lambda e: self._populate_table())

        # Reset button
        btn_reset = tk.Button(
            filter_bar,
            text="✕ Reset",
            bg=PurpleTheme.BG_INPUT,
            fg=PurpleTheme.PURPLE_LIGHT,
            activebackground=PurpleTheme.BORDER,
            activeforeground=PurpleTheme.TEXT_WHITE,
            font=(PurpleTheme.FONT_FAMILY, 8, "bold"),
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=3,
            command=self._reset_filters
        )
        btn_reset.pack(side=tk.LEFT)

        # Topic Treeview Table
        table_container = tk.Frame(self.left_panel, bg=PurpleTheme.BG_CARD)
        table_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        columns = ("id", "tech", "section", "topic", "priority", "status", "date")
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            style="Custom.Treeview",
            selectmode="browse"
        )

        # Headings & Column formatting
        self.tree.heading("id", text="#", anchor=tk.CENTER)
        self.tree.heading("tech", text="Tech", anchor=tk.W)
        self.tree.heading("section", text="Section", anchor=tk.W)
        self.tree.heading("topic", text="Topic Name", anchor=tk.W)
        self.tree.heading("priority", text="Priority", anchor=tk.CENTER)
        self.tree.heading("status", text="Status", anchor=tk.CENTER)
        self.tree.heading("date", text="Date Covered", anchor=tk.CENTER)

        self.tree.column("id", width=38, minwidth=35, anchor=tk.CENTER)
        self.tree.column("tech", width=80, minwidth=70, anchor=tk.W)
        self.tree.column("section", width=170, minwidth=140, anchor=tk.W)
        self.tree.column("topic", width=190, minwidth=150, anchor=tk.W)
        self.tree.column("priority", width=70, minwidth=60, anchor=tk.CENTER)
        self.tree.column("status", width=105, minwidth=90, anchor=tk.CENTER)
        self.tree.column("date", width=90, minwidth=80, anchor=tk.CENTER)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_table_select)
        self.tree.bind("<KeyRelease-Up>", self._on_table_select)
        self.tree.bind("<KeyRelease-Down>", self._on_table_select)

        # Tags for colored row statuses
        self.tree.tag_configure("Covered", foreground=PurpleTheme.COLOR_COVERED)
        self.tree.tag_configure("In Progress", foreground=PurpleTheme.COLOR_IN_PROGRESS)
        self.tree.tag_configure("Needs Revision", foreground=PurpleTheme.COLOR_REVISION)
        self.tree.tag_configure("Not Started", foreground=PurpleTheme.COLOR_NOT_STARTED)

        # Footer Status
        self.table_footer = tk.Label(
            self.left_panel,
            text="Showing 65 of 65 topics",
            font=(PurpleTheme.FONT_FAMILY, 8),
            fg=PurpleTheme.TEXT_MUTED,
            bg=PurpleTheme.BG_CARD,
            anchor=tk.W,
            padx=12,
            pady=4
        )
        self.table_footer.pack(fill=tk.X, side=tk.BOTTOM)

    def _build_right_panel(self):
        """Constructs the Topic Details panel on the right side."""
        # Top Header of Right Panel
        header = tk.Frame(self.right_panel, bg=PurpleTheme.BG_CARD_LIGHT, padx=16, pady=12)
        header.pack(fill=tk.X)

        self.detail_id_lbl = tk.Label(
            header,
            text="TOPIC DETAILS",
            font=(PurpleTheme.FONT_FAMILY, 8, "bold"),
            fg=PurpleTheme.PURPLE_LIGHT,
            bg=PurpleTheme.BG_CARD_LIGHT
        )
        self.detail_id_lbl.pack(anchor=tk.W)

        self.detail_title_lbl = tk.Label(
            header,
            text="Select a topic from the table",
            font=(PurpleTheme.FONT_FAMILY, 12, "bold"),
            fg=PurpleTheme.TEXT_WHITE,
            bg=PurpleTheme.BG_CARD_LIGHT,
            wraplength=380,
            justify=tk.LEFT
        )
        self.detail_title_lbl.pack(anchor=tk.W, pady=(2, 4))

        # Badges Frame
        self.badges_frame = tk.Frame(header, bg=PurpleTheme.BG_CARD_LIGHT)
        self.badges_frame.pack(anchor=tk.W, fill=tk.X, pady=(2, 0))

        self.badge_tech = self._create_badge(self.badges_frame, "Core Java", PurpleTheme.PURPLE_PRIMARY)
        self.badge_priority = self._create_badge(self.badges_frame, "Core", PurpleTheme.BG_INPUT)

        # Details Content
        content_frame = tk.Frame(self.right_panel, bg=PurpleTheme.BG_CARD, padx=16, pady=12)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Section
        tk.Label(
            content_frame,
            text="CURRICULUM SECTION",
            font=(PurpleTheme.FONT_FAMILY, 8, "bold"),
            fg=PurpleTheme.TEXT_MUTED,
            bg=PurpleTheme.BG_CARD
        ).pack(anchor=tk.W)

        self.section_val_lbl = tk.Label(
            content_frame,
            text="—",
            font=(PurpleTheme.FONT_FAMILY, 9),
            fg=PurpleTheme.PURPLE_GLOW,
            bg=PurpleTheme.BG_CARD,
            wraplength=380,
            justify=tk.LEFT
        )
        self.section_val_lbl.pack(anchor=tk.W, pady=(2, 10))

        # Subtopics / Concepts Box
        tk.Label(
            content_frame,
            text="SUBTOPICS & CONCEPTS",
            font=(PurpleTheme.FONT_FAMILY, 8, "bold"),
            fg=PurpleTheme.TEXT_MUTED,
            bg=PurpleTheme.BG_CARD
        ).pack(anchor=tk.W)

        self.subtopics_box = tk.Label(
            content_frame,
            text="—",
            font=(PurpleTheme.FONT_FAMILY, 9),
            fg=PurpleTheme.TEXT_LIGHT,
            bg=PurpleTheme.BG_INPUT,
            padx=10,
            pady=6,
            relief="flat",
            wraplength=360,
            justify=tk.LEFT,
            anchor=tk.W
        )
        self.subtopics_box.pack(fill=tk.X, pady=(2, 10))

        # Application Box
        tk.Label(
            content_frame,
            text="PRACTICAL APPLICATION",
            font=(PurpleTheme.FONT_FAMILY, 8, "bold"),
            fg=PurpleTheme.TEXT_MUTED,
            bg=PurpleTheme.BG_CARD
        ).pack(anchor=tk.W)

        self.app_box = tk.Label(
            content_frame,
            text="—",
            font=(PurpleTheme.FONT_FAMILY, 9),
            fg=PurpleTheme.TEXT_LIGHT,
            bg=PurpleTheme.BG_INPUT,
            padx=10,
            pady=6,
            relief="flat",
            wraplength=360,
            justify=tk.LEFT,
            anchor=tk.W
        )
        self.app_box.pack(fill=tk.X, pady=(2, 12))

        # Divider
        divider = tk.Frame(content_frame, bg=PurpleTheme.BORDER, height=1)
        divider.pack(fill=tk.X, pady=(0, 10))

        # Status Selector Dropdown
        status_row = tk.Frame(content_frame, bg=PurpleTheme.BG_CARD)
        status_row.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            status_row,
            text="Status:",
            font=(PurpleTheme.FONT_FAMILY, 9, "bold"),
            fg=PurpleTheme.TEXT_WHITE,
            bg=PurpleTheme.BG_CARD,
            width=12,
            anchor=tk.W
        ).pack(side=tk.LEFT)

        self.status_dropdown = ttk.Combobox(
            status_row,
            textvariable=self.edit_status_var,
            values=["Not Started", "In Progress", "Covered", "Needs Revision"],
            state="readonly",
            style="Purple.TCombobox"
        )
        self.status_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_dropdown.bind("<<ComboboxSelected>>", self._on_status_change)

        # Date Covered Entry + Today Button
        date_row = tk.Frame(content_frame, bg=PurpleTheme.BG_CARD)
        date_row.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            date_row,
            text="Date Covered:",
            font=(PurpleTheme.FONT_FAMILY, 9, "bold"),
            fg=PurpleTheme.TEXT_WHITE,
            bg=PurpleTheme.BG_CARD,
            width=12,
            anchor=tk.W
        ).pack(side=tk.LEFT)

        self.date_entry = tk.Entry(
            date_row,
            textvariable=self.edit_date_var,
            bg=PurpleTheme.BG_INPUT,
            fg=PurpleTheme.TEXT_WHITE,
            insertbackground=PurpleTheme.TEXT_WHITE,
            relief="flat",
            font=(PurpleTheme.FONT_FAMILY, 9),
            highlightbackground=PurpleTheme.BORDER,
            highlightthickness=1
        )
        self.date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6), ipady=3)

        btn_today = tk.Button(
            date_row,
            text="📅 Today",
            bg=PurpleTheme.BG_INPUT,
            fg=PurpleTheme.PURPLE_LIGHT,
            activebackground=PurpleTheme.BORDER,
            activeforeground=PurpleTheme.TEXT_WHITE,
            font=(PurpleTheme.FONT_FAMILY, 8, "bold"),
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=2,
            command=self._set_today_date
        )
        btn_today.pack(side=tk.RIGHT)

        # Practice Notes Field
        tk.Label(
            content_frame,
            text="Practice / Study Notes:",
            font=(PurpleTheme.FONT_FAMILY, 9, "bold"),
            fg=PurpleTheme.TEXT_WHITE,
            bg=PurpleTheme.BG_CARD
        ).pack(anchor=tk.W, pady=(2, 4))

        notes_box = tk.Frame(content_frame, bg=PurpleTheme.BG_INPUT, bd=1, relief="solid")
        notes_box.configure(highlightbackground=PurpleTheme.BORDER, highlightthickness=1)
        notes_box.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.notes_text = tk.Text(
            notes_box,
            bg=PurpleTheme.BG_INPUT,
            fg=PurpleTheme.TEXT_WHITE,
            insertbackground=PurpleTheme.TEXT_WHITE,
            relief="flat",
            font=(PurpleTheme.FONT_FAMILY, 9),
            wrap=tk.WORD,
            height=4
        )
        self.notes_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Action Buttons
        btn_row = tk.Frame(content_frame, bg=PurpleTheme.BG_CARD)
        btn_row.pack(fill=tk.X, pady=(0, 4))

        self.btn_save = tk.Button(
            btn_row,
            text="💾 Save Progress",
            bg=PurpleTheme.PURPLE_PRIMARY,
            fg=PurpleTheme.TEXT_WHITE,
            activebackground=PurpleTheme.PURPLE_HOVER,
            activeforeground=PurpleTheme.TEXT_WHITE,
            font=(PurpleTheme.FONT_FAMILY, 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=7,
            command=self._save_current_topic
        )
        self.btn_save.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        self.btn_export = tk.Button(
            btn_row,
            text="📊 Export Excel",
            bg="#059669",
            fg=PurpleTheme.TEXT_WHITE,
            activebackground="#047857",
            activeforeground=PurpleTheme.TEXT_WHITE,
            font=(PurpleTheme.FONT_FAMILY, 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=7,
            command=self._export_to_excel
        )
        self.btn_export.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Feedback Toast Label
        self.toast_lbl = tk.Label(
            content_frame,
            text="",
            font=(PurpleTheme.FONT_FAMILY, 9, "bold"),
            fg=PurpleTheme.COLOR_COVERED,
            bg=PurpleTheme.BG_CARD
        )
        self.toast_lbl.pack(fill=tk.X, pady=(4, 0))

    def _create_badge(self, parent, text, bg_color):
        lbl = tk.Label(
            parent,
            text=f" {text} ",
            bg=bg_color,
            fg=PurpleTheme.TEXT_WHITE,
            font=(PurpleTheme.FONT_FAMILY, 8, "bold"),
            padx=6,
            pady=1
        )
        lbl.pack(side=tk.LEFT, padx=(0, 6))
        return lbl

    def _set_today_date(self):
        """Fills date covered with today's YYYY-MM-DD."""
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        self.edit_date_var.set(today_str)

    def _on_status_change(self, event=None):
        """Auto-fills date covered if status changed to Covered and date is empty."""
        if self.edit_status_var.get() == "Covered" and not self.edit_date_var.get().strip():
            self._set_today_date()

    def _show_toast(self, message, is_error=False):
        """Displays temporary notification message."""
        self.toast_lbl.config(
            text=message,
            fg=PurpleTheme.COLOR_REVISION if is_error else PurpleTheme.COLOR_COVERED
        )
        self.root.after(3500, lambda: self.toast_lbl.config(text=""))

    def toggle_theme(self):
        """Switches between Dark Mode and Light Mode."""
        if ActiveTheme._theme == DarkTheme:
            ActiveTheme.set_theme(LightTheme)
        else:
            ActiveTheme.set_theme(DarkTheme)

        self.root.configure(bg=PurpleTheme.BG_DARK)
        # Destroy current container frames
        for widget in [self.top_frame, self.cards_frame, self.body_frame]:
            widget.destroy()

        # Re-apply styles and rebuild UI
        self._configure_styles()
        self._build_ui()
        self._load_dashboard_metrics()
        self._populate_table()

    def _reset_filters(self):
        """Clears search and dropdown filters."""
        self.search_var.set("")
        self.status_filter_var.set("All Statuses")
        self.tech_filter_var.set("All Technologies")
        self._populate_table()

    def _load_dashboard_metrics(self):
        """Updates the 4 top cards and overall progress bar."""
        with tracker.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM topics")
            total = cursor.fetchone()["total"]

            cursor.execute("SELECT status, COUNT(*) AS cnt FROM topics GROUP BY status")
            counts = {row["status"]: row["cnt"] for row in cursor.fetchall()}

        covered = counts.get("Covered", 0)
        in_progress = counts.get("In Progress", 0)
        revision = counts.get("Needs Revision", 0)
        not_started = counts.get("Not Started", 0)

        pct_covered = (covered / total * 100) if total > 0 else 0

        # Update Top Bar
        self.overall_pct_lbl.config(text=f"{pct_covered:.1f}% Completed")
        self.top_progressbar["value"] = pct_covered

        # Update 4 Cards
        self.card_total_val.config(text=str(total))
        self.card_total_sub.config(text="65 Topics Curriculum")

        self.card_covered_val.config(text=str(covered))
        self.card_covered_sub.config(text=f"{pct_covered:.1f}% of curriculum")

        self.card_inprog_val.config(text=str(in_progress))
        pct_inprog = (in_progress / total * 100) if total > 0 else 0
        self.card_inprog_sub.config(text=f"{pct_inprog:.1f}% currently studying")

        self.card_rev_val.config(text=str(revision))
        self.card_rev_sub.config(text=f"{not_started} not started")

    def _populate_table(self):
        """Queries database with current filters and populates the Treeview."""
        query_sql = "SELECT id, technology, section, topic, priority, status, date_covered FROM topics WHERE 1=1"
        params = []

        # Filter by search text
        search_text = self.search_var.get().strip()
        if search_text:
            query_sql += """
                AND (
                    topic LIKE ?
                    OR subtopics LIKE ?
                    OR section LIKE ?
                    OR practice_notes LIKE ?
                )
            """
            p = f"%{search_text}%"
            params.extend([p, p, p, p])

        # Filter by status
        selected_status = self.status_filter_var.get()
        if selected_status and selected_status != "All Statuses":
            query_sql += " AND status = ?"
            params.append(selected_status)

        # Filter by technology
        selected_tech = self.tech_filter_var.get()
        if selected_tech and selected_tech != "All Technologies":
            query_sql += " AND technology = ?"
            params.append(selected_tech)

        query_sql += " ORDER BY id ASC"

        with tracker.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query_sql, params)
            rows = cursor.fetchall()

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in rows:
            status = row["status"]
            date_val = row["date_covered"] or "—"
            self.tree.insert(
                "",
                tk.END,
                iid=str(row["id"]),
                values=(
                    row["id"],
                    row["technology"],
                    row["section"],
                    row["topic"],
                    row["priority"],
                    status,
                    date_val
                ),
                tags=(status,)
            )

        self.table_footer.config(text=f"Showing {len(rows)} of 65 topics")

        # Keep current selection if still in filtered list
        if self.current_topic_id and self.tree.exists(str(self.current_topic_id)):
            self.tree.selection_set(str(self.current_topic_id))
            self.tree.see(str(self.current_topic_id))

    def _on_table_select(self, event):
        """Triggered when a user selects a topic in the table."""
        selected = self.tree.selection()
        if not selected:
            return

        topic_id = int(selected[0])
        self.current_topic_id = topic_id

        with tracker.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM topics WHERE id = ?", (topic_id,))
            topic = cursor.fetchone()

        if not topic:
            return

        # Populate Right Panel
        self.detail_id_lbl.config(text=f"TOPIC #{topic['id']} · {topic['technology'].upper()}")
        self.detail_title_lbl.config(text=topic["topic"])
        self.section_val_lbl.config(text=f"{topic['section']}")

        self.badge_tech.config(text=f" {topic['technology']} ")
        self.badge_priority.config(text=f" Priority: {topic['priority']} ")

        self.subtopics_box.config(text=topic["subtopics"] or "No subtopics specified.")
        self.app_box.config(text=topic["vyavastha_app"] or "Core programming concept.")

        self.edit_status_var.set(topic["status"])
        self.edit_date_var.set(topic["date_covered"] or "")

        self.notes_text.delete("1.0", tk.END)
        if topic["practice_notes"]:
            self.notes_text.insert("1.0", topic["practice_notes"])

    def _save_current_topic(self):
        """Saves status, date covered, and notes for the active topic."""
        if not self.current_topic_id:
            messagebox.showinfo("Select Topic", "Please select a topic from the table first.")
            return

        new_status = self.edit_status_var.get()
        new_date = self.edit_date_var.get().strip() or None
        new_notes = self.notes_text.get("1.0", tk.END).strip() or None

        with tracker.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE topics
                SET status = ?, date_covered = ?, practice_notes = ?
                WHERE id = ?
            """, (new_status, new_date, new_notes, self.current_topic_id))
            conn.commit()

        # Update row in treeview directly
        if self.tree.exists(str(self.current_topic_id)):
            current_vals = list(self.tree.item(str(self.current_topic_id), "values"))
            current_vals[5] = new_status
            current_vals[6] = new_date or "—"
            self.tree.item(str(self.current_topic_id), values=current_vals, tags=(new_status,))

        # Refresh metrics
        self._load_dashboard_metrics()
        self._show_toast(f"✓ Topic #{self.current_topic_id} updated successfully!")

    def _export_to_excel(self):
        """Exports SQLite database back to the Excel workbook."""
        try:
            tracker.export_progress_to_excel()
            self._show_toast("✓ Progress exported to Excel workbook!")
            messagebox.showinfo(
                "Export Complete",
                "Your progress has been successfully synchronized to:\n\n"
                f"{tracker.EXCEL_FILE.resolve()}\n\n"
                "The Progress Tracker sheet and formulas in Summary sheet are now up to date."
            )
        except Exception as e:
            self._show_toast(f"Export failed: {e}", is_error=True)
            messagebox.showerror("Export Error", f"Failed to export to Excel:\n{e}")


def main():
    if not HAS_TKINTER:
        print("[!] Tkinter is not installed on this system. Starting web server instead...")
        from server import run_mobile_server
        run_mobile_server()
        return

    root = tk.Tk()
    dashboard = BrainrotRecoveryDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
