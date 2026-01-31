"""
Modal Context for modal submit interactions
"""

from typing import Any, Dict, List, Optional

from .base import BaseContext


class ModalContext(BaseContext):
    """Context for handling modal submit interactions"""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._fields: Dict[str, str] = self._parse_fields()

    def _parse_fields(self) -> Dict[str, str]:
        """Parse modal fields from interaction data"""
        fields: Dict[str, str] = {}
        data = self._interaction.get("data", {})
        components = data.get("components", [])
        
        for row in components:
            row_components = row.get("components", [])
            for component in row_components:
                custom_id = component.get("custom_id", "")
                value = component.get("value", "")
                if custom_id:
                    fields[custom_id] = value
        
        return fields

    @property
    def custom_id(self) -> str:
        """Get the modal custom ID"""
        data = self._interaction.get("data", {})
        return data.get("custom_id", "")

    @property
    def fields(self) -> Dict[str, str]:
        """Get all modal fields as dict"""
        return self._fields

    def get_field(self, custom_id: str, default: str = "") -> str:
        """Get a specific field value"""
        return self._fields.get(custom_id, default)
