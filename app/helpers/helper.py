from typing import Dict, List, Any


def _get_entity_key(entity_type: str) -> str:
    return f"{entity_type}s" if not entity_type.endswith('s') else entity_type


def _extract_entities(data: Dict[str, Any], entity_type: str) -> List[Dict[str, Any]]:
    entity_key = _get_entity_key(entity_type)

    if entity_key in data and isinstance(data[entity_key], list):
        return data[entity_key]
    elif entity_type in data and isinstance(data[entity_type], list):
        return data[entity_type]

    return []
