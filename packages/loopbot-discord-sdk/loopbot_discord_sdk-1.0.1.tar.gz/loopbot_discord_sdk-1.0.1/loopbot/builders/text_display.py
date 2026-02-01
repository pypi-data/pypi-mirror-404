"""
Text Display Builder for Discord Components V2
"""

from typing import Any, Dict


class TextDisplayBuilder:
    """Builder for Discord Text Display components (requires IS_COMPONENTS_V2 flag)"""

    def __init__(self, content: str = ""):
        self._content: str = content

    def set_content(self, content: str) -> "TextDisplayBuilder":
        """Set the text content (supports markdown)"""
        self._content = content
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Discord API format"""
        return {
            "type": 10,
            "content": self._content,
        }
