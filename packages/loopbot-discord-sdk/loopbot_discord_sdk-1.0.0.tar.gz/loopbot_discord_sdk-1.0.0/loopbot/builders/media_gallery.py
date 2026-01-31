"""
Media Gallery Builder for Discord Components V2
"""

from typing import Any, Dict, List, Optional


class MediaGalleryBuilder:
    """Builder for Discord Media Gallery components (requires IS_COMPONENTS_V2 flag)"""

    def __init__(self):
        self._items: List[Dict[str, Any]] = []

    def add_item(
        self,
        url: str,
        description: Optional[str] = None,
        spoiler: bool = False,
    ) -> "MediaGalleryBuilder":
        """Add a media item to the gallery"""
        item: Dict[str, Any] = {
            "media": {"url": url},
        }
        if description:
            item["description"] = description
        if spoiler:
            item["spoiler"] = spoiler
        self._items.append(item)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Discord API format"""
        return {
            "type": 12,
            "items": self._items,
        }
