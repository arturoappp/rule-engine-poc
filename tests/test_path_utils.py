"""
Tests for the path utilities in the rule engine.
"""

import unittest

from utils.path_utils import PathUtils


class PathUtilsTest(unittest.TestCase):
    """Test case for the path utilities in the rule engine."""

    def test_simplify_path(self):
        """Test the simplify_path method."""
        # Test with a full JSONPath
        self.assertEqual(PathUtils.simplify_path("$.devices[*].vendor"), "vendor")

        # Test with a nested path
        self.assertEqual(PathUtils.simplify_path("$.devices[*].config.version"), "config.version")

        # Test with a direct path (no entity)
        self.assertEqual(PathUtils.simplify_path("$.version"), "version")

        # Test with array index
        self.assertEqual(PathUtils.simplify_path("$.devices[0].vendor"), "vendor")

        # Test without $ prefix
        self.assertEqual(PathUtils.simplify_path("devices[*].vendor"), "vendor")

        # Test with just a property name
        self.assertEqual(PathUtils.simplify_path("vendor"), "vendor")

    def test_get_value_from_path(self):
        """Test the get_value_from_path method."""
        # Simple entity with direct properties
        entity = {
            "id": "device-1",
            "vendor": "Cisco",
            "version": "17.3.6"
        }

        self.assertEqual(PathUtils.get_value_from_path(entity, "id"), "device-1")
        self.assertEqual(PathUtils.get_value_from_path(entity, "vendor"), "Cisco")
        self.assertEqual(PathUtils.get_value_from_path(entity, "version"), "17.3.6")
        self.assertIsNone(PathUtils.get_value_from_path(entity, "nonexistent"))

        # Entity with nested properties
        entity = {
            "id": "device-1",
            "vendor": "Cisco",
            "config": {
                "version": "17.3.6",
                "modules": ["routing", "firewall"]
            }
        }

        self.assertEqual(PathUtils.get_value_from_path(entity, "config.version"), "17.3.6")
        self.assertEqual(PathUtils.get_value_from_path(entity, "config.modules"), ["routing", "firewall"])
        self.assertIsNone(PathUtils.get_value_from_path(entity, "config.nonexistent"))

        # Entity with arrays
        entity = {
            "id": "device-1",
            "vendor": "Cisco",
            "interfaces": [
                {"name": "eth0", "ip": "192.168.1.1"},
                {"name": "eth1", "ip": "192.168.2.1"}
            ]
        }

        self.assertEqual(PathUtils.get_value_from_path(entity, "interfaces[0].name"), "eth0")
        self.assertEqual(PathUtils.get_value_from_path(entity, "interfaces[1].ip"), "192.168.2.1")
        self.assertIsNone(PathUtils.get_value_from_path(entity, "interfaces[2].name"))  # Out of range
        self.assertIsNone(PathUtils.get_value_from_path(entity, "interfaces[0].nonexistent"))

    def test_extract_entity_list(self):
        """Test the extract_entity_list method."""
        # Test with plural key
        data = {
            "devices": [
                {"id": "device-1"},
                {"id": "device-2"}
            ]
        }

        self.assertEqual(len(PathUtils.extract_entity_list(data, "device")), 2)

        # Test with singular key
        data = {
            "device": [
                {"id": "device-1"},
                {"id": "device-2"}
            ]
        }

        self.assertEqual(len(PathUtils.extract_entity_list(data, "device")), 2)

        # Test with non-existent key
        data = {
            "configs": [
                {"id": "config-1"},
                {"id": "config-2"}
            ]
        }

        self.assertEqual(len(PathUtils.extract_entity_list(data, "device")), 0)

        # Test with empty array
        data = {
            "devices": []
        }

        self.assertEqual(len(PathUtils.extract_entity_list(data, "device")), 0)


if __name__ == '__main__':
    unittest.main()