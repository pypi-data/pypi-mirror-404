"""
Separator Builder for Discord Components V2
"""

from typing import Any, Dict, Literal


class SeparatorBuilder:
    """Builder for Discord Separator components (requires IS_COMPONENTS_V2 flag)"""

    def __init__(self):
        self._divider: bool = True
        self._spacing: int = 1

    def set_divider(self, divider: bool) -> "SeparatorBuilder":
        """Set whether to show visual divider"""
        self._divider = divider
        return self

    def set_spacing(self, spacing: Literal[1, 2]) -> "SeparatorBuilder":
        """Set spacing size (1 = small, 2 = large)"""
        self._spacing = spacing
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Discord API format"""
        return {
            "type": 14,
            "divider": self._divider,
            "spacing": self._spacing,
        }
