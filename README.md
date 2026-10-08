# Light XML Viewer & WYSIWYG Editor (Python + Tkinter)

A lightweight, zero-dependency visual XML viewer and WYSIWYG editor built with Python and Tkinter and with help of Antigravity AI.

---

## 🌟 Key Features

- **🌲 Visual WYSIWYG Tree Editor**:
  - Interactive hierarchical tree displaying element tags, attributes preview, and inner text preview.
  - Full DOM node management: **Add Child**, **Add Sibling (Before/After)**, **Duplicate Node**, **Move Up / Down**, and **Delete**.
  - Right-click context menu for instant node operations.
  - Expand All / Collapse All tree navigation.

- **🔍 Live Element Inspector & Property Editor**:
  - **Tag Renamer**: In-place element tag editing with validation.
  - **Attributes Table**: Tabular view of all attributes with Add, Edit, and Delete actions.
  - **Text Content Editor**: Multi-line editor for inner node content.
  - **Live XPath Breadcrumbs**: Real-time XPath generation with one-click copy to clipboard.

- **📝 Synchronized Source Code Editor**:
  - Real-time syntax highlighting for XML declarations, tags, brackets, attributes, and comments.
  - Synchronized line numbers and smooth scrolling.
  - Bidirectional sync: edits in the visual tree update source code, and vice versa.

- **⚡ XML Tools & Utilities**:
  - **XML Validation**: Instant well-formedness checker reporting exact line and column numbers.
  - **Pretty Print / Formatting**: Clean re-indentation and formatting.
  - **Search & Filter**: Real-time search across tag names, attribute names/values, and text content with Next / Previous navigation.

- **🪶 Ultra-Lightweight & Cross-Platform**:
  - Uses only Python standard libraries (`tkinter`, `xml.etree.ElementTree`, `xml.dom.minidom`).
  - No external pip dependencies required.

---

## 🚀 How to Run

### 1. Run the Standalone Executable (.exe)
You can launch the pre-built, single-file Windows executable directly without needing Python installed:
* Double-click `dist\XMLViewer.exe` in Windows Explorer, or run:
```powershell
.\dist\XMLViewer.exe
```

### 2. Launch with Python
```powershell
python main.py
```

### 3. Rebuild the Executable
To rebuild the `.exe` at any time:
```powershell
pyinstaller --onefile --windowed --add-data "sample.xml;." --name "XMLViewer" --clean main.py
```

### 4. Run the Unit Tests
```powershell
python test_xml_editor.py
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl + N` | New XML Document |
| `Ctrl + O` | Open XML File |
| `Ctrl + S` | Save File |
| `Ctrl + Shift + S` | Save File As... |
| `Ctrl + F` | Jump to Search Bar |
| `F5` | Synchronize Active View |
| `Insert` | Add Child Element to Selected Node |
| `Delete` | Delete Selected Node |
| `Alt + Up` | Move Selected Element Up |
| `Alt + Down` | Move Selected Element Down |

---

## 📁 Project Structure

```
XMLViewer/
├── main.py              # Application launcher (with high-DPI support)
├── gui.py               # Tkinter GUI implementation (Tree, Inspector, Source editor)
├── xml_model.py         # XML DOM model, CRUD, XPath, formatting & validation
├── sample.xml           # Preloaded sample XML catalog for testing
├── test_xml_editor.py   # Unit test suite
└── README.md            # Documentation
```
