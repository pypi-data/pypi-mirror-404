"""
Container Builder for Discord Components V2
"""

from typing import Any, Dict, List, Union


class ContainerBuilder:
    """Builder for Discord Container components (requires IS_COMPONENTS_V2 flag)"""

    def __init__(self):
        self._components: List[Dict[str, Any]] = []
        self._accent_color: int | None = None
        self._spoiler: bool = False

    def add_component(self, component: Union[Dict[str, Any], Any]) -> "ContainerBuilder":
        """Add a child component"""
        if hasattr(component, "to_dict"):
            self._components.append(component.to_dict())
        else:
            self._components.append(component)
        return self

    def add_text(self, content: str) -> "ContainerBuilder":
        """Add a text display component"""
        self._components.append({
            "type": 10,
            "content": content,
        })
        return self

    def add_separator(self, divider: bool = True, spacing: int = 1) -> "ContainerBuilder":
        """Add a separator component"""
        self._components.append({
            "type": 14,
            "divider": divider,
            "spacing": spacing,
        })
        return self

    def set_accent_color(self, color: int) -> "ContainerBuilder":
        """Set the accent color (RGB value)"""
        self._accent_color = color
        return self

    def set_spoiler(self, spoiler: bool = True) -> "ContainerBuilder":
        """Set whether container is a spoiler"""
        self._spoiler = spoiler
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Discord API format"""
        result: Dict[str, Any] = {
            "type": 17,
            "components": self._components,
        }
        if self._accent_color is not None:
            result["accent_color"] = self._accent_color
        if self._spoiler:
            result["spoiler"] = self._spoiler
        return result
