from typing import Dict


def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """Merge two dictionaries deeply."""
    result = dict1.copy()
    for key, value in dict2.items():
        if isinstance(value, dict) and key in result:
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result