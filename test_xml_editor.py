"""
Unit tests for XML Viewer & WYSIWYG Editor model and operations.
"""

import unittest
from xml_model import XMLModel


class TestXMLModel(unittest.TestCase):
    def setUp(self):
        self.model = XMLModel()
        xml_sample = """<?xml version="1.0" encoding="UTF-8"?>
<root title="Test Suite">
    <item id="1">First</item>
    <item id="2">Second</item>
</root>"""
        ok, err = self.model.parse_string(xml_sample)
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_root_and_traversal(self):
        self.assertEqual(self.model.root.tag, "root")
        self.assertEqual(len(list(self.model.root)), 2)
        item1 = self.model.root[0]
        self.assertEqual(self.model.get_xpath(item1), "/root/item[1]")

    def test_rename_element(self):
        item1 = self.model.root[0]
        ok, err = self.model.rename_element(item1, "entry")
        self.assertTrue(ok)
        self.assertEqual(item1.tag, "entry")

        # Invalid tag
        ok, err = self.model.rename_element(item1, "invalid tag with spaces")
        self.assertFalse(ok)

    def test_set_text_and_attributes(self):
        item1 = self.model.root[0]
        self.model.set_text(item1, "Updated Content")
        self.assertEqual(item1.text, "Updated Content")

        ok, err = self.model.set_attribute(item1, "status", "active")
        self.assertTrue(ok)
        self.assertEqual(item1.attrib.get("status"), "active")

        self.model.remove_attribute(item1, "status")
        self.assertNotIn("status", item1.attrib)

    def test_add_child_and_sibling(self):
        item1 = self.model.root[0]
        ok, child, err = self.model.add_child(item1, "subitem", text="Sub", attrib={"key": "val"})
        self.assertTrue(ok)
        self.assertEqual(child.tag, "subitem")
        self.assertEqual(child.text, "Sub")
        self.assertEqual(child.attrib["key"], "val")
        self.assertIn(child, list(item1))

        ok, sib, err = self.model.insert_sibling(item1, "newitem", after=True)
        self.assertTrue(ok)
        self.assertEqual(self.model.root[1], sib)

    def test_duplicate_and_move(self):
        item1 = self.model.root[0]
        ok, cloned, err = self.model.duplicate_element(item1)
        self.assertTrue(ok)
        self.assertEqual(cloned.tag, item1.tag)
        self.assertEqual(cloned.attrib, item1.attrib)

        # Move item down
        ok = self.model.move_element(item1, "down")
        self.assertTrue(ok)
        self.assertEqual(self.model.root[1], item1)

    def test_delete_element(self):
        item2 = self.model.root[1]
        ok, err = self.model.delete_element(item2)
        self.assertTrue(ok)
        self.assertEqual(len(list(self.model.root)), 1)

    def test_validation(self):
        valid_xml = "<root><child>Valid</child></root>"
        is_val, err, line, col = XMLModel.validate_string(valid_xml)
        self.assertTrue(is_val)

        invalid_xml = "<root><unclosed></root>"
        is_val, err, line, col = XMLModel.validate_string(invalid_xml)
        self.assertFalse(is_val)
        self.assertIsNotNone(err)


if __name__ == "__main__":
    unittest.main()
