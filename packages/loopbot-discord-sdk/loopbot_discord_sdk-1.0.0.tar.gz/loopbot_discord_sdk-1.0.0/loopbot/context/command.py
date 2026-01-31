"""
Command Context for slash commands
"""

from typing import Any, Dict, List, Optional

from .base import BaseContext


class CommandContext(BaseContext):
    """Context for handling slash command interactions"""

    @property
    def command_name(self) -> str:
        """Get the command name"""
        data = self._interaction.get("data", {})
        return data.get("name", "")

    @property
    def options(self) -> Dict[str, Any]:
        """Get command options as a dict"""
        data = self._interaction.get("data", {})
        options = data.get("options", [])
        return self._parse_options(options)

    def _parse_options(self, options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse options list into dict"""
        result: Dict[str, Any] = {}
        for opt in options:
            name = opt.get("name", "")
            value = opt.get("value")
            
            # Handle subcommands/groups
            if opt.get("options"):
                result[name] = self._parse_options(opt["options"])
            else:
                result[name] = value
        
        return result

    def get_option(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """Get a specific option value"""
        return self.options.get(name, default)

    def get_string(self, name: str, default: str = "") -> str:
        """Get a string option"""
        return str(self.get_option(name, default))

    def get_int(self, name: str, default: int = 0) -> int:
        """Get an integer option"""
        value = self.get_option(name, default)
        return int(value) if value is not None else default

    def get_bool(self, name: str, default: bool = False) -> bool:
        """Get a boolean option"""
        return bool(self.get_option(name, default))

    def get_user(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a user option from resolved data"""
        user_id = self.get_option(name)
        if not user_id:
            return None
        
        data = self._interaction.get("data", {})
        resolved = data.get("resolved", {})
        users = resolved.get("users", {})
        return users.get(user_id)

    def get_channel(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a channel option from resolved data"""
        channel_id = self.get_option(name)
        if not channel_id:
            return None
        
        data = self._interaction.get("data", {})
        resolved = data.get("resolved", {})
        channels = resolved.get("channels", {})
        return channels.get(channel_id)

    def get_role(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a role option from resolved data"""
        role_id = self.get_option(name)
        if not role_id:
            return None
        
        data = self._interaction.get("data", {})
        resolved = data.get("resolved", {})
        roles = resolved.get("roles", {})
        return roles.get(role_id)
