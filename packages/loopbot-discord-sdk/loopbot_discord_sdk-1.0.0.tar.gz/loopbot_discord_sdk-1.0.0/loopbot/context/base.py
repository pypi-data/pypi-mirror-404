"""
Base Context for all interaction types
"""

from typing import Any, Dict, List, Optional, Union

from ..types import Interaction, InteractionResponseType, DiscordUser, DiscordMember
from ..builders.embed import EmbedBuilder
from ..builders.action_row import ActionRowBuilder
from ..builders.modal import ModalBuilder


class BaseContext:
    """Base context for handling Discord interactions"""

    def __init__(
        self,
        interaction: Dict[str, Any],
        client: Any,
        application_id: str,
    ):
        self._interaction = interaction
        self._client = client
        self._application_id = application_id
        self._response: Optional[Dict[str, Any]] = None
        self._deferred = False

    @property
    def interaction_id(self) -> str:
        return self._interaction.get("id", "")

    @property
    def token(self) -> str:
        return self._interaction.get("token", "")

    @property
    def guild_id(self) -> Optional[str]:
        return self._interaction.get("guild_id")

    @property
    def channel_id(self) -> Optional[str]:
        return self._interaction.get("channel_id")

    @property
    def user(self) -> Optional[Dict[str, Any]]:
        """Get the user who triggered the interaction"""
        member = self._interaction.get("member")
        if member:
            return member.get("user")
        return self._interaction.get("user")

    @property
    def user_id(self) -> Optional[str]:
        user = self.user
        return user.get("id") if user else None

    @property
    def username(self) -> Optional[str]:
        user = self.user
        return user.get("username") if user else None

    @property
    def member(self) -> Optional[Dict[str, Any]]:
        return self._interaction.get("member")

    @property
    def locale(self) -> Optional[str]:
        return self._interaction.get("locale")

    @property
    def response(self) -> Optional[Dict[str, Any]]:
        return self._response

    @property
    def is_deferred(self) -> bool:
        return self._deferred

    def reply(
        self,
        content: Optional[str] = None,
        embeds: Optional[List[Union[Dict[str, Any], EmbedBuilder]]] = None,
        components: Optional[List[Union[Dict[str, Any], ActionRowBuilder]]] = None,
        ephemeral: bool = False,
    ) -> None:
        """Reply to the interaction"""
        data: Dict[str, Any] = {}
        
        if content:
            data["content"] = content
        
        if embeds:
            data["embeds"] = [
                e.to_dict() if isinstance(e, EmbedBuilder) else e
                for e in embeds
            ]
        
        if components:
            data["components"] = [
                c.to_dict() if isinstance(c, ActionRowBuilder) else c
                for c in components
            ]
        
        if ephemeral:
            data["flags"] = 64

        self._response = {
            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": data,
        }

    def reply_text(self, content: str, ephemeral: bool = False) -> None:
        """Reply with simple text"""
        self.reply(content=content, ephemeral=ephemeral)

    def reply_with_components(
        self,
        components: List[Any],
        ephemeral: bool = False,
    ) -> None:
        """Reply with Components V2 (Container, MediaGallery, etc.)"""
        data: Dict[str, Any] = {
            "components": [
                c.to_dict() if hasattr(c, "to_dict") else c
                for c in components
            ],
            "flags": 32768,  # IS_COMPONENTS_V2
        }
        
        if ephemeral:
            data["flags"] |= 64

        self._response = {
            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": data,
        }

    def update(
        self,
        content: Optional[str] = None,
        embeds: Optional[List[Union[Dict[str, Any], EmbedBuilder]]] = None,
        components: Optional[List[Union[Dict[str, Any], ActionRowBuilder]]] = None,
    ) -> None:
        """Update the original message"""
        data: Dict[str, Any] = {}
        
        if content is not None:
            data["content"] = content
        
        if embeds:
            data["embeds"] = [
                e.to_dict() if isinstance(e, EmbedBuilder) else e
                for e in embeds
            ]
        
        if components:
            data["components"] = [
                c.to_dict() if isinstance(c, ActionRowBuilder) else c
                for c in components
            ]

        self._response = {
            "type": InteractionResponseType.UPDATE_MESSAGE,
            "data": data,
        }

    def update_with_components(self, components: List[Any]) -> None:
        """Update the original message with Components V2"""
        self._response = {
            "type": InteractionResponseType.UPDATE_MESSAGE,
            "data": {
                "components": [
                    c.to_dict() if hasattr(c, "to_dict") else c
                    for c in components
                ],
                "flags": 32768,  # IS_COMPONENTS_V2
            },
        }

    def defer(self, ephemeral: bool = False) -> None:
        """Defer the response (show 'thinking...')"""
        self._deferred = True
        self._response = {
            "type": InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {"flags": 64 if ephemeral else 0},
        }

    def defer_update(self) -> None:
        """Defer the update (acknowledge without visible loading)"""
        self._deferred = True
        self._response = {
            "type": InteractionResponseType.DEFERRED_UPDATE_MESSAGE,
        }

    def show_modal(self, modal: ModalBuilder) -> None:
        """Show a modal to the user"""
        self._response = {
            "type": InteractionResponseType.MODAL,
            "data": modal.to_dict(),
        }

    async def follow_up(
        self,
        content: Optional[str] = None,
        embeds: Optional[List[Union[Dict[str, Any], EmbedBuilder]]] = None,
        components: Optional[List[Union[Dict[str, Any], ActionRowBuilder]]] = None,
        ephemeral: bool = False,
    ) -> Dict[str, Any]:
        """Send a follow-up message"""
        data: Dict[str, Any] = {}
        
        if content:
            data["content"] = content
        
        if embeds:
            data["embeds"] = [
                e.to_dict() if isinstance(e, EmbedBuilder) else e
                for e in embeds
            ]
        
        if components:
            data["components"] = [
                c.to_dict() if isinstance(c, ActionRowBuilder) else c
                for c in components
            ]
        
        if ephemeral:
            data["flags"] = 64

        return await self._client.follow_up(
            self._application_id,
            self.token,
            data,
        )

    async def edit_reply(
        self,
        content: Optional[str] = None,
        embeds: Optional[List[Union[Dict[str, Any], EmbedBuilder]]] = None,
        components: Optional[List[Union[Dict[str, Any], ActionRowBuilder]]] = None,
    ) -> None:
        """Edit the original response"""
        data: Dict[str, Any] = {}
        
        if content is not None:
            data["content"] = content
        
        if embeds:
            data["embeds"] = [
                e.to_dict() if isinstance(e, EmbedBuilder) else e
                for e in embeds
            ]
        
        if components:
            data["components"] = [
                c.to_dict() if isinstance(c, ActionRowBuilder) else c
                for c in components
            ]

        await self._client.edit_original(
            self._application_id,
            self.token,
            data,
        )
