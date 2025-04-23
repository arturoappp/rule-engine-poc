"""
Utilities for handling JSONPath-like paths in the rule engine.
"""

from typing import Any, Dict


class PathUtils:
    """Utility class for handling access paths in rules."""

    @staticmethod
    def simplify_path(path: str) -> str:
        """
        Simplify a JSONPath for use with individual entities.

        Args:
            path: JSONPath (e.g. "$.devices[*].vendor")

        Returns:
            Simplified path (e.g. "vendor")
        """
        # Remove the "$." prefix
        if path.startswith('$.'):
            path = path[2:]

        # Remove the entity part and the index
        # For example, "devices[*].vendor" -> "vendor"
        parts = path.split('.')
        if len(parts) > 1 and '[' in parts[0]:
            path = '.'.join(parts[1:])

        return path

    @staticmethod
    def get_value_from_path(entity: Dict, path: str) -> Any:
        """
        Get a value from an entity using an access path.

        Args:
            entity: Entity dictionary
            path: Access path (e.g. "vendor" or "nested.property")

        Returns:
            Value at the specified path
        """
        if not path:
            return None

        parts = path.split('.')
        current = entity

        for part in parts:
            # Handle arrays with indices
            if '[' in part and ']' in part:
                array_name = part.split('[')[0]
                index_part = part.split('[')[1].split(']')[0]

                if array_name not in current:
                    return None

                try:
                    index = int(index_part)
                    if isinstance(current[array_name], list) and 0 <= index < len(current[array_name]):
                        current = current[array_name][index]
                    else:
                        return None
                except (ValueError, IndexError):
                    return None
            else:
                # Normal object navigation
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None

        return current

    @staticmethod
    def extract_entity_list(data: Dict, entity_type: str) -> list:
        """
        Extract the list of entities from the data.

        Args:
            data: Data dictionary
            entity_type: Entity type to extract (without 's' at the end)

        Returns:
            List of entities
        """
        # Try different common formats (plural, singular)
        plural_key = f"{entity_type}s"
        singular_key = entity_type

        if plural_key in data and isinstance(data[plural_key], list):
            return data[plural_key]
        elif singular_key in data and isinstance(data[singular_key], list):
            return data[singular_key]
        elif entity_type in data and isinstance(data[entity_type], list):
            return data[entity_type]

        # If there is no entity list, return an empty list
        return []
