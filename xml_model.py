"""
XML Document Model for XML Viewer & WYSIWYG Editor.
Provides XML parsing, tree management, element manipulation, serialization, and validation.
"""

import copy
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Optional, Dict, List, Tuple


class XMLModel:
    def __init__(self):
        self.root: Optional[ET.Element] = None
        self.filepath: Optional[str] = None
        self.parent_map: Dict[ET.Element, Optional[ET.Element]] = {}
        self.element_id_map: Dict[str, ET.Element] = {}
        self.id_counter = 0

    def parse_string(self, xml_text: str) -> Tuple[bool, Optional[str]]:
        """Parses XML string into an ElementTree."""
        try:
            # Strip leading/trailing whitespaces
            clean_text = xml_text.strip()
            if not clean_text:
                return False, "XML content is empty."
            root = ET.fromstring(clean_text)
            self.root = root
            self._rebuild_maps()
            return True, None
        except ET.ParseError as e:
            return False, f"Line {e.position[0]}, Column {e.position[1]}: {e.msg}"
        except Exception as e:
            return False, str(e)

    def parse_file(self, filepath: str) -> Tuple[bool, Optional[str]]:
        """Reads and parses an XML file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            success, err = self.parse_string(content)
            if success:
                self.filepath = filepath
            return success, err
        except UnicodeDecodeError:
            try:
                with open(filepath, "r", encoding="latin-1") as f:
                    content = f.read()
                success, err = self.parse_string(content)
                if success:
                    self.filepath = filepath
                return success, err
            except Exception as e:
                return False, f"Encoding error: {str(e)}"
        except Exception as e:
            return False, str(e)

    def _rebuild_maps(self):
        """Rebuilds parent map and generates stable unique IDs for treeview linking."""
        self.parent_map.clear()
        self.element_id_map.clear()
        self.id_counter = 0

        if self.root is None:
            return

        def _traverse(element: ET.Element, parent: Optional[ET.Element]):
            self.id_counter += 1
            node_id = f"node_{self.id_counter}"
            self.element_id_map[node_id] = element
            self.parent_map[element] = parent
            for child in element:
                _traverse(child, element)

        _traverse(self.root, None)

    def get_element_by_id(self, node_id: str) -> Optional[ET.Element]:
        return self.element_id_map.get(node_id)

    def get_id_by_element(self, element: ET.Element) -> Optional[str]:
        for node_id, elem in self.element_id_map.items():
            if elem is element:
                return node_id
        return None

    def get_parent(self, element: ET.Element) -> Optional[ET.Element]:
        return self.parent_map.get(element)

    def get_xpath(self, element: ET.Element) -> str:
        """Computes a 1-based XPath expression for the given element."""
        if element is None or self.root is None:
            return ""
        if element is self.root:
            return f"/{self.root.tag}"

        path = []
        curr = element
        while curr is not None and curr is not self.root:
            parent = self.parent_map.get(curr)
            if parent is not None:
                # Count sibling position
                same_tag_siblings = [c for c in parent if c.tag == curr.tag]
                if len(same_tag_siblings) > 1:
                    idx = same_tag_siblings.index(curr) + 1
                    path.append(f"{curr.tag}[{idx}]")
                else:
                    path.append(curr.tag)
            else:
                path.append(curr.tag)
            curr = parent

        if self.root is not None:
            path.append(self.root.tag)
        return "/" + "/".join(reversed(path))

    def rename_element(self, element: ET.Element, new_tag: str) -> Tuple[bool, Optional[str]]:
        new_tag = new_tag.strip()
        if not new_tag:
            return False, "Tag name cannot be empty."
        if any(c in new_tag for c in " /<>\"'&: \t\r\n"):
            # basic XML tag name sanity check
            if not self._is_valid_tag(new_tag):
                return False, f"Invalid XML tag name '{new_tag}'"
        element.tag = new_tag
        return True, None

    def _is_valid_tag(self, tag: str) -> bool:
        try:
            ET.fromstring(f"<{tag}/>")
            return True
        except ET.ParseError:
            return False

    def set_text(self, element: ET.Element, text: str):
        element.text = text if text != "" else None

    def set_attribute(self, element: ET.Element, key: str, value: str) -> Tuple[bool, Optional[str]]:
        key = key.strip()
        if not key:
            return False, "Attribute name cannot be empty."
        try:
            # Validate attribute key
            ET.fromstring(f'<test {key}="val"/>')
        except ET.ParseError:
            return False, f"Invalid attribute name '{key}'"
        element.attrib[key] = value
        return True, None

    def remove_attribute(self, element: ET.Element, key: str):
        if key in element.attrib:
            del element.attrib[key]

    def add_child(self, parent: ET.Element, tag: str, text: str = "", attrib: Optional[Dict[str, str]] = None) -> Tuple[bool, Optional[ET.Element], Optional[str]]:
        tag = tag.strip()
        if not self._is_valid_tag(tag):
            return False, None, f"Invalid XML tag name '{tag}'"
        child = ET.SubElement(parent, tag, attrib=attrib or {})
        if text:
            child.text = text
        self._rebuild_maps()
        return True, child, None

    def insert_sibling(self, target: ET.Element, tag: str, text: str = "", attrib: Optional[Dict[str, str]] = None, after: bool = True) -> Tuple[bool, Optional[ET.Element], Optional[str]]:
        parent = self.parent_map.get(target)
        if parent is None:
            return False, None, "Cannot add sibling to root element."
        tag = tag.strip()
        if not self._is_valid_tag(tag):
            return False, None, f"Invalid XML tag name '{tag}'"

        new_elem = ET.Element(tag, attrib=attrib or {})
        if text:
            new_elem.text = text

        idx = list(parent).index(target)
        insert_idx = idx + 1 if after else idx
        parent.insert(insert_idx, new_elem)
        self._rebuild_maps()
        return True, new_elem, None

    def duplicate_element(self, element: ET.Element) -> Tuple[bool, Optional[ET.Element], Optional[str]]:
        parent = self.parent_map.get(element)
        if parent is None:
            return False, None, "Cannot duplicate the root element."

        cloned = copy.deepcopy(element)
        idx = list(parent).index(element)
        parent.insert(idx + 1, cloned)
        self._rebuild_maps()
        return True, cloned, None

    def delete_element(self, element: ET.Element) -> Tuple[bool, Optional[str]]:
        if element is self.root:
            return False, "Cannot delete root element. Create a new document or modify it."
        parent = self.parent_map.get(element)
        if parent is not None:
            parent.remove(element)
            self._rebuild_maps()
            return True, None
        return False, "Parent element not found."

    def move_element(self, element: ET.Element, direction: str) -> bool:
        """Moves an element up or down among its siblings. direction is 'up' or 'down'."""
        parent = self.parent_map.get(element)
        if parent is None:
            return False
        siblings = list(parent)
        idx = siblings.index(element)
        if direction == "up" and idx > 0:
            parent.remove(element)
            parent.insert(idx - 1, element)
            self._rebuild_maps()
            return True
        elif direction == "down" and idx < len(siblings) - 1:
            parent.remove(element)
            parent.insert(idx + 1, element)
            self._rebuild_maps()
            return True
        return False

    def to_string(self, pretty: bool = True, indent_str: str = "    ") -> str:
        """Serializes current tree into XML string."""
        if self.root is None:
            return ""

        raw_bytes = ET.tostring(self.root, encoding="utf-8")
        if not pretty:
            return raw_bytes.decode("utf-8")

        try:
            # Use minidom for clean formatting
            dom = minidom.parseString(raw_bytes)
            # Remove redundant empty lines from minidom pretty print
            pretty_xml = dom.toprettyxml(indent=indent_str, encoding="utf-8").decode("utf-8")
            # Clean up empty lines that minidom often injects
            lines = [line for line in pretty_xml.splitlines() if line.strip()]
            return "\n".join(lines)
        except Exception:
            # Fallback to ET indent if minidom fails
            clone = copy.deepcopy(self.root)
            ET.indent(clone, space=indent_str)
            return ET.tostring(clone, encoding="utf-8").decode("utf-8")

    def create_empty(self, root_tag: str = "root"):
        """Creates a brand new XML document."""
        self.root = ET.Element(root_tag)
        self.filepath = None
        self._rebuild_maps()

    @staticmethod
    def validate_string(xml_text: str) -> Tuple[bool, Optional[str], Optional[int], Optional[int]]:
        """Validates XML text, returns (is_valid, error_msg, line, col)."""
        clean_text = xml_text.strip()
        if not clean_text:
            return False, "XML is empty.", 1, 1
        try:
            ET.fromstring(clean_text)
            return True, None, None, None
        except ET.ParseError as e:
            return False, e.msg, e.position[0], e.position[1]
        except Exception as e:
            return False, str(e), None, None
