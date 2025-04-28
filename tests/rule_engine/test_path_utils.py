"""
Tests for the path utilities in the rule engine using pytest.
"""

import pytest
from rule_engine.utils.path_utils import PathUtils


def test_simplify_path():
    """Test the simplify_path method."""
    # Test with a full JSONPath
    assert PathUtils.simplify_path("$.devices[*].vendor") == "vendor"

    # Test with a nested path
    assert PathUtils.simplify_path("$.devices[*].config.version") == "config.version"

    # Test with a direct path (no entity)
    assert PathUtils.simplify_path("$.version") == "version"

    # Test with array index
    assert PathUtils.simplify_path("$.devices[0].vendor") == "vendor"

    # Test without $ prefix
    assert PathUtils.simplify_path("devices[*].vendor") == "vendor"

    # Test with just a property name
    assert PathUtils.simplify_path("vendor") == "vendor"


def test_get_value_from_path():
    """Test the get_value_from_path method."""
    # Simple entity with direct properties
    entity = {
        "id": "device-1",
        "vendor": "Cisco",
        "version": "17.3.6"
    }

    assert PathUtils.get_value_from_path(entity, "id") == "device-1"
    assert PathUtils.get_value_from_path(entity, "vendor") == "Cisco"
    assert PathUtils.get_value_from_path(entity, "version") == "17.3.6"
    assert PathUtils.get_value_from_path(entity, "nonexistent") is None

    # Entity with nested properties
    entity = {
        "id": "device-1",
        "vendor": "Cisco",
        "config": {
            "version": "17.3.6",
            "modules": ["routing", "firewall"]
        }
    }

    assert PathUtils.get_value_from_path(entity, "config.version") == "17.3.6"
    assert PathUtils.get_value_from_path(entity, "config.modules") == ["routing", "firewall"]
    assert PathUtils.get_value_from_path(entity, "config.nonexistent") is None

    # Entity with arrays
    entity = {
        "id": "device-1",
        "vendor": "Cisco",
        "interfaces": [
            {"name": "eth0", "ip": "192.168.1.1"},
            {"name": "eth1", "ip": "192.168.2.1"}
        ]
    }

    assert PathUtils.get_value_from_path(entity, "interfaces[0].name") == "eth0"
    assert PathUtils.get_value_from_path(entity, "interfaces[1].ip") == "192.168.2.1"
    assert PathUtils.get_value_from_path(entity, "interfaces[2].name") is None  # Out of range
    assert PathUtils.get_value_from_path(entity, "interfaces[0].nonexistent") is None


def test_extract_entity_list():
    """Test the extract_entity_list method."""
    # Test with plural key
    data = {
        "devices": [
            {"id": "device-1"},
            {"id": "device-2"}
        ]
    }

    assert len(PathUtils.extract_entity_list(data, "device")) == 2

    # Test with singular key
    data = {
        "device": [
            {"id": "device-1"},
            {"id": "device-2"}
        ]
    }

    assert len(PathUtils.extract_entity_list(data, "device")) == 2

    # Test with non-existent key
    data = {
        "configs": [
            {"id": "config-1"},
            {"id": "config-2"}
        ]
    }

    assert len(PathUtils.extract_entity_list(data, "device")) == 0

    # Test with empty array
    data = {
        "devices": []
    }

    assert len(PathUtils.extract_entity_list(data, "device")) == 0