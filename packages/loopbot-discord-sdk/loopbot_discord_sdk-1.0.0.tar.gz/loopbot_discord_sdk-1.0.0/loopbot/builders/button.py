"""
Button Builder for Discord buttons
"""

from enum import IntEnum
from typing import Any, Dict, Optional


class ButtonStyle(IntEnum):
    PRIMARY = 1
    SECONDARY = 2
    SUCCESS = 3
    DANGER = 4
    LINK = 5


class ButtonBuilder:
    """Builder for Discord buttons"""

    def __init__(self):
        self._button: Dict[str, Any] = {"type": 2}

    def set_custom_id(self, custom_id: str) -> "ButtonBuilder":
        """Set the button custom ID"""
        self._button["custom_id"] = custom_id
        return self

    def set_label(self, label: str) -> "ButtonBuilder":
        """Set the button label"""
        self._button["label"] = label
        return self

    def set_style(self, style: ButtonStyle) -> "ButtonBuilder":
        """Set the button style"""
        self._button["style"] = int(style)
        return self

    def set_emoji(self, name: str, id: Optional[str] = None) -> "ButtonBuilder":
        """Set the button emoji"""
        self._button["emoji"] = {"name": name}
        if id:
            self._button["emoji"]["id"] = id
        return self

    def set_url(self, url: str) -> "ButtonBuilder":
        """Set the button URL (for link buttons)"""
        self._button["url"] = url
        self._button["style"] = int(ButtonStyle.LINK)
        return self

    def set_disabled(self, disabled: bool = True) -> "ButtonBuilder":
        """Set whether the button is disabled"""
        self._button["disabled"] = disabled
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Discord API format"""
        return self._button
