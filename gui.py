"""
GUI implementation for the XML Viewer & WYSIWYG Editor using Tkinter.
Features:
- Dual-mode: Visual WYSIWYG Tree + Inspector, and Syntax-Highlighted XML Source Code.
- Bidirectional synchronization between visual and source views.
- Node inspector with tag renaming, multi-line text editor, and attributes table.
- Search and highlight in tree and source code.
- XML validation and prettification.
- Full node CRUD (Add child/sibling, delete, duplicate, move up/down).
"""

import os
import sys
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Optional, Dict

from xml_model import XMLModel


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for development and PyInstaller bundled exe."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))

    # Check inside bundle/source directory
    path1 = os.path.join(base_path, relative_path)
    if os.path.exists(path1):
        return path1

    # Also check next to executable in case of external assets
    exe_dir = os.path.dirname(sys.executable)
    path2 = os.path.join(exe_dir, relative_path)
    if os.path.exists(path2):
        return path2

    return path1



class AddNodeDialog(tk.Toplevel):
    """Dialog to create a new XML element."""
    def __init__(self, parent, title="Add Element", default_tag="item"):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None

        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding="16")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Tag Name:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.tag_var = tk.StringVar(value=default_tag)
        self.tag_entry = ttk.Entry(frame, textvariable=self.tag_var, width=32)
        self.tag_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.tag_entry.select_range(0, tk.END)

        ttk.Label(frame, text="Text Content (optional):", font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.text_var = tk.StringVar(value="")
        self.text_entry = ttk.Entry(frame, textvariable=self.text_var, width=32)
        self.text_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        ttk.Label(frame, text="Attribute Name (optional):", font=("Segoe UI", 9)).grid(row=4, column=0, sticky="w", pady=(0, 4))
        self.attr_name_var = tk.StringVar()
        self.attr_name_entry = ttk.Entry(frame, textvariable=self.attr_name_var, width=15)
        self.attr_name_entry.grid(row=5, column=0, sticky="w", pady=(0, 16))

        ttk.Label(frame, text="Value:", font=("Segoe UI", 9)).grid(row=4, column=1, sticky="w", pady=(0, 4))
        self.attr_val_var = tk.StringVar()
        self.attr_val_entry = ttk.Entry(frame, textvariable=self.attr_val_var, width=15)
        self.attr_val_entry.grid(row=5, column=1, sticky="w", pady=(0, 16))

        btn_box = ttk.Frame(frame)
        btn_box.grid(row=6, column=0, columnspan=2, sticky="e")
        ttk.Button(btn_box, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(btn_box, text="Add Element", command=self._on_ok).pack(side=tk.RIGHT)

        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self.destroy())

        self.geometry("+%d+%d" % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 100))
        self.tag_entry.focus_set()
        self.wait_window(self)

    def _on_ok(self):
        tag = self.tag_var.get().strip()
        if not tag:
            messagebox.showwarning("Validation Error", "Tag name is required.", parent=self)
            self.tag_entry.focus_set()
            return

        attrib = {}
        aname = self.attr_name_var.get().strip()
        if aname:
            attrib[aname] = self.attr_val_var.get()

        self.result = {
            "tag": tag,
            "text": self.text_var.get(),
            "attrib": attrib
        }
        self.destroy()


class AddAttributeDialog(tk.Toplevel):
    """Dialog to add or edit an attribute."""
    def __init__(self, parent, title="Attribute", default_name="", default_value=""):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None

        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding="16")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Attribute Name:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.name_var = tk.StringVar(value=default_name)
        self.name_entry = ttk.Entry(frame, textvariable=self.name_var, width=28)
        self.name_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(frame, text="Value:", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.val_var = tk.StringVar(value=default_value)
        self.val_entry = ttk.Entry(frame, textvariable=self.val_var, width=28)
        self.val_entry.grid(row=3, column=0, sticky="ew", pady=(0, 16))

        btn_box = ttk.Frame(frame)
        btn_box.grid(row=4, column=0, sticky="e")
        ttk.Button(btn_box, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(btn_box, text="Save", command=self._on_ok).pack(side=tk.RIGHT)

        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self.destroy())

        self.geometry("+%d+%d" % (parent.winfo_rootx() + 120, parent.winfo_rooty() + 120))
        if default_name:
            self.val_entry.focus_set()
        else:
            self.name_entry.focus_set()
        self.wait_window(self)

    def _on_ok(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Validation Error", "Attribute name is required.", parent=self)
            self.name_entry.focus_set()
            return
        self.result = (name, self.val_var.get())
        self.destroy()


class XMLViewerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Light XML Viewer & WYSIWYG Editor")
        self.root.geometry("1100x720")
        self.root.minsize(800, 500)

        self.model = XMLModel()
        self.is_modified = False
        self.selected_node_id: Optional[str] = None
        self.updating_inspector = False
        self.search_matches = []
        self.current_match_idx = -1

        self._setup_styles()
        self._build_menu()
        self._build_toolbar()
        self._build_main_ui()
        self._build_status_bar()

        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self.on_new_file())
        self.root.bind("<Control-o>", lambda e: self.on_open_file())
        self.root.bind("<Control-s>", lambda e: self.on_save_file())
        self.root.bind("<Control-S>", lambda e: self.on_save_as())
        self.root.bind("<Control-f>", lambda e: self.focus_search())
        self.root.bind("<F5>", lambda e: self.sync_current_view())

        # Load default sample
        default_sample = get_resource_path("sample.xml")
        if os.path.exists(default_sample):
            self.load_file(default_sample)
        else:
            self.model.create_empty("root")
            self.refresh_tree_view()
            self.update_status("Ready (New document)")

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Clean light modern palette
        bg_main = "#f8f9fa"
        panel_bg = "#ffffff"
        accent_color = "#0d6efd"
        border_color = "#dee2e6"

        self.root.configure(bg=bg_main)
        style.configure(".", background=bg_main, font=("Segoe UI", 9))
        style.configure("TFrame", background=bg_main)
        style.configure("White.TFrame", background=panel_bg)

        style.configure("Toolbar.TFrame", background="#eef1f5", relief=tk.FLAT)
        style.configure("Toolbar.TButton", padding=(6, 4), font=("Segoe UI", 9))
        
        style.configure("Treeview", 
                        background=panel_bg, 
                        fieldbackground=panel_bg, 
                        rowheight=26, 
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading", 
                        background="#e9ecef", 
                        foreground="#333333", 
                        font=("Segoe UI", 9, "bold"),
                        padding=4)
        style.map("Treeview", 
                  background=[("selected", "#0d6efd")], 
                  foreground=[("selected", "#ffffff")])

        style.configure("Section.TLabel", font=("Segoe UI", 10, "bold"), foreground="#212529", background=panel_bg)
        style.configure("Muted.TLabel", font=("Segoe UI", 8), foreground="#6c757d", background=panel_bg)
        style.configure("Status.TLabel", font=("Segoe UI", 9), foreground="#495057", background="#e9ecef")

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Document", accelerator="Ctrl+N", command=self.on_new_file)
        file_menu.add_command(label="Open XML File...", accelerator="Ctrl+O", command=self.on_open_file)
        file_menu.add_command(label="Load Sample Catalog", command=self.load_sample)
        file_menu.add_separator()
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.on_save_file)
        file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.on_save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit / WYSIWYG Menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Add Child Element", accelerator="Ins", command=self.on_add_child)
        edit_menu.add_command(label="Add Sibling After", command=self.on_add_sibling_after)
        edit_menu.add_command(label="Add Sibling Before", command=self.on_add_sibling_before)
        edit_menu.add_separator()
        edit_menu.add_command(label="Add Attribute", command=self.on_add_attribute)
        edit_menu.add_command(label="Duplicate Element", command=self.on_duplicate_node)
        edit_menu.add_command(label="Delete Element", accelerator="Del", command=self.on_delete_node)
        edit_menu.add_separator()
        edit_menu.add_command(label="Move Node Up", accelerator="Alt+Up", command=lambda: self.on_move_node("up"))
        edit_menu.add_command(label="Move Node Down", accelerator="Alt+Down", command=lambda: self.on_move_node("down"))
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Validate XML", command=self.on_validate_xml)
        tools_menu.add_command(label="Pretty Print / Reformat", command=self.on_format_xml)
        tools_menu.add_separator()
        tools_menu.add_command(label="Expand All Tree Nodes", command=self.on_expand_all)
        tools_menu.add_command(label="Collapse All Tree Nodes", command=self.on_collapse_all)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About XML Editor", command=self.on_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _build_toolbar(self):
        toolbar = ttk.Frame(self.root, style="Toolbar.TFrame", padding="6 4 6 4")
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # File buttons
        ttk.Button(toolbar, text="📄 New", style="Toolbar.TButton", command=self.on_new_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📂 Open", style="Toolbar.TButton", command=self.on_open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Save", style="Toolbar.TButton", command=self.on_save_file).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        # Node Operations
        ttk.Button(toolbar, text="➕ Add Child", style="Toolbar.TButton", command=self.on_add_child).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="➕ Add Sibling", style="Toolbar.TButton", command=self.on_add_sibling_after).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Delete", style="Toolbar.TButton", command=self.on_delete_node).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⬆️ Up", style="Toolbar.TButton", command=lambda: self.on_move_node("up")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⬇️ Down", style="Toolbar.TButton", command=lambda: self.on_move_node("down")).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        # Utilities
        ttk.Button(toolbar, text="✨ Format", style="Toolbar.TButton", command=self.on_format_xml).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✔️ Validate", style="Toolbar.TButton", command=self.on_validate_xml).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📖 Sample", style="Toolbar.TButton", command=self.load_sample).pack(side=tk.LEFT, padx=2)

        # Search box on the right
        search_box = ttk.Frame(toolbar, style="Toolbar.TFrame")
        search_box.pack(side=tk.RIGHT, padx=4)

        ttk.Label(search_box, text="🔍", background="#eef1f5").pack(side=tk.LEFT, padx=(0, 2))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_box, textvariable=self.search_var, width=18)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 4))
        self.search_entry.bind("<Return>", lambda e: self.on_search_next())

        ttk.Button(search_box, text="▲", width=3, command=self.on_search_prev).pack(side=tk.LEFT, padx=1)
        ttk.Button(search_box, text="▼", width=3, command=self.on_search_next).pack(side=tk.LEFT, padx=1)
        self.search_count_lbl = ttk.Label(search_box, text="", background="#eef1f5", font=("Segoe UI", 8))
        self.search_count_lbl.pack(side=tk.LEFT, padx=(4, 0))

    def _build_main_ui(self):
        # Notebook with Tabs: [🌲 Visual WYSIWYG Editor] and [📝 XML Source Code]
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 4))

        # Tab 1: WYSIWYG Visual Tab
        self.tab_visual = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_visual, text="  🌲 WYSIWYG Visual Editor  ")

        # Tab 2: XML Source Tab
        self.tab_source = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_source, text="  📝 Raw XML Source Code  ")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._build_visual_tab()
        self._build_source_tab()

    def _build_visual_tab(self):
        # Paned Window: Left = Tree Hierarchy, Right = Inspector & Properties
        paned = ttk.PanedWindow(self.tab_visual, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # --- LEFT PANEL: TREE VIEW ---
        left_frame = ttk.Frame(paned, padding="4")
        paned.add(left_frame, weight=3)

        tree_header = ttk.Frame(left_frame)
        tree_header.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(tree_header, text="XML Document Hierarchy", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        
        btn_collapse = ttk.Button(tree_header, text="Collapse", width=8, command=self.on_collapse_all)
        btn_collapse.pack(side=tk.RIGHT, padx=(2, 0))
        btn_expand = ttk.Button(tree_header, text="Expand", width=8, command=self.on_expand_all)
        btn_expand.pack(side=tk.RIGHT)

        tree_container = ttk.Frame(left_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)

        tree_scroll_y = ttk.Scrollbar(tree_container, orient=tk.VERTICAL)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree = ttk.Treeview(
            tree_container,
            columns=("attributes", "text"),
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            selectmode="browse"
        )
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)

        self.tree.heading("#0", text="Element Tag", anchor=tk.W)
        self.tree.heading("attributes", text="Attributes", anchor=tk.W)
        self.tree.heading("text", text="Inner Text", anchor=tk.W)

        self.tree.column("#0", width=220, minwidth=140)
        self.tree.column("attributes", width=200, minwidth=120)
        self.tree.column("text", width=240, minwidth=140)

        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.bind("<Button-3>", self._show_tree_context_menu)
        self.tree.bind("<Delete>", lambda e: self.on_delete_node())
        self.tree.bind("<Insert>", lambda e: self.on_add_child())

        # Context Menu for Tree
        self.tree_menu = tk.Menu(self.root, tearoff=0)
        self.tree_menu.add_command(label="➕ Add Child Element", command=self.on_add_child)
        self.tree_menu.add_command(label="➕ Add Sibling After", command=self.on_add_sibling_after)
        self.tree_menu.add_command(label="➕ Add Sibling Before", command=self.on_add_sibling_before)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="🏷️ Add Attribute", command=self.on_add_attribute)
        self.tree_menu.add_command(label="📋 Duplicate Node", command=self.on_duplicate_node)
        self.tree_menu.add_command(label="⬆️ Move Up", command=lambda: self.on_move_node("up"))
        self.tree_menu.add_command(label="⬇️ Move Down", command=lambda: self.on_move_node("down"))
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="📌 Copy XPath", command=self.on_copy_xpath)
        self.tree_menu.add_command(label="🗑️ Delete Node", command=self.on_delete_node)

        # --- RIGHT PANEL: WYSIWYG INSPECTOR ---
        right_frame = ttk.Frame(paned, padding="8", style="White.TFrame")
        paned.add(right_frame, weight=2)

        ttk.Label(right_frame, text="Element Inspector & Editor", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 6))

        # XPath Breadcrumb
        xpath_box = ttk.Frame(right_frame, style="White.TFrame")
        xpath_box.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(xpath_box, text="XPath:", style="Muted.TLabel").pack(side=tk.LEFT, padx=(0, 4))
        self.xpath_lbl = ttk.Label(xpath_box, text="/", font=("Consolas", 8, "bold"), foreground="#0d6efd", background="#ffffff")
        self.xpath_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(xpath_box, text="Copy", width=5, command=self.on_copy_xpath).pack(side=tk.RIGHT)

        # Tag Name Editor
        tag_box = ttk.LabelFrame(right_frame, text=" Element Tag Name ", padding=8)
        tag_box.pack(fill=tk.X, pady=(0, 10))

        tag_inner = ttk.Frame(tag_box)
        tag_inner.pack(fill=tk.X)
        self.tag_editor_var = tk.StringVar()
        self.tag_editor_entry = ttk.Entry(tag_inner, textvariable=self.tag_editor_var, font=("Segoe UI", 10, "bold"))
        self.tag_editor_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.tag_editor_entry.bind("<Return>", lambda e: self.apply_tag_change())
        ttk.Button(tag_inner, text="Update Tag", command=self.apply_tag_change).pack(side=tk.RIGHT)

        # Attributes Editor Table
        attr_box = ttk.LabelFrame(right_frame, text=" Attributes ", padding=8)
        attr_box.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        attr_tbl_container = ttk.Frame(attr_box)
        attr_tbl_container.pack(fill=tk.BOTH, expand=True)

        self.attr_tree = ttk.Treeview(attr_tbl_container, columns=("name", "value"), show="headings", height=5)
        self.attr_tree.heading("name", text="Attribute Name", anchor=tk.W)
        self.attr_tree.heading("value", text="Value", anchor=tk.W)
        self.attr_tree.column("name", width=110)
        self.attr_tree.column("value", width=150)
        self.attr_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        attr_scroll = ttk.Scrollbar(attr_tbl_container, orient=tk.VERTICAL, command=self.attr_tree.yview)
        attr_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.attr_tree.configure(yscrollcommand=attr_scroll.set)

        self.attr_tree.bind("<Double-1>", lambda e: self.on_edit_attribute())

        # Attribute action buttons
        attr_btn_row = ttk.Frame(attr_box)
        attr_btn_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(attr_btn_row, text="➕ Add", width=8, command=self.on_add_attribute).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(attr_btn_row, text="✏️ Edit", width=8, command=self.on_edit_attribute).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(attr_btn_row, text="🗑️ Remove", width=8, command=self.on_remove_attribute).pack(side=tk.LEFT)

        # Text Content Editor
        text_box = ttk.LabelFrame(right_frame, text=" Text Content ", padding=8)
        text_box.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        text_scroll = ttk.Scrollbar(text_box)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_editor = tk.Text(
            text_box,
            wrap=tk.WORD,
            font=("Consolas", 10),
            yscrollcommand=text_scroll.set,
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=0,
            bg="#fafbfc"
        )
        self.text_editor.pack(fill=tk.BOTH, expand=True)
        text_scroll.config(command=self.text_editor.yview)

        # Inspector Save / Apply Button
        btn_apply_box = ttk.Frame(right_frame, style="White.TFrame")
        btn_apply_box.pack(fill=tk.X)
        self.btn_save_changes = ttk.Button(btn_apply_box, text="💾 Apply Changes to Selected Node", command=self.apply_inspector_changes)
        self.btn_save_changes.pack(side=tk.RIGHT)

    def _build_source_tab(self):
        source_frame = ttk.Frame(self.tab_source, padding=6)
        source_frame.pack(fill=tk.BOTH, expand=True)

        source_top = ttk.Frame(source_frame)
        source_top.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(source_top, text="Raw XML Document Source", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Button(source_top, text="🔄 Sync to Visual Tree", command=self.sync_source_to_model).pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Button(source_top, text="✨ Pretty Format", command=self.on_format_xml).pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Button(source_top, text="✔️ Check Syntax", command=self.on_validate_xml).pack(side=tk.RIGHT)

        text_area_frame = ttk.Frame(source_frame)
        text_area_frame.pack(fill=tk.BOTH, expand=True)

        # Line numbers
        self.line_numbers = tk.Text(
            text_area_frame,
            width=5,
            padx=4,
            takefocus=0,
            border=0,
            background="#f1f3f5",
            foreground="#868e96",
            font=("Consolas", 10),
            state=tk.DISABLED
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Source code text box
        code_scroll_y = ttk.Scrollbar(text_area_frame, orient=tk.VERTICAL)
        code_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        code_scroll_x = ttk.Scrollbar(text_area_frame, orient=tk.HORIZONTAL)
        code_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.source_editor = tk.Text(
            text_area_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            yscrollcommand=self._on_source_scroll,
            xscrollcommand=code_scroll_x.set,
            undo=True,
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=0,
            bg="#ffffff",
            fg="#212529"
        )
        self.source_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        code_scroll_y.config(command=self._on_source_scroll_y)
        code_scroll_x.config(command=self.source_editor.xview)

        # Syntax tags styling
        self.source_editor.tag_configure("xml_decl", foreground="#6c757d", font=("Consolas", 10, "italic"))
        self.source_editor.tag_configure("xml_comment", foreground="#6a737d", font=("Consolas", 10, "italic"))
        self.source_editor.tag_configure("xml_tag", foreground="#005cc5", font=("Consolas", 10, "bold"))
        self.source_editor.tag_configure("xml_bracket", foreground="#005cc5")
        self.source_editor.tag_configure("xml_attr_name", foreground="#6f42c1")
        self.source_editor.tag_configure("xml_attr_val", foreground="#22863a")
        self.source_editor.tag_configure("search_highlight", background="#ffe066", foreground="#000000")

        self.source_editor.bind("<KeyRelease>", self._on_source_key_release)
        self.source_editor.bind("<MouseWheel>", self._on_mouse_wheel)

    def _build_status_bar(self):
        status_frame = ttk.Frame(self.root, style="Toolbar.TFrame", padding="6 2 6 2")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_lbl = ttk.Label(status_frame, text="Ready", style="Status.TLabel")
        self.status_lbl.pack(side=tk.LEFT)

        self.file_info_lbl = ttk.Label(status_frame, text="Untitled", style="Status.TLabel")
        self.file_info_lbl.pack(side=tk.RIGHT, padx=(10, 0))

        self.node_count_lbl = ttk.Label(status_frame, text="Nodes: 0", style="Status.TLabel")
        self.node_count_lbl.pack(side=tk.RIGHT)

    def update_status(self, msg: str):
        self.status_lbl.config(text=msg)

    # ---------------- SYNCHRONIZATION & TABS ----------------

    def _on_tab_changed(self, event):
        current_tab = self.notebook.index("current")
        if current_tab == 0:  # Switched to Visual Tab
            # If source code was edited, parse and update visual tree
            src_text = self.source_editor.get("1.0", tk.END).strip()
            if src_text:
                ok, err = self.model.parse_string(src_text)
                if ok:
                    self.refresh_tree_view()
                else:
                    messagebox.showerror(
                        "XML Parse Error",
                        f"Could not sync source to Visual Editor:\n{err}\n\nPlease fix syntax errors in the source tab.",
                        parent=self.root
                    )
                    self.notebook.select(1)
        elif current_tab == 1:  # Switched to Source Tab
            # Sync visual tree model to source editor
            self.sync_model_to_source()

    def sync_model_to_source(self):
        xml_text = self.model.to_string(pretty=True)
        self.source_editor.delete("1.0", tk.END)
        self.source_editor.insert("1.0", xml_text)
        self._highlight_syntax()
        self._update_line_numbers()

    def sync_source_to_model(self):
        src_text = self.source_editor.get("1.0", tk.END).strip()
        ok, err = self.model.parse_string(src_text)
        if ok:
            self.refresh_tree_view()
            self.set_modified(True)
            self.update_status("XML Source successfully synchronized with Visual Editor.")
            messagebox.showinfo("Success", "Source synchronized with Visual Editor!", parent=self.root)
        else:
            messagebox.showerror("XML Parse Error", f"Cannot synchronize:\n{err}", parent=self.root)

    def sync_current_view(self):
        if self.notebook.index("current") == 1:
            self.sync_source_to_model()
        else:
            self.sync_model_to_source()

    # ---------------- SOURCE CODE SYNTAX & SCROLL ----------------

    def _on_source_scroll(self, *args):
        self.line_numbers.yview_moveto(args[0])

    def _on_source_scroll_y(self, *args):
        self.source_editor.yview(*args)
        self.line_numbers.yview(*args)

    def _on_mouse_wheel(self, event):
        self.line_numbers.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_source_key_release(self, event=None):
        self._update_line_numbers()
        self._highlight_syntax()
        self.set_modified(True)

    def _update_line_numbers(self):
        lines = int(self.source_editor.index("end-1c").split(".")[0])
        line_num_content = "\n".join(str(i) for i in range(1, lines + 1))
        self.line_numbers.config(state=tk.NORMAL)
        self.line_numbers.delete("1.0", tk.END)
        self.line_numbers.insert("1.0", line_num_content)
        self.line_numbers.config(state=tk.DISABLED)

    def _highlight_syntax(self):
        for tag in ["xml_decl", "xml_comment", "xml_tag", "xml_bracket", "xml_attr_name", "xml_attr_val"]:
            self.source_editor.tag_remove(tag, "1.0", tk.END)

        text = self.source_editor.get("1.0", tk.END)

        # XML Declaration: <? ... ?>
        for m in re.finditer(r"<\?.*?\?>", text):
            start = f"1.0 + {m.start()} chars"
            end = f"1.0 + {m.end()} chars"
            self.source_editor.tag_add("xml_decl", start, end)

        # Comments: <!-- ... -->
        for m in re.finditer(r"<!--[\s\S]*?-->", text):
            start = f"1.0 + {m.start()} chars"
            end = f"1.0 + {m.end()} chars"
            self.source_editor.tag_add("xml_comment", start, end)

        # Tags and attributes: <(/)?([a-zA-Z0-9_\-:]+) ... (/)?>
        tag_pat = re.finditer(r"<(/)?([a-zA-Z0-9_\-:]+)((?:\s+[^=>/]+(?:=(?:\"[^\"]*\"|'[^']*'))?)*)\s*(/?)>", text)
        for m in tag_pat:
            start_pos = m.start()
            # Tag brackets & name
            slash = m.group(1) or ""
            tag_name = m.group(2)
            attrs_str = m.group(3)

            bracket_start = f"1.0 + {start_pos} chars"
            bracket_end = f"1.0 + {start_pos + 1 + len(slash)} chars"
            self.source_editor.tag_add("xml_bracket", bracket_start, bracket_end)

            name_start = bracket_end
            name_end = f"1.0 + {start_pos + 1 + len(slash) + len(tag_name)} chars"
            self.source_editor.tag_add("xml_tag", name_start, name_end)

            # Attributes inside tag
            if attrs_str:
                attr_offset = start_pos + 1 + len(slash) + len(tag_name)
                for am in re.finditer(r'([a-zA-Z0-9_\-:]+)(?:=("[^"]*"|\'[^\']*\'))?', attrs_str):
                    aname = am.group(1)
                    aval = am.group(2)
                    astart = attr_offset + am.start(1)
                    aend = attr_offset + am.end(1)
                    self.source_editor.tag_add("xml_attr_name", f"1.0 + {astart} chars", f"1.0 + {aend} chars")

                    if aval:
                        vstart = attr_offset + am.start(2)
                        vend = attr_offset + am.end(2)
                        self.source_editor.tag_add("xml_attr_val", f"1.0 + {vstart} chars", f"1.0 + {vend} chars")

    # ---------------- TREE VIEW & INSPECTOR ----------------

    def refresh_tree_view(self, select_node_id: Optional[str] = None):
        """Re-populates the visual Treeview from the XML model."""
        self.tree.delete(*self.tree.get_children())
        if self.model.root is None:
            self.node_count_lbl.config(text="Nodes: 0")
            self._clear_inspector()
            return

        def _populate(elem, parent_tree_id=""):
            node_id = self.model.get_id_by_element(elem)
            if not node_id:
                return

            # Format attributes preview
            attrs_str = " ".join([f'{k}="{v}"' for k, v in elem.attrib.items()])
            # Format text preview
            text_str = (elem.text or "").strip().replace("\n", " ")
            if len(text_str) > 40:
                text_str = text_str[:37] + "..."

            display_tag = f"<{elem.tag}>"
            item = self.tree.insert(
                parent_tree_id,
                tk.END,
                iid=node_id,
                text=display_tag,
                values=(attrs_str, text_str),
                open=True
            )

            for child in elem:
                _populate(child, item)

        _populate(self.model.root)
        total_nodes = len(self.model.element_id_map)
        self.node_count_lbl.config(text=f"Nodes: {total_nodes}")

        target_select = select_node_id or self.selected_node_id
        if target_select and self.tree.exists(target_select):
            self.tree.selection_set(target_select)
            self.tree.see(target_select)
            self._populate_inspector(target_select)
        elif self.model.root is not None:
            root_id = self.model.get_id_by_element(self.model.root)
            if root_id and self.tree.exists(root_id):
                self.tree.selection_set(root_id)
                self._populate_inspector(root_id)

    def _on_tree_select(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        node_id = selected[0]
        self.selected_node_id = node_id
        self._populate_inspector(node_id)

    def _on_tree_double_click(self, event=None):
        """Double clicking a node opens tag editor or edit dialog."""
        self.tag_editor_entry.focus_set()
        self.tag_editor_entry.select_range(0, tk.END)

    def _show_tree_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.selected_node_id = item
            self._populate_inspector(item)
            self.tree_menu.post(event.x_root, event.y_root)

    def _populate_inspector(self, node_id: str):
        elem = self.model.get_element_by_id(node_id)
        if elem is None:
            self._clear_inspector()
            return

        self.updating_inspector = True

        # XPath
        xpath = self.model.get_xpath(elem)
        self.xpath_lbl.config(text=xpath or "/")

        # Tag
        self.tag_editor_var.set(elem.tag)

        # Attributes
        self.attr_tree.delete(*self.attr_tree.get_children())
        for k, v in elem.attrib.items():
            self.attr_tree.insert("", tk.END, values=(k, v))

        # Text
        self.text_editor.delete("1.0", tk.END)
        if elem.text:
            self.text_editor.insert("1.0", elem.text)

        self.updating_inspector = False

    def _clear_inspector(self):
        self.xpath_lbl.config(text="/")
        self.tag_editor_var.set("")
        self.attr_tree.delete(*self.attr_tree.get_children())
        self.text_editor.delete("1.0", tk.END)
        self.selected_node_id = None

    # ---------------- WYSIWYG ACTIONS & MODIFICATIONS ----------------

    def apply_tag_change(self):
        if not self.selected_node_id:
            return
        elem = self.model.get_element_by_id(self.selected_node_id)
        if elem is None:
            return

        new_tag = self.tag_editor_var.get().strip()
        ok, err = self.model.rename_element(elem, new_tag)
        if not ok:
            messagebox.showerror("Error", err, parent=self.root)
            self.tag_editor_var.set(elem.tag)
            return

        self.set_modified(True)
        self.refresh_tree_view(self.selected_node_id)
        self.update_status(f"Element tag updated to <{new_tag}>")

    def apply_inspector_changes(self):
        if not self.selected_node_id:
            return
        elem = self.model.get_element_by_id(self.selected_node_id)
        if elem is None:
            return

        # Tag
        new_tag = self.tag_editor_var.get().strip()
        if new_tag != elem.tag:
            ok, err = self.model.rename_element(elem, new_tag)
            if not ok:
                messagebox.showerror("Tag Error", err, parent=self.root)
                return

        # Text
        new_text = self.text_editor.get("1.0", "end-1c")
        self.model.set_text(elem, new_text)

        self.set_modified(True)
        self.refresh_tree_view(self.selected_node_id)
        self.update_status(f"Changes applied to <{elem.tag}>")

    def on_add_attribute(self):
        if not self.selected_node_id:
            messagebox.showinfo("Select Element", "Please select an element first.", parent=self.root)
            return
        elem = self.model.get_element_by_id(self.selected_node_id)
        if elem is None:
            return

        dlg = AddAttributeDialog(self.root, title=f"Add Attribute to <{elem.tag}>")
        if dlg.result:
            key, val = dlg.result
            ok, err = self.model.set_attribute(elem, key, val)
            if not ok:
                messagebox.showerror("Error", err, parent=self.root)
                return
            self.set_modified(True)
            self.refresh_tree_view(self.selected_node_id)
            self.update_status(f"Added attribute '{key}' to <{elem.tag}>")

    def on_edit_attribute(self):
        if not self.selected_node_id:
            return
        elem = self.model.get_element_by_id(self.selected_node_id)
        if elem is None:
            return

        selected_attr = self.attr_tree.selection()
        if not selected_attr:
            messagebox.showinfo("Select Attribute", "Please select an attribute from the table to edit.", parent=self.root)
            return

        item = self.attr_tree.item(selected_attr[0])
        old_key, old_val = item["values"]

        dlg = AddAttributeDialog(self.root, title="Edit Attribute", default_name=str(old_key), default_value=str(old_val))
        if dlg.result:
            new_key, new_val = dlg.result
            if new_key != old_key:
                self.model.remove_attribute(elem, old_key)
            ok, err = self.model.set_attribute(elem, new_key, new_val)
            if not ok:
                messagebox.showerror("Error", err, parent=self.root)
                return
            self.set_modified(True)
            self.refresh_tree_view(self.selected_node_id)
            self.update_status(f"Updated attribute '{new_key}'")

    def on_remove_attribute(self):
        if not self.selected_node_id:
            return
        elem = self.model.get_element_by_id(self.selected_node_id)
        if elem is None:
            return

        selected_attr = self.attr_tree.selection()
        if not selected_attr:
            messagebox.showinfo("Select Attribute", "Please select an attribute to remove.", parent=self.root)
            return

        item = self.attr_tree.item(selected_attr[0])
        key = item["values"][0]

        if messagebox.askyesno("Confirm Remove", f"Remove attribute '{key}'?", parent=self.root):
            self.model.remove_attribute(elem, str(key))
            self.set_modified(True)
            self.refresh_tree_view(self.selected_node_id)
            self.update_status(f"Removed attribute '{key}'")

    def on_add_child(self):
        if not self.selected_node_id:
            messagebox.showinfo("Select Parent", "Please select a parent element first.", parent=self.root)
            return
        parent_elem = self.model.get_element_by_id(self.selected_node_id)
        if parent_elem is None:
            return

        dlg = AddNodeDialog(self.root, title=f"Add Child to <{parent_elem.tag}>")
        if dlg.result:
            ok, new_elem, err = self.model.add_child(
                parent_elem,
                dlg.result["tag"],
                dlg.result["text"],
                dlg.result["attrib"]
            )
            if not ok:
                messagebox.showerror("Error", err, parent=self.root)
                return
            self.set_modified(True)
            new_id = self.model.get_id_by_element(new_elem)
            self.refresh_tree_view(new_id)
            self.update_status(f"Added child <{new_elem.tag}>")

    def on_add_sibling_after(self):
        self._add_sibling(after=True)

    def on_add_sibling_before(self):
        self._add_sibling(after=False)

    def _add_sibling(self, after: bool):
        if not self.selected_node_id:
            messagebox.showinfo("Select Node", "Please select an element first.", parent=self.root)
            return
        target = self.model.get_element_by_id(self.selected_node_id)
        if target is None:
            return

        if target is self.model.root:
            messagebox.showwarning("Root Element", "Cannot add siblings to the XML root element.", parent=self.root)
            return

        dlg = AddNodeDialog(self.root, title="Add Sibling Element")
        if dlg.result:
            ok, new_elem, err = self.model.insert_sibling(
                target,
                dlg.result["tag"],
                dlg.result["text"],
                dlg.result["attrib"],
                after=after
            )
            if not ok:
                messagebox.showerror("Error", err, parent=self.root)
                return
            self.set_modified(True)
            new_id = self.model.get_id_by_element(new_elem)
            self.refresh_tree_view(new_id)
            self.update_status(f"Added sibling <{new_elem.tag}>")

    def on_duplicate_node(self):
        if not self.selected_node_id:
            return
        elem = self.model.get_element_by_id(self.selected_node_id)
        if elem is None:
            return

        ok, cloned, err = self.model.duplicate_element(elem)
        if not ok:
            messagebox.showwarning("Notice", err, parent=self.root)
            return

        self.set_modified(True)
        new_id = self.model.get_id_by_element(cloned)
        self.refresh_tree_view(new_id)
        self.update_status(f"Duplicated <{elem.tag}>")

    def on_delete_node(self):
        if not self.selected_node_id:
            return
        elem = self.model.get_element_by_id(self.selected_node_id)
        if elem is None:
            return

        if elem is self.model.root:
            messagebox.showwarning("Cannot Delete Root", "Cannot delete the root XML element.", parent=self.root)
            return

        parent = self.model.get_parent(elem)
        parent_id = self.model.get_id_by_element(parent) if parent else None

        if messagebox.askyesno("Confirm Delete", f"Delete element <{elem.tag}> and all its children?", parent=self.root):
            ok, err = self.model.delete_element(elem)
            if not ok:
                messagebox.showerror("Error", err, parent=self.root)
                return
            self.set_modified(True)
            self.refresh_tree_view(parent_id)
            self.update_status(f"Deleted element <{elem.tag}>")

    def on_move_node(self, direction: str):
        if not self.selected_node_id:
            return
        elem = self.model.get_element_by_id(self.selected_node_id)
        if elem is None:
            return

        success = self.model.move_element(elem, direction)
        if success:
            self.set_modified(True)
            self.refresh_tree_view(self.selected_node_id)
            self.update_status(f"Moved <{elem.tag}> {direction}")

    def on_copy_xpath(self):
        if not self.selected_node_id:
            return
        elem = self.model.get_element_by_id(self.selected_node_id)
        if elem:
            xpath = self.model.get_xpath(elem)
            self.root.clipboard_clear()
            self.root.clipboard_append(xpath)
            self.update_status(f"Copied XPath to clipboard: {xpath}")

    def on_expand_all(self):
        def _expand(item):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                _expand(child)
        for root_item in self.tree.get_children():
            _expand(root_item)

    def on_collapse_all(self):
        def _collapse(item):
            for child in self.tree.get_children(item):
                _collapse(child)
            if self.tree.parent(item):  # Keep root open
                self.tree.item(item, open=False)
        for root_item in self.tree.get_children():
            _collapse(root_item)

    # ---------------- SEARCH & FILTER ----------------

    def focus_search(self):
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)

    def _collect_search_matches(self, query: str):
        query = query.lower().strip()
        matches = []
        if not query:
            return matches

        for node_id, elem in self.model.element_id_map.items():
            # Check tag
            if query in elem.tag.lower():
                matches.append(node_id)
                continue
            # Check attributes
            matched_attr = False
            for k, v in elem.attrib.items():
                if query in k.lower() or query in str(v).lower():
                    matches.append(node_id)
                    matched_attr = True
                    break
            if matched_attr:
                continue
            # Check text
            if elem.text and query in elem.text.lower():
                matches.append(node_id)

        return matches

    def on_search_next(self):
        query = self.search_var.get().strip()
        if not query:
            return

        self.search_matches = self._collect_search_matches(query)
        if not self.search_matches:
            self.search_count_lbl.config(text="0/0")
            self.update_status(f"No matches found for '{query}'")
            return

        self.current_match_idx = (self.current_match_idx + 1) % len(self.search_matches)
        self._navigate_search_match()

    def on_search_prev(self):
        query = self.search_var.get().strip()
        if not query:
            return

        self.search_matches = self._collect_search_matches(query)
        if not self.search_matches:
            self.search_count_lbl.config(text="0/0")
            return

        self.current_match_idx = (self.current_match_idx - 1) % len(self.search_matches)
        self._navigate_search_match()

    def _navigate_search_match(self):
        target_id = self.search_matches[self.current_match_idx]
        self.search_count_lbl.config(text=f"{self.current_match_idx + 1}/{len(self.search_matches)}")
        
        # Switch to visual tab or highlight
        if self.tree.exists(target_id):
            # Ensure parents are open
            p = self.tree.parent(target_id)
            while p:
                self.tree.item(p, open=True)
                p = self.tree.parent(p)

            self.tree.selection_set(target_id)
            self.tree.see(target_id)
            self._populate_inspector(target_id)
            self.update_status(f"Match {self.current_match_idx + 1} of {len(self.search_matches)}")

    # ---------------- FILE & SYSTEM OPERATIONS ----------------

    def set_modified(self, modified: bool = True):
        self.is_modified = modified
        fname = os.path.basename(self.model.filepath) if self.model.filepath else "Untitled"
        mark = " *" if self.is_modified else ""
        self.root.title(f"{fname}{mark} - Light XML Viewer & WYSIWYG Editor")
        self.file_info_lbl.config(text=f"{fname}{mark}")

    def on_new_file(self):
        if self.is_modified:
            if not messagebox.askyesno("Unsaved Changes", "Discard unsaved changes and create new document?", parent=self.root):
                return

        root_tag = simpledialog.askstring("New Document", "Enter root element tag name:", initialvalue="root", parent=self.root)
        if not root_tag:
            return
        root_tag = root_tag.strip()
        self.model.create_empty(root_tag)
        self.set_modified(False)
        self.refresh_tree_view()
        self.sync_model_to_source()
        self.update_status(f"Created new XML document with root <{root_tag}>")

    def on_open_file(self):
        if self.is_modified:
            if not messagebox.askyesno("Unsaved Changes", "Discard unsaved changes and open file?", parent=self.root):
                return

        path = filedialog.askopenfilename(
            title="Open XML File",
            filetypes=[("XML files", "*.xml"), ("XSL/XSLT files", "*.xsl;*.xslt"), ("All files", "*.*")],
            parent=self.root
        )
        if path:
            self.load_file(path)

    def load_file(self, filepath: str):
        ok, err = self.model.parse_file(filepath)
        if ok:
            self.set_modified(False)
            self.refresh_tree_view()
            self.sync_model_to_source()
            self.update_status(f"Loaded {os.path.basename(filepath)}")
        else:
            messagebox.showerror("Error Opening XML", f"Could not open '{filepath}':\n{err}", parent=self.root)

    def load_sample(self):
        sample_path = get_resource_path("sample.xml")
        if os.path.exists(sample_path):
            self.load_file(sample_path)
        else:
            messagebox.showinfo("Sample File", "sample.xml was not found.", parent=self.root)

    def on_save_file(self):
        if not self.model.filepath:
            return self.on_save_as()

        # If currently in source tab, synchronize changes first
        if self.notebook.index("current") == 1:
            src_text = self.source_editor.get("1.0", tk.END).strip()
            ok, err = self.model.parse_string(src_text)
            if not ok:
                messagebox.showerror("Cannot Save", f"XML contains syntax errors:\n{err}", parent=self.root)
                return

        content = self.model.to_string(pretty=True)
        try:
            with open(self.model.filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self.set_modified(False)
            self.update_status(f"Saved {os.path.basename(self.model.filepath)}")
            messagebox.showinfo("Saved", f"File saved successfully to:\n{self.model.filepath}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Save Error", str(e), parent=self.root)

    def on_save_as(self):
        # Sync if in source view
        if self.notebook.index("current") == 1:
            src_text = self.source_editor.get("1.0", tk.END).strip()
            ok, err = self.model.parse_string(src_text)
            if not ok:
                messagebox.showerror("Cannot Save", f"XML contains syntax errors:\n{err}", parent=self.root)
                return

        path = filedialog.asksaveasfilename(
            title="Save XML File As",
            defaultextension=".xml",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
            parent=self.root
        )
        if path:
            self.model.filepath = path
            self.on_save_file()

    def on_validate_xml(self):
        # Get XML string based on active tab
        if self.notebook.index("current") == 1:
            text = self.source_editor.get("1.0", tk.END)
        else:
            text = self.model.to_string(pretty=True)

        is_valid, err_msg, line, col = XMLModel.validate_string(text)
        if is_valid:
            messagebox.showinfo("XML Validation", "✓ XML is well-formed and valid!", parent=self.root)
            self.update_status("Validation: XML is well-formed.")
        else:
            loc = f"Line {line}, Column {col}: " if line else ""
            messagebox.showerror("Validation Error", f"✗ XML is not valid!\n\n{loc}{err_msg}", parent=self.root)
            self.update_status(f"Validation Error: {err_msg}")
            if self.notebook.index("current") == 1 and line:
                # Highlight and move cursor to error
                self.source_editor.focus_set()
                self.source_editor.mark_set(tk.INSERT, f"{line}.{col or 0}")
                self.source_editor.see(f"{line}.0")

    def on_format_xml(self):
        if self.notebook.index("current") == 1:
            src_text = self.source_editor.get("1.0", tk.END).strip()
            ok, err = self.model.parse_string(src_text)
            if not ok:
                messagebox.showerror("Format Error", f"Cannot format invalid XML:\n{err}", parent=self.root)
                return

        formatted = self.model.to_string(pretty=True)
        self.source_editor.delete("1.0", tk.END)
        self.source_editor.insert("1.0", formatted)
        self._highlight_syntax()
        self._update_line_numbers()
        self.set_modified(True)
        self.update_status("XML pretty-printed with clean indentation.")

    def on_about(self):
        about_text = (
            "Light XML Viewer & WYSIWYG Editor\n"
            "Version 1.0\n\n"
            "Built with Python and Tkinter.\n\n"
            "Features:\n"
            "• WYSIWYG Tree DOM visual editor\n"
            "• Live element tag, text, and attribute inspector\n"
            "• Syntax-highlighted XML code view\n"
            "• Full CRUD (Add child/sibling, delete, duplicate, move)\n"
            "• Real-time search & filter\n"
            "• XML validation & pretty formatting"
        )
        messagebox.showinfo("About XML Editor", about_text, parent=self.root)
