"""
Select Menu Builder for Discord dropdowns
"""

from typing import Any, Dict, List, Optional


class SelectMenuBuilder:
    """Builder for Discord select menus"""

    def __init__(self):
        self._select: Dict[str, Any] = {"type": 3, "options": []}

    def set_custom_id(self, custom_id: str) -> "SelectMenuBuilder":
        """Set the select menu custom ID"""
        self._select["custom_id"] = custom_id
        return self

    def set_placeholder(self, placeholder: str) -> "SelectMenuBuilder":
        """Set the placeholder text"""
        self._select["placeholder"] = placeholder
        return self

    def set_min_values(self, min_values: int) -> "SelectMenuBuilder":
        """Set minimum values to select"""
        self._select["min_values"] = min_values
        return self

    def set_max_values(self, max_values: int) -> "SelectMenuBuilder":
        """Set maximum values to select"""
        self._select["max_values"] = max_values
        return self

    def set_disabled(self, disabled: bool = True) -> "SelectMenuBuilder":
        """Set whether the select is disabled"""
        self._select["disabled"] = disabled
        return self

    def add_option(
        self,
        label: str,
        value: str,
        description: Optional[str] = None,
        emoji: Optional[Dict[str, str]] = None,
        default: bool = False,
    ) -> "SelectMenuBuilder":
        """Add an option to the select menu"""
        option: Dict[str, Any] = {
            "label": label,
            "value": value,
        }
        if description:
            option["description"] = description
        if emoji:
            option["emoji"] = emoji
        if default:
            option["default"] = default
        self._select["options"].append(option)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Discord API format"""
        return self._select
