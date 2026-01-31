"""
File Builder for Discord Components V2
"""

from typing import Any, Dict


class FileBuilder:
    """Builder for Discord File components (requires IS_COMPONENTS_V2 flag)"""

    def __init__(self, url: str):
        self._url: str = url
        self._spoiler: bool = False

    def set_url(self, url: str) -> "FileBuilder":
        """Set the file URL"""
        self._url = url
        return self

    def set_spoiler(self, spoiler: bool = True) -> "FileBuilder":
        """Set whether file is a spoiler"""
        self._spoiler = spoiler
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Discord API format"""
        result: Dict[str, Any] = {
            "type": 13,
            "file": {"url": self._url},
        }
        if self._spoiler:
            result["spoiler"] = self._spoiler
        return result
