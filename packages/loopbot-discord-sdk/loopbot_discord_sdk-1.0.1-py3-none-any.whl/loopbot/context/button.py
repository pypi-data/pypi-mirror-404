"""
Button Context for button interactions
"""

from typing import Any, Dict, Optional

from .base import BaseContext


class ButtonContext(BaseContext):
    """Context for handling button interactions"""

    @property
    def custom_id(self) -> str:
        """Get the button custom ID"""
        data = self._interaction.get("data", {})
        return data.get("custom_id", "")

    @property
    def message(self) -> Optional[Dict[str, Any]]:
        """Get the message the button was attached to"""
        return self._interaction.get("message")

    @property
    def message_id(self) -> Optional[str]:
        """Get the message ID"""
        message = self.message
        return message.get("id") if message else None
