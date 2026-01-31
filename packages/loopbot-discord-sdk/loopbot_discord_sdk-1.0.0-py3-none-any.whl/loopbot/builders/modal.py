"""
Modal Builder for Discord modals
"""

from typing import Any, Dict, List, Literal, Optional


class ModalBuilder:
    """Builder for Discord modals"""

    def __init__(self):
        self._custom_id: str = ""
        self._title: str = ""
        self._components: List[Dict[str, Any]] = []

    def set_custom_id(self, custom_id: str) -> "ModalBuilder":
        """Set the modal custom ID"""
        self._custom_id = custom_id
        return self

    def set_title(self, title: str) -> "ModalBuilder":
        """Set the modal title"""
        self._title = title
        return self

    def add_text_input(
        self,
        custom_id: str,
        label: str,
        style: Literal["short", "paragraph"] = "short",
        required: bool = True,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        placeholder: Optional[str] = None,
        value: Optional[str] = None,
    ) -> "ModalBuilder":
        """Add a text input to the modal"""
        input_data: Dict[str, Any] = {
            "type": 4,
            "custom_id": custom_id,
            "style": 1 if style == "short" else 2,
            "label": label,
            "required": required,
        }
        if min_length is not None:
            input_data["min_length"] = min_length
        if max_length is not None:
            input_data["max_length"] = max_length
        if placeholder:
            input_data["placeholder"] = placeholder
        if value:
            input_data["value"] = value

        # Wrap in action row
        self._components.append({
            "type": 1,
            "components": [input_data],
        })
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Discord API format"""
        return {
            "title": self._title,
            "custom_id": self._custom_id,
            "components": self._components,
        }
