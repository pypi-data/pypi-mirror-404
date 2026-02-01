"""
Select Context for select menu interactions
"""

from typing import Any, Dict, List, Optional

from .base import BaseContext


class SelectContext(BaseContext):
    """Context for handling select menu interactions"""

    @property
    def custom_id(self) -> str:
        """Get the select menu custom ID"""
        data = self._interaction.get("data", {})
        return data.get("custom_id", "")

    @property
    def values(self) -> List[str]:
        """Get selected values"""
        data = self._interaction.get("data", {})
        return data.get("values", [])

    @property
    def message(self) -> Optional[Dict[str, Any]]:
        """Get the message the select was attached to"""
        return self._interaction.get("message")

    @property
    def message_id(self) -> Optional[str]:
        """Get the message ID"""
        message = self.message
        return message.get("id") if message else None
