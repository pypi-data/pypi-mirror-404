"""
Section Builder for Discord Components V2
"""

from typing import Any, Dict, List, Optional, Union

from .button import ButtonBuilder


class SectionBuilder:
    """Builder for Discord Section components (requires IS_COMPONENTS_V2 flag)"""

    def __init__(self):
        self._components: List[Dict[str, Any]] = []
        self._accessory: Dict[str, Any] | None = None

    def add_text(self, content: str) -> "SectionBuilder":
        """Add a text display component"""
        self._components.append({
            "type": 10,
            "content": content,
        })
        return self

    def set_button_accessory(self, button: ButtonBuilder) -> "SectionBuilder":
        """Set a button as the accessory"""
        self._accessory = button.to_dict()
        return self

    def set_thumbnail_accessory(
        self,
        url: str,
        description: Optional[str] = None,
    ) -> "SectionBuilder":
        """Set a thumbnail as the accessory"""
        self._accessory = {
            "type": 11,
            "media": {"url": url},
        }
        if description:
            self._accessory["description"] = description
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Discord API format"""
        result: Dict[str, Any] = {
            "type": 9,
            "components": self._components,
        }
        if self._accessory:
            result["accessory"] = self._accessory
        return result
