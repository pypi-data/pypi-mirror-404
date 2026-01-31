"""
Action Row Builder for grouping components
"""

from typing import Any, Dict, List, Union

from .button import ButtonBuilder
from .select_menu import SelectMenuBuilder


class ActionRowBuilder:
    """Builder for Discord action rows"""

    def __init__(self):
        self._components: List[Dict[str, Any]] = []

    def add_button(self, button: ButtonBuilder) -> "ActionRowBuilder":
        """Add a button to the row"""
        self._components.append(button.to_dict())
        return self

    def add_select_menu(self, select: "SelectMenuBuilder") -> "ActionRowBuilder":
        """Add a select menu to the row"""
        self._components.append(select.to_dict())
        return self

    def add_component(self, component: Union[Dict[str, Any], Any]) -> "ActionRowBuilder":
        """Add a component to the row"""
        if hasattr(component, "to_dict"):
            self._components.append(component.to_dict())
        else:
            self._components.append(component)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Discord API format"""
        return {
            "type": 1,
            "components": self._components,
        }
