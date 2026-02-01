"""
Embed Builder for Discord rich embeds
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class EmbedBuilder:
    """Builder for Discord embeds"""

    def __init__(self):
        self._embed: Dict[str, Any] = {}

    def set_title(self, title: str) -> "EmbedBuilder":
        """Set the embed title"""
        self._embed["title"] = title
        return self

    def set_description(self, description: str) -> "EmbedBuilder":
        """Set the embed description"""
        self._embed["description"] = description
        return self

    def set_url(self, url: str) -> "EmbedBuilder":
        """Set the embed URL"""
        self._embed["url"] = url
        return self

    def set_color(self, color: int) -> "EmbedBuilder":
        """Set the embed color (RGB integer)"""
        self._embed["color"] = color
        return self

    def set_timestamp(self, timestamp: Optional[datetime] = None) -> "EmbedBuilder":
        """Set the embed timestamp"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        self._embed["timestamp"] = timestamp.isoformat()
        return self

    def set_footer(
        self,
        text: str,
        icon_url: Optional[str] = None,
    ) -> "EmbedBuilder":
        """Set the embed footer"""
        self._embed["footer"] = {"text": text}
        if icon_url:
            self._embed["footer"]["icon_url"] = icon_url
        return self

    def set_image(self, url: str) -> "EmbedBuilder":
        """Set the embed image"""
        self._embed["image"] = {"url": url}
        return self

    def set_thumbnail(self, url: str) -> "EmbedBuilder":
        """Set the embed thumbnail"""
        self._embed["thumbnail"] = {"url": url}
        return self

    def set_author(
        self,
        name: str,
        url: Optional[str] = None,
        icon_url: Optional[str] = None,
    ) -> "EmbedBuilder":
        """Set the embed author"""
        self._embed["author"] = {"name": name}
        if url:
            self._embed["author"]["url"] = url
        if icon_url:
            self._embed["author"]["icon_url"] = icon_url
        return self

    def add_field(
        self,
        name: str,
        value: str,
        inline: bool = False,
    ) -> "EmbedBuilder":
        """Add a field to the embed"""
        if "fields" not in self._embed:
            self._embed["fields"] = []
        self._embed["fields"].append({
            "name": name,
            "value": value,
            "inline": inline,
        })
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Discord API format"""
        return self._embed
